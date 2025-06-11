# provides a basic wrapper around vertex ai vector search. 

# from dotenv import load_dotenv # Removed
# import os # Removed
from google.cloud import aiplatform
from storage_wrapper import storage
from video_path import VideoPath
import config # Added config import
import logging # Added logging
from typing import List, Dict # Added typing imports
from vector_store_base import VectorStoreBase # Added base class import

# load_dotenv() # Removed

logger = logging.getLogger(__name__) # Added logger

class VectorSearch(VectorStoreBase): # Inherit from VectorStoreBase

    # initialize with 3 values from the vector search index and index endpoint. 
    # these values can be looked up in the vector search console in vertexai
    # eg. 
    # VECTOR_SEARCH_INDEX="projects/173481798756/locations/us-central1/indexes/7718532044568920064"
    # DEPLOYED_INDEX_ID="quickstart1_1739716044566"
    # INDEX_ENDPOINT_ID = "1756364272255893504"

    def __init__(self, 
                project = config.PROJECT_ID,
                location = config.LOCATION,
                index = config.VECTOR_SEARCH_INDEX,
                index_endpoint_id = config.INDEX_ENDPOINT_ID,
                deployed_index_id = config.DEPLOYED_INDEX_ID
        ):
            self.project = project  # Instance attribute
            self.location = location  # Instance attribute
            aiplatform.init(project=self.project, location=self.location)
            self.index = aiplatform.MatchingEngineIndex(index_name=index)
            self.index_endpoint_id = index_endpoint_id
            self.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(self.index_endpoint_id)
            self.deployed_index_id = deployed_index_id

    # converte the embeddings from MultiModalEmbeddings model output to vector search format
    def _convert_to_datapoints(self, embedding_results: List[Dict], vpath: 'VideoPath') -> List[Dict]:
        """Converts embedding results to the format required by Vertex AI Vector Search."""
        datapoints = []
        for item in embedding_results:
            datapoint_id = f"{vpath.file_name()}:{item['startOffsetSec']}:{item['endOffsetSec']}"
            feature_vector = item["embedding"]
            # Vertex AI Vector Search also allows a list of "restricts" and "crowding_tag" per datapoint if needed.
            # For now, keeping it simple.
            datapoints.append(
                {
                    "datapoint_id": datapoint_id,
                    "feature_vector": feature_vector,
                    # Example of adding restricts if needed:
                    # "restricts": [
                    #     {"namespace": "source", "allow_list": [vpath.file_name()]},
                    #     {"namespace": "segment_duration", "allow_list": [str(item['endOffsetSec'] - item['startOffsetSec'])]}
                    # ]
                }
            )
        return datapoints

    def insert(self, embedding_results: List[Dict], vpath: 'VideoPath') -> None:
        """
        Inserts video embeddings into Vertex AI Vector Search.
        Converts embedding_results to the required datapoint format and upserts them.
        """
        if not embedding_results:
            logger.warning(f"No embedding results provided for {vpath.file_name()}, skipping insertion.")
            return

        datapoints = self._convert_to_datapoints(embedding_results, vpath)

        # Upsert datapoints in batches (Vertex AI limit is typically 1000 per call, but can be up to 20,000 for some)
        # The upsert_datapoints method of the SDK handles batching internally up to a certain limit,
        # but being explicit can be safer for very large inputs or if lower limits are hit.
        # However, the SDK's upsert_datapoints takes a list of datapoints directly.
        # Let's use a smaller batch size for demonstration if we were doing it manually.
        # For now, we trust the SDK to handle reasonable batching for a single index.upsert_datapoints call.
        # The example showed looping with 1000, which is fine.

        for i in range(0, len(datapoints), 1000): # Batching by 1000
            batch = datapoints[i : i + 1000]
            try:
                logger.info(f"Upserting batch of {len(batch)} datapoints for {vpath.file_name()} (starting from index {i}).")
                self.index.upsert_datapoints(datapoints=batch)
                logger.info(f"Successfully upserted batch for {vpath.file_name()} (index {i} to {i+len(batch)-1}).")
            except Exception as e:
                logger.error(f"Error upserting datapoints for {vpath.file_name()} (batch starting {i}): {e}")
                # Optionally, re-raise or handle more gracefully (e.g., collect failures)
                # For now, just log and continue if possible, or re-raise if critical
                raise


    def query(self, vector: List[float], top_k: int = 3) -> List[Dict]:
        """
        Performs a nearest neighbor search in Vertex AI Vector Search.
        Returns a list of search results, each containing 'id' and 'distance'.
        Additional metadata might be included if returned by the service and configured.
        """
        if not vector:
            logger.warning("Query called with an empty vector.")
            return []
        try:
            results = self.index_endpoint.find_neighbors(
                deployed_index_id=self.deployed_index_id,
                queries=[vector],
                num_neighbors=top_k,
            )

            output_results = []
            if results and results[0]: # find_neighbors returns a list of lists of MatchNeighbor
                for neighbor in results[0]:
                    # neighbor.id, neighbor.distance
                    # neighbor.feature_vector (if requested and available)
                    # neighbor.restricts (if any)
                    # neighbor.crowding_tag (if any)
                    output_results.append(
                        {
                            "id": neighbor.id, # This is the datapoint_id
                            "distance": neighbor.distance,
                            # We don't have direct metadata here unless it's part of the ID
                            # or if we fetch it separately using the ID.
                            # For now, we'll parse from ID if possible, or keep it simple.
                            # Example of trying to parse metadata from ID:
                            # parts = neighbor.id.split(':')
                            # metadata = {"file_name": parts[0], "start": parts[1], "end": parts[2]} if len(parts) == 3 else {}
                        }
                    )
            return output_results
        except Exception as e:
            logger.error(f"Error during Vector Search query: {e}")
            return [] # Return empty list on error

vs = VectorSearch()