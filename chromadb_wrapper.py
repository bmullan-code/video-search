import chromadb
from chromadb.config import Settings
from video_path import VideoPath
# from dotenv import load_dotenv # Removed
# import os # Removed
import config # Added config import
from typing import List, Dict # Added typing
from vector_store_base import VectorStoreBase # Added base class
import logging # Added logging

# load_dotenv() # Removed
logger = logging.getLogger(__name__)

class ChromaDB(VectorStoreBase): # Inherit from VectorStoreBase

    def __init__(self, collection_name = config.CHROMADB_COLLECTION_NAME):
        logger.info(f"Initializing ChromaDB with collection: {collection_name}, path: .chromadb")
        self.client = chromadb.PersistentClient(path=".chromadb") # TODO: Make path configurable?
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                # Optionally, specify metadata for the collection, e.g., embedding function details
                # metadata={"hnsw:space": "cosine"} # Example for cosine distance
            )
            logger.info(f"Successfully got or created collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to get or create ChromaDB collection {collection_name}: {e}")
            raise

    # Old convertEmbeddings method is removed. Logic integrated into insert.

    def insert(self, embedding_results: List[Dict], vpath: 'VideoPath') -> None:
        """
        Inserts video embeddings into ChromaDB.
        Each embedding result is transformed into a document with ID, embedding vector, and metadata.
        """
        if not embedding_results:
            logger.warning(f"No embedding results provided for {vpath.file_name()}, skipping insertion.")
            return

        ids_list = []
        embeddings_list = []
        metadatas_list = []

        for item in embedding_results:
            segment_id = f"{vpath.file_name()}:{item['startOffsetSec']}:{item['endOffsetSec']}"
            ids_list.append(segment_id)
            embeddings_list.append(item["embedding"])
            metadatas_list.append({
                "video_filename": vpath.file_name(),
                "gcs_path": vpath.path(), # Storing the GCS path for reference
                "start_offset_sec": int(item['startOffsetSec']), # Ensure int for filtering if needed
                "end_offset_sec": int(item['endOffsetSec']),
            })

        if not ids_list: # Should not happen if embedding_results is not empty, but good check
            logger.warning(f"No data to insert for {vpath.file_name()} after processing embedding_results.")
            return

        try:
            logger.info(f"Adding {len(ids_list)} embeddings to ChromaDB for {vpath.file_name()}.")
            # Note: ChromaDB's add can take lists of embeddings, metadatas, documents, and ids.
            # If 'documents' are not provided, they are often not stored or searchable by text.
            # For video segments, the 'transcript' or a summary could be a document.
            # Here, we are primarily storing embeddings with metadata.
            self.collection.add(
                embeddings=embeddings_list,
                ids=ids_list,
                metadatas=metadatas_list
            )
            logger.info(f"Successfully added {len(ids_list)} embeddings to ChromaDB for {vpath.file_name()}.")
        except Exception as e:
            logger.error(f"Error adding embeddings to ChromaDB for {vpath.file_name()}: {e}")
            # Optionally re-raise or handle more gracefully
            raise
     
    def query(self, vector: List[float], top_k: int = 3) -> List[Dict]:
        """
        Performs a nearest neighbor search in ChromaDB.
        Returns a list of search results, each including id, distance, and metadata.
        """
        if not vector:
            logger.warning("Query called with an empty vector.")
            return []
        try:
            results = self.collection.query(
                query_embeddings=[vector],
                n_results=top_k,
                include=['metadatas', 'distances'] # Request metadatas and distances
            )

            output_results = []
            # ChromaDB query results format:
            # results = {
            # 'ids': [['id1', 'id2']],
            # 'embeddings': None, (or list of lists of embeddings if include=['embeddings'])
            # 'documents': None, (or list of lists of documents if include=['documents'])
            # 'metadatas': [[{'meta1': 'val1'}, {'meta2': 'val2'}]],
            # 'distances': [[0.1, 0.2]]
            # }
            # We are interested in the first query's results (index 0 of each list).

            if results and results["ids"] and results["ids"][0]:
                ids = results["ids"][0]
                distances = results["distances"][0] if results.get("distances") and results["distances"] else [None] * len(ids)
                metadatas = results["metadatas"][0] if results.get("metadatas") and results["metadatas"] else [{}] * len(ids)

                for i in range(len(ids)):
                    output_results.append({
                        "id": ids[i],
                        "distance": distances[i],
                        "metadata": metadatas[i]
                    })
            else:
                logger.info("ChromaDB query returned no results.")

            return output_results
        except Exception as e:
            logger.error(f"Error during ChromaDB query: {e}")
            return []


cdb = ChromaDB()

