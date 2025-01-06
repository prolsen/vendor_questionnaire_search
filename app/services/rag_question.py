# app/services/rag_question.py
import logging
from typing import List

from llama_index.core import (
    VectorStoreIndex,
    QueryBundle,
    PromptTemplate,
    get_response_synthesizer,
)
from llama_index.core.base.response.schema import RESPONSE_TYPE
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers.type import ResponseMode
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.storage.storage_context import StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.postprocessor.cohere_rerank import CohereRerank
from pydantic import BaseModel
import qdrant_client
from prompt import general_qa_prompt_tmpl_str
from config import settings

class SourceNode(BaseModel):
    """
    Represents a source node containing metadata about a retrieved document.

    Attributes:
        node_id (str): Unique identifier for the node.
        document_name (str): Name of the source document.
        question (str): Content of the node (typically a question).
        answer (str): Answer associated with the node.
        product (str): Product related to the node.
        score (float): Similarity or relevance score of the node.
    """
    node_id: str
    document_name: str
    question: str
    answer: str
    product: str
    score: float

class QuestionResponse(BaseModel):
    """
    Represents the complete response to a query.

    Attributes:
        answer (str): The generated answer to the query.
        source_nodes (List[SourceNode]): List of source nodes used to generate the answer.
    """
    answer: str
    source_nodes: List[SourceNode]

class RagQuestion:
    """
    Handles Retrieval-Augmented Generation (RAG) question answering using Qdrant vector store.

    This class manages the process of embedding queries, retrieving relevant documents,
    and generating answers using a language model and vector search.

    Attributes:
        llm: Language model used for generating responses.
        embed_model: Model used for embedding text.
        response_synthesizer: Synthesizes responses from retrieved nodes.
        client: Qdrant client for vector database interactions.
        vector_store: Vector store for document embeddings.
        general_qa_prompt_tmpl_str: Prompt template for question answering.
        cohere_rerank: Cohere reranking processor for improving retrieval.
    """

    def __init__(self, llm, embed_model):
        """
        Initialize the RAG question answering system.

        Args:
            llm: Language model for generating responses.
            embed_model: Model for creating text embeddings.
        """
        self.llm = llm
        self.embed_model = embed_model

        self.response_synthesizer = get_response_synthesizer(
            llm=self.llm,
            verbose=True, 
            response_mode=ResponseMode.TREE_SUMMARIZE
        )
        
        self.client = qdrant_client.QdrantClient(url=settings.QDRANT_SERVER, port=settings.QDRANT_PORT)
        self.vector_store = QdrantVectorStore(collection_name=settings.QDRANT_VECTOR_COLLECTION, client=self.client)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        self.general_qa_prompt_tmpl_str = PromptTemplate(general_qa_prompt_tmpl_str)
        self.cohere_rerank = CohereRerank(api_key=settings.COHERE_API_KEY, top_n=7)

    def _query_index(self, query_engine: RetrieverQueryEngine, query: str) -> RESPONSE_TYPE:
        """
        Execute a query on the vector index.

        Args:
            query_engine (RetrieverQueryEngine): Query engine to use for retrieval.
            query (str): The input query string.

        Returns:
            RESPONSE_TYPE: The generated response from the query.

        Raises:
            Exception: If there's an error during the query process.
        """
        try:
            embedded_query = self.embed_model.get_text_embedding(query)
            response = query_engine.query(QueryBundle(query_str=query, embedding=embedded_query))
            return response
        except Exception as e:
            logging.error(f"Error querying index: {str(e)}")
            raise

    def _create_query_engine(self) -> RetrieverQueryEngine:
        """
        Create a query engine for vector-based retrieval.

        Returns:
            RetrieverQueryEngine: Configured query engine with retrieval and post-processing.

        Raises:
            Exception: If there's an error creating the query engine.
        """
        try:
            vector_index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                embed_model=self.embed_model
            )
            
            vector_retriever = VectorIndexRetriever(
                index=vector_index,
                similarity_top_k=25
            )
            
            vector_query_engine = RetrieverQueryEngine(
                retriever=vector_retriever,
                response_synthesizer=self.response_synthesizer,
                node_postprocessors=[
                    SimilarityPostprocessor(similarity_cutoff=0.45), 
                    self.cohere_rerank
                ],
            )
            
            vector_query_engine.update_prompts({"response_synthesizer:text_qa_template": self.general_qa_prompt_tmpl_str})
            
            return vector_query_engine
        except Exception as e:
            logging.error(f"Error creating query engine: {str(e)}")
            raise

    def query(self, query: str) -> QuestionResponse:
        """
        Process a query and generate a response.

        Args:
            query (str): The input query string.

        Returns:
            QuestionResponse: Structured response containing the answer and source nodes.

        Raises:
            Exception: If there's an error during the query process.
        """
        try:
            vector_query_engine = self._create_query_engine()
            response = self._query_index(query_engine=vector_query_engine, query=query)
            return self._process_response(response)
        except Exception as e:
            logging.error(f"Error in general question query: {str(e)}")
            raise

    def _process_response(self, response: RESPONSE_TYPE) -> QuestionResponse:
        """
        Process the raw response into a structured QuestionResponse.

        Args:
            response (RESPONSE_TYPE): The raw response from the query engine.

        Returns:
            QuestionResponse: Structured response with answer and source nodes.
        """
        source_nodes = [
            SourceNode(
                node_id=source_node.node.id_,
                document_name=source_node.node.metadata.get('document_name', 'Unknown'),
                question=source_node.node.get_content(),
                product=source_node.node.metadata.get('product', 'None specified'),
                answer=source_node.node.metadata.get('answer', 'No answer provided'),
                score=source_node.score
            )
            for source_node in response.source_nodes
        ]
        
        return QuestionResponse(
            answer=response.response,
            source_nodes=source_nodes
        )