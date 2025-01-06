# ragbuilder.py
import os
import json
import argparse
from typing import Any, Dict, List
from llama_index.core import (
    VectorStoreIndex, 
    Document, 
    Settings,
)
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage.storage_context import StorageContext
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client

from app.config import settings

class QARagBuilder:
    """
    A class to build and manage a RAG system for question-answer pairs using Qdrant as the vector store
    and OpenAI for embeddings and language modeling.

    The class handles the entire pipeline from loading QA pairs to storing them in a vector database,
    including text splitting, embedding generation, and vector storage management.

    Attributes:
        client: A Qdrant client instance for vector database operations
        vector_store: A QdrantVectorStore instance for managing vector storage
        storage_context: A StorageContext instance for managing storage operations
        text_splitter: A SentenceSplitter instance for chunking text into appropriate sizes
    """
    
    def __init__(self):        
        """
        Initializes the QARagBuilder with OpenAI models and Qdrant vector store configurations.
        Sets up the necessary components including LLM, embedding model, vector store, and text splitter.
        """
        Settings.llm = OpenAI(model=settings.OPENAI_LLM_MODEL, temperature=settings.TEMPERATURE, api_key=settings.OPENAI_API_KEY)
        Settings.embed_model = OpenAIEmbedding(model=settings.OPENAI_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY, num_workers=8)

        # Try connecting to Qdrant with different configurations
        self.client = self._setup_qdrant_client()
        
        self.vector_store = QdrantVectorStore(collection_name=settings.QDRANT_VECTOR_COLLECTION, 
                                            client=self.client,
                                            enable_hybrid=False)
        
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.text_splitter = SentenceSplitter(chunk_size=2048, chunk_overlap=256)

    def _setup_qdrant_client(self):
        """
        Attempts to establish a connection to the Qdrant server using multiple fallback configurations.

        Returns:
            qdrant_client.QdrantClient: A connected Qdrant client instance

        Raises:
            ConnectionError: If unable to connect to Qdrant with any of the configurations
        """
        # List of possible Qdrant configurations to try
        configs = [
            {"url": settings.QDRANT_SERVER, "port": settings.QDRANT_PORT},
            {"url": "localhost", "port": settings.QDRANT_PORT},  # Local fallback
            {"url": "127.0.0.1", "port": settings.QDRANT_PORT},  # Alternative local fallback
        ]

        last_exception = None
        for config in configs:
            try:
                client = qdrant_client.QdrantClient(**config)
                # test the connection by making a simple API call
                client.get_collections()
                print(f"Successfully connected to Qdrant at {config['url']}:{config['port']}")
                return client
            except Exception as e:
                last_exception = e
                print(f"Failed to connect to Qdrant at {config['url']}:{config['port']}: {str(e)}")
                continue

        raise ConnectionError(f"Could not connect to Qdrant with any configuration. Last error: {str(last_exception)}")

    def write_to_vectordb(self, nodes: List[BaseNode]):
        """
        Writes the provided nodes to the vector database using the configured embedding model.

        Args:
            nodes (List[BaseNode]): A list of nodes to be written to the vector database

        Raises:
            Exception: If writing to the vector database fails
        """
        try:
            VectorStoreIndex(nodes=nodes,
                           embed_model=Settings.embed_model,
                           storage_context=self.storage_context,
                           show_progress=True)
        except Exception as e:
            print(f"Failed to write nodes to vector db: {str(e)}")

    def get_semantic_vector(self, text: str) -> List[float]:
        """
        Generates a semantic vector embedding for the provided text using the configured embedding model.

        Args:
            text (str): The text to generate an embedding for

        Returns:
            List[float]: The generated embedding vector
        """
        embedding = Settings.embed_model.get_text_embedding(text)
        return embedding
    
    def get_question_answers(self, qa_directory: str) -> List[Dict[str, Any]]:
        """
        Loads question-answer pairs from JSON files in the specified directory.

        Args:
            qa_directory (str): Path to the directory containing QA JSON files

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing the loaded QA pairs
        """
        all_data = []
        try:
            for filename in os.listdir(qa_directory):
                if filename.endswith('.json'):
                    file_path = os.path.join(qa_directory, filename)
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            all_data.append(data)
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON from file: {filename}")
                    except IOError:
                        print(f"Error reading file: {filename}")
        except FileNotFoundError as e:
            print(f"{e}")
        
        return all_data
    
    def split_text_and_create_nodes(self, documents: List[Document]) -> List[BaseNode]:
        """
        Splits the provided documents into nodes using the configured text splitter and enriches
        them with metadata.

        Args:
            documents (List[Document]): The documents to be split into nodes

        Returns:
            List[BaseNode]: A list of enriched nodes created from the documents
        """
        nodes = self.text_splitter.get_nodes_from_documents(documents)
        enriched_nodes = []
        
        for node in nodes:
            metadata = node.metadata if node.metadata else {}
            
            node.metadata = metadata
            enriched_nodes.append(node)
            
        return enriched_nodes
    
    def load_data(self, text_list: List[Dict[str, Any]]) -> List[Document]:
        """
        Processes a list of text data into Documents with associated metadata.

        Args:
            text_list (List[Dict[str, Any]]): A list of dictionaries containing text data and metadata

        Returns:
            List[Document]: A list of Document objects with processed text and metadata
        """
        documents = []
        
        for text in text_list:
            document_name = text.get('document_name', '')
            
            for row in text.get('data', []):
                question = row.get('question', '')
                
                combined_metadata = {'document_name': document_name}
                
                for key, value in row.items():
                    if key != 'question':
                        combined_metadata[key] = value if isinstance(value, str) else value
                
                documents.append(Document(text=question, metadata=combined_metadata))
        
        return documents

def main():
    """
    Main function to process vendor Question and Answer documents.
    Handles command-line arguments and orchestrates the RAG building process.
    """
    parser = argparse.ArgumentParser(description='Process Vendor Question and Answer documents from a specified directory')
    parser.add_argument('--qa_directory', type=str, 
                       default='./app/data/questions_and_answers',
                       help='Path to the directory containing Question and Answer JSON files')
    args = parser.parse_args()

    rag = QARagBuilder()
    
    # Get question answers from the specified directory
    question_answers = rag.get_question_answers(qa_directory=args.qa_directory)
    if question_answers:
        documents = rag.load_data(text_list=question_answers)
        nodes = rag.split_text_and_create_nodes(documents=documents)
        rag.write_to_vectordb(nodes=nodes)

if __name__ == "__main__":
    main()