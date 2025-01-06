# app/services/rag_search.py
import json
import logging
from typing import Dict, List, Optional, Any

import qdrant_client
from pydantic import BaseModel

from llama_index.core import (
    VectorStoreIndex,
    QueryBundle,
    PromptTemplate,
    get_response_synthesizer,
    set_global_handler
)
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)
from llama_index.core.base.response.schema import RESPONSE_TYPE
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers.type import ResponseMode
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.settings import Settings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.postprocessor.cohere_rerank import CohereRerank
from llama_index.vector_stores.qdrant import QdrantVectorStore

from prompt import qa_prompt_tmpl_str

from config import settings

# Set a simple global error handler for llama_index
set_global_handler("simple")

class SourceNode(BaseModel):
    """
    Represents a single source node with metadata about a retrieved document.

    Attributes:
        node_id (str): Unique identifier for the node.
        document_name (str): Name of the source document.
        question (str): Content of the node (typically a question or text).
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

class QueryResponse(BaseModel):
    """
    Represents the complete response to a query.

    Attributes:
        suggested_answer (Optional[str]): The generated answer to the query, if available.
        source_nodes (List[SourceNode]): List of source nodes used to generate the answer.
    """
    suggested_answer: Optional[str] = None
    source_nodes: List[SourceNode]
    
class RagSearch:
    """
    Handles Retrieval-Augmented Generation (RAG) search using Qdrant vector store.

    This class manages the process of embedding queries, retrieving relevant documents,
    and generating answers using OpenAI's language and embedding models.

    Attributes:
        response_synthesizer: Synthesizes responses from retrieved nodes.
        client: Qdrant client for vector database interactions.
        vector_store: Vector store for document embeddings.
        storage_context: Storage context for the vector store.
        qa_prompt_tmpl: Prompt template for question answering.
        cohere_rerank: Cohere reranking processor for improving retrieval.
    """

    def __init__(self):
        """
        Initialize the RAG search system.

        Sets up OpenAI language and embedding models, Qdrant vector store,
        response synthesizer, and other necessary components.
        """
        # Configure OpenAI models for language and embedding
        Settings.llm = OpenAI(model=settings.OPENAI_LLM_MODEL, temperature=settings.TEMPERATURE, api_key=settings.OPENAI_API_KEY)
        Settings.embed_model = OpenAIEmbedding(model=settings.OPENAI_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)            
    
        # Create response synthesizer with compact response mode
        self.response_synthesizer = get_response_synthesizer(
            llm=Settings.llm,
            verbose=True, 
            response_mode=ResponseMode.COMPACT
        )

        # Set up Qdrant vector store client and storage
        self.client = qdrant_client.QdrantClient(url=settings.QDRANT_SERVER, port=settings.QDRANT_PORT)
        self.vector_store = QdrantVectorStore(collection_name=settings.QDRANT_VECTOR_COLLECTION, client=self.client)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

        # Configure prompt template and reranking
        self.qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
        self.cohere_rerank = CohereRerank(api_key=settings.COHERE_API_KEY, top_n=3)

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
            # Embed the query using the configured embedding model
            embedded_query = Settings.embed_model.get_text_embedding(query)
            
            # Execute the query with both text and embedding
            response = query_engine.query(QueryBundle(query_str=query, embedding=embedded_query))
            return response
        except Exception as e:
            logging.error(f"Error querying index: {str(e)}")
            raise

    def _create_query_engine(self, product: str) -> RetrieverQueryEngine:
        """
        Create a query engine with optional product-based filtering.

        Args:
            product (str): Product to filter results by. 'All' means no filtering.

        Returns:
            RetrieverQueryEngine: Configured query engine with optional filtering.

        Raises:
            Exception: If there's an error creating the query engine.
        """
        # Create metadata filter if a specific product is specified
        filter = None
        if product != "All":
            filter = MetadataFilters(
                filters=[
                    MetadataFilter(key="product", operator=FilterOperator.EQ, value=product),
                ],
            )
            
        try:
            # Create vector index from the vector store
            vector_index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store, 
                embed_model=Settings.embed_model
            )
            
            # Create vector retriever with optional filtering
            vector_retriever = VectorIndexRetriever(
                index=vector_index, 
                similarity_top_k=7,
                filters=filter
            )
            
            # Create query engine with retriever, synthesizer, and post-processors
            vector_query_engine = RetrieverQueryEngine(
                retriever=vector_retriever,
                response_synthesizer=self.response_synthesizer,
                node_postprocessors=[
                    SimilarityPostprocessor(similarity_cutoff=0.45), 
                    self.cohere_rerank
                ],
            )
            
            # Update prompt template for response synthesis
            vector_query_engine.update_prompts({"response_synthesizer:text_qa_template": self.qa_prompt_tmpl})
            
            return vector_query_engine
        except Exception as e:
            logging.error(f"Error creating query engine: {str(e)}")
            raise

    def query_rag(self, query: str, product: str = "All") -> QueryResponse:
        """
        Perform a Retrieval-Augmented Generation (RAG) query.

        Args:
            query (str): The input query string.
            product (str, optional): Product to filter results by. Defaults to "All".

        Returns:
            QueryResponse: Structured response containing suggested answer and source nodes.

        Raises:
            Exception: If there's an error during the RAG query process.
        """
        try:
            # Create query engine with optional product filtering
            vector_query_engine = self._create_query_engine(product=product)
            
            # Execute the query
            response = self._query_index(query_engine=vector_query_engine, query=query)
            logging.info(f"query_rag -> response: {response}")
            
            # Process and return the response
            return self._process_response(response)
        except Exception as e:
            logging.error(f"Error in RAG query: {str(e)}")
            raise

    def _process_response(self, response: RESPONSE_TYPE) -> QueryResponse:
        """
        Process the raw response into a structured QueryResponse.

        Attempts to parse the response as JSON to extract a suggested answer.

        Args:
            response (RESPONSE_TYPE): The raw response from the query engine.

        Returns:
            QueryResponse: Structured response with suggested answer and source nodes.
        """
        try:
            # Log the original response
            logging.info(f"_process_response -> response.response: {response.response}")
            
            # Try to parse the response as JSON
            parsed_response = json.loads(response.response)
            logging.info(f"_process_response -> parsed_response: {parsed_response}")
            
            # Extract suggested answer, defaulting to None if not found
            suggested_answer = parsed_response.get("suggested_answer", None)
            logging.info(f"_process_response -> suggested_answer: {suggested_answer}")
        
        except json.JSONDecodeError:
            # Handle JSON parsing errors
            logging.error("Failed to parse JSON response")
            suggested_answer = "Failed to extract suggested answer"
        
        # Create source nodes from the response
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
        
        # Log the final processed response details
        logging.info(f"Suggested Answer: {suggested_answer}")
        logging.info(f"Source Nodes: {source_nodes}")
        
        # Return structured query response
        return QueryResponse(
            suggested_answer=suggested_answer,
            source_nodes=source_nodes
        )