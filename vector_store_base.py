from abc import ABC, abstractmethod
from typing import List, Dict, TYPE_CHECKING

# Use TYPE_CHECKING to avoid circular import issues if VideoPath might import VectorStoreBase
# or if direct import is problematic for other reasons.
# However, for simple type hinting of parameters/return values, a string literal is often sufficient.
if TYPE_CHECKING:
    from video_path import VideoPath

class VectorStoreBase(ABC):
    """
    Abstract base class defining the interface for vector store operations.
    Concrete implementations of vector stores (e.g., ChromaDB, Vertex AI Vector Search)
    should inherit from this class and implement its methods.
    """

    @abstractmethod
    def insert(self, embedding_results: List[Dict], vpath: 'VideoPath') -> None:
        """
        Inserts video embeddings into the vector store.

        The `embedding_results` are expected to be a list of dictionaries,
        where each dictionary contains details for a video segment embedding.
        Example structure for each item in `embedding_results`:
        {
            "startOffsetSec": int,  # Start offset of the segment in seconds
            "endOffsetSec": int,    # End offset of the segment in seconds
            "embedding": List[float] # The embedding vector for this segment
        }

        Args:
            embedding_results (List[Dict]): A list of embedding dictionaries for video segments.
            vpath ('VideoPath'): A VideoPath object representing the video, used for
                                 generating unique IDs and storing metadata.

        Returns:
            None
        """
        pass

    @abstractmethod
    def query(self, vector: List[float], top_k: int = 3) -> List[Dict]:
        """
        Performs a nearest neighbor search in the vector store for the given vector.

        Args:
            vector (List[float]): The embedding vector to query with.
            top_k (int): The number of nearest neighbors to retrieve. Defaults to 3.

        Returns:
            List[Dict]: A list of dictionaries, where each dictionary represents a
                        search result. Each result dictionary should ideally include
                        at least 'id' (str), 'distance' (float), and optionally
                        'metadata' (Dict) or other relevant fields.
                        Example: [{"id": "video.mp4:0:10", "distance": 0.85, "metadata": {...}}, ...]
        """
        pass
