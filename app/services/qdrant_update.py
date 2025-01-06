# app/services/qdrant_update.py
import json
from qdrant_client import QdrantClient
from config import settings

class QdrantUpdater:
    """
    A service class for updating documents in a Qdrant vector database collection.

    This class provides functionality to retrieve and update document metadata 
    in a Qdrant vector store, specifically focusing on updating the 'answer' 
    field for a given node.

    Attributes:
        client (QdrantClient): Client for interacting with the Qdrant vector database.
        collection_name (str): Name of the vector collection being updated.
    """

    def __init__(self, host=settings.QDRANT_SERVER, port=settings.QDRANT_PORT, collection_name=settings.QDRANT_VECTOR_COLLECTION):
        """
        Initialize the QdrantUpdater with connection details for the Qdrant database.

        Args:
            host (str, optional): Hostname of the Qdrant server. 
                                  Defaults to value from settings.
            port (int, optional): Port number for the Qdrant server. 
                                  Defaults to value from settings.
            collection_name (str, optional): Name of the vector collection. 
                                             Defaults to value from settings.
        """
        self.client = QdrantClient(url=host, port=port)
        self.collection_name = collection_name

    def update_document(self, node_id: str, answer: str):
        """
        Update the answer for a specific document node in the Qdrant collection.

        This method retrieves an existing point by its node_id, updates its payload 
        to include the new answer, and then sets the updated payload back to Qdrant.

        Args:
            node_id (str): Unique identifier of the node to be updated.
            answer (str): New answer text to be associated with the node.

        Returns:
            dict: A dictionary containing the node_id and the updated answer.

        Raises:
            ValueError: If no point is found with the given node_id in the collection.
        """
        # Retrieve the existing point from Qdrant
        retrieved_points = self.client.retrieve(self.collection_name, [node_id])
        
        # Raise an error if the node is not found
        if not retrieved_points:
            raise ValueError(f"Point with node_id {node_id} not found")

        # Get the first (and should be only) retrieved point
        point = retrieved_points[0]

        # Parse the node content from the payload
        node_content = json.loads(point.payload["_node_content"])
        
        # Update the answer in the node's metadata
        node_content["metadata"]["answer"] = answer
        
        # Prepare the updated payload
        updated_payload = {
            "_node_content": json.dumps(node_content),
            "answer": answer
        }
        
        # Set the updated payload in Qdrant
        self.client.set_payload(
            collection_name=self.collection_name,
            payload=updated_payload,
            points=[node_id]
        )

        # Return the details of the update
        return {"node_id": node_id, "updated_answer": answer}