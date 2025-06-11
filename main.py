from video_path import VideoPath
from video_embedding import VideoEmbedding
from pinecone_wrapper import PineconeWrapper
from vector_search_wrapper import VectorSearch
from storage_wrapper import storage
from video_search_results import VideoSearchResults
import json
# import os # No longer needed
from chromadb_wrapper import cdb
from vector_search_wrapper import vs
from video_transcript import VideoTranscript
# from dotenv import load_dotenv # Removed
import logging # Added logging
import config # Added config import

# load_dotenv() # Removed

# Basic logging configuration
# This will be configured by config.py if it's imported first at service startup,
# or can be left here if main.py can be run standalone.
# For consistency, if service.py or another entry point configures logging based on config.py,
# this might be redundant or could be removed if main.py isn't a primary entry point.
# Let's assume config.py might not always be the first importer of logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

vector_store = vs if (config.VECTOR_STORE == "VECTOR_SEARCH") else cdb # Use config
ve = VideoEmbedding() # VideoEmbedding instance

# Removed get_or_create_video_embedding function

def process_video(vpath: VideoPath):
    logger.info(f"Processing video: {vpath.path()}")

    video_emb_data = [] # Initialize with empty list
    try:
        # Get video embeddings using the new cache-aware method
        video_emb_data = ve.get_video_embedding_with_cache(vpath=vpath)
    except Exception as e:
        logger.error(f"Failed to get video embedding for {vpath.path()}: {e}")
        return # Skip this video if embedding fails

    if not video_emb_data:
        logger.warning(f"No embedding data returned for {vpath.path()}, skipping vector store insertion and transcript.")
        return

    # Transform embeddings into the record structure expected by vector_store.insert
    # (similar to service.py)
    records_to_insert = [
        {
            "id": f"{vpath.file_name()}:{item['startOffsetSec']}:{item['endOffsetSec']}",
            "values": item["embedding"],
            "metadata": {
                "startOffsetSec": item["startOffsetSec"],
                "endOffsetSec": item["endOffsetSec"],
                "videoPath": vpath.path(),
                "fileName": vpath.file_name(),
            },
        }
        for item in video_emb_data
    ]

    if not records_to_insert:
        logger.warning(f"No records to insert for {vpath.path()} after processing embeddings.")
        return

    try:
        vector_store.insert(records=records_to_insert)
        logger.info(f"Successfully inserted embeddings for {vpath.path()} into vector store.")
    except Exception as e:
        logger.error(f"Failed to insert embeddings for {vpath.path()} into vector store: {e}")
        return # Stop processing this video if insertion fails

    # Create transcript (using gemini)
    try:
        logger.info(f"Creating transcript for {vpath.path()}...")
        video_transcript = VideoTranscript(video_path=vpath).create()
        if video_transcript:
            logger.info(f"Successfully created transcript for {vpath.path()}")
        else:
            logger.warning(f"Transcript creation returned no result for {vpath.path()}")
    except Exception as e:
        logger.error(f"Failed to create transcript for {vpath.path()}: {e}")

    # todo - rag based on transcript (chunk into ~30 second blocks) (filter to select transcript search)
    # todo - hybrid search based on transcript (get all transcript segments around a segment (min 4 sec) and store with video embeddings)
    # todo - rag based on transcript (chunk into ~30 second blocks) (filter to select transcript search)
    # todo - hybrid search based on transcript (get all transcript segments around a segment (min 4 sec) and store with video embeddings)
    # todo - frame metadata extraction using gemini (store metadata with embeddings ?) filter based on meta data
    # todo - add meta data based on image search in frame eg. a particular person, object, brand etc. 

if __name__ == "__main__":
    logger.info("Starting video processing main script.")
    # Fetch video files from GCS, filtering for .mp4 extensions
    video_files = storage.list_files(extension=".mp4")

    if not video_files:
        logger.info("No .mp4 files found in the GCS bucket.")
    else:
        logger.info(f"Found video files: {video_files}")
        for video_filename in video_files:
            video_path = VideoPath(video_filename)
            process_video(video_path)
    logger.info("Finished video processing main script.")