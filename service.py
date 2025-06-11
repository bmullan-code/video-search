# from dotenv import load_dotenv # Removed
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from video_path import VideoPath
from video_embedding import VideoEmbedding
from vector_search_wrapper import vs
from chromadb_wrapper import cdb
from video_search_results import VideoSearchResults
from storage_wrapper import storage  # Assuming you have a storage_wrapper module
from video_path import VideoPath
from fastapi.staticfiles import StaticFiles

import json, os
import uvicorn
import logging

# --- Logger Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Log to console
        # You can add logging.FileHandler("app.log") here to log to a file
    ]
)
logger = logging.getLogger(__name__)

# prompt:
# create a fastapi interface to expose a set of video search rest methods


# app = FastAPI()

# load_dotenv() # Removed

# It's important that config is imported before other modules that might need it.
import config # Added config import

app = FastAPI(title="Video Search API")
# Ensure ./video-search-frontend/build exists or handle appropriately
# For now, assuming it's part of deployment and will exist.
# Check if STATIC_DIR is defined in config or use a default
static_dir = getattr(config, "STATIC_DIR", "./video-search-frontend/build")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning(f"Static directory {static_dir} not found. Static file serving will be disabled.")

# origins should also ideally come from config
origins = getattr(config, "CORS_ORIGINS", [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
])

origins = [
    "http://localhost",  # Allow requests from localhost
    "http://localhost:3000",  # Specifically allow requests from port 3000
    "http://localhost:8080", # Add any other origins that should have access to your api
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, etc.)
    allow_headers=["*"],  # Allow all headers
)

ve = VideoEmbedding()
# Use config for VECTOR_STORE
vector_store = vs if config.VECTOR_STORE == "VECTOR_SEARCH" else cdb

@app.post("/process_video/", status_code=201)
async def process_video_route(file: UploadFile = File(...)):
    """Processes a video file and adds its embeddings to Pinecone."""
    try:
        logger.info(f"Processing video: {file.filename}")
        vpath = VideoPath(file.filename)  # Create VideoPath from filename
        contents = await file.read()

        # Save to local cache first
        local_video_path = f"{storage.cache}/{vpath.file_name()}"
        with open(local_video_path, "wb") as f:
            f.write(contents)
        logger.info(f"Video {file.filename} saved to cache: {local_video_path}")

        # TODO: Consider uploading to GCS storage here if that's the intended workflow
        # For now, embeddings will be generated from the local cached file
        # storage.upload_file(local_video_path, vpath.file_name()) # Example

        # --- Upload the video to GCS before generating embeddings from GCS path ---
        try:
            logger.info(f"Uploading {local_video_path} to GCS as {vpath.file_name()}")
            storage.upload_file(local_video_path, vpath.file_name())
            logger.info(f"Successfully uploaded {vpath.file_name()} to GCS.")
        except Exception as e:
            logger.error(f"Failed to upload {vpath.file_name()} to GCS: {e}")
            # Clean up cached file
            try:
                os.remove(local_video_path)
                logger.info(f"Cleaned up cached video file: {local_video_path} after upload failure.")
            except OSError as e_os:
                logger.error(f"Error cleaning up cached video file {local_video_path}: {e_os}")
            raise HTTPException(status_code=500, detail=f"Failed to upload video to cloud storage: {str(e)}")

        # Get embeddings using the cache-aware method.
        # This will read from GCS cache or generate (from GCS video) & save to GCS cache.
        video_emb_data = ve.get_video_embedding_with_cache(vpath=vpath)

        if not video_emb_data:
            logger.error(f"Failed to generate/retrieve embeddings for {file.filename}")
            # No need to clean up local_video_path here as it should be in GCS if upload succeeded.
            # If upload failed, it was cleaned up above.
            raise HTTPException(status_code=500, detail="Failed to process video embeddings.")

        # Assuming video_emb_data is a list of dictionaries as per original structure
        records = [
            {
                "id": f"{vpath.file_name()}:{item['startOffsetSec']}:{item['endOffsetSec']}",
                "values": item["embedding"],
                "metadata": {
                    "startOffsetSec": item["startOffsetSec"],
                    "endOffsetSec": item["endOffsetSec"],
                    "videoPath": vpath.path(),  # Store GCS path or original filename
                    "fileName": vpath.file_name(),
                },
            }
            for item in video_emb_data # Changed 've' to 'item' to avoid conflict
        ]

        vector_store.insert(records=records) # Use vector_store consistently
        logger.info(f"Embeddings for {file.filename} inserted into vector store.")

        # Store embedding JSON in GCS -- This is now handled by get_video_embedding_with_cache
        # storage.write_json(video_emb_data, vpath.file_name_json())
        # logger.info(f"Embeddings JSON for {file.filename} stored in GCS: {vpath.file_name_json()}")

        # Clean up the locally cached uploaded video file after successful processing
        try:
            os.remove(local_video_path)
            logger.info(f"Cleaned up cached video file: {local_video_path}")
        except OSError as e_os:
            logger.error(f"Error cleaning up cached video file {local_video_path}: {e_os}")

        return {"message": f"Video {file.filename} processed and embeddings added successfully."}

    except FileNotFoundError as fnf_error: # This might be for local_video_path if open fails, or from storage.upload_file
        logger.error(f"File not found during video processing for {file.filename}: {fnf_error}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(fnf_error)}")
    except Exception as e:
        logger.exception(f"Error processing video {file.filename}: {e}")
        # Clean up cached file if it exists and an error occurs mid-processing
        local_video_path_on_error = f"{storage.cache}/{file.filename}" # Reconstruct path if needed
        if os.path.exists(local_video_path_on_error):
            try:
                os.remove(local_video_path_on_error)
                logger.info(f"Cleaned up cached video file due to error: {local_video_path_on_error}")
            except OSError as e_os:
                logger.error(f"Error cleaning up cached video file {local_video_path_on_error} during error handling: {e_os}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing the video: {str(e)}")

@app.get("/search_by_text/")
async def search_by_text(text: str, top_k: int = 10):
    """Searches for videos by text query."""
    try:
        logger.info(f"Searching by text: '{text}', top_k: {top_k}")
        text_emb = ve.get_text_embedding(text=text)
        if not text_emb:
            logger.warning(f"Could not generate text embedding for: '{text}'")
            raise HTTPException(status_code=500, detail="Failed to generate text embedding.")

        results = vector_store.query(vector=text_emb, top_k=top_k)
        vsr = VideoSearchResults(results)
        logger.info(f"Found {len(vsr.get_results())} results for text search: '{text}'")
        return vsr.get_results()
    except Exception as e:
        logger.exception(f"Error searching by text '{text}': {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during text search: {str(e)}")

@app.post("/search_by_image/")
async def search_by_image(file: UploadFile = File(...), top_k: int = 10):
    """Searches for videos by image."""
    try:
        logger.info(f"Searching by image: {file.filename}, top_k: {top_k}")
        # image_path = VideoPath(file.filename).path() # This might not be what we want if file isn't in GCS yet

        contents = await file.read()
        # Save to local cache for embedding generation
        local_image_path = f"{storage.cache}/{file.filename}"
        with open(local_image_path, "wb") as f:
            f.write(contents)
        logger.info(f"Image {file.filename} saved to cache for processing: {local_image_path}")

        image_emb = ve.get_image_embedding(image_path=local_image_path)
        if not image_emb:
            logger.warning(f"Could not generate image embedding for: '{file.filename}'")
            # Clean up cached file
            try:
                os.remove(local_image_path)
                logger.info(f"Cleaned up cached image: {local_image_path}")
            except OSError as e_os:
                logger.error(f"Error cleaning up cached image {local_image_path}: {e_os}")
            raise HTTPException(status_code=500, detail="Failed to generate image embedding.")

        results = vector_store.query(vector=image_emb, top_k=top_k) # Ensure query takes vector=
        vsr = VideoSearchResults(results)
        logger.info(f"Found {len(vsr.get_results())} results for image search: '{file.filename}'")

        # Clean up cached file
        try:
            os.remove(local_image_path)
            logger.info(f"Cleaned up cached image: {local_image_path}")
        except OSError as e_os:
            logger.error(f"Error cleaning up cached image {local_image_path}: {e_os}")

        return vsr.get_results()

    except FileNotFoundError as fnf_error:
        logger.error(f"File not found during image search processing: {fnf_error}")
        raise HTTPException(status_code=404, detail=f"File not found: {fnf_error.filename}")
    except Exception as e:
        logger.exception(f"Error searching by image {file.filename}: {e}")
        # Clean up cached file if it exists and an error occurs mid-processing
        local_image_path_on_error = f"{storage.cache}/{file.filename}"
        if os.path.exists(local_image_path_on_error):
            try:
                os.remove(local_image_path_on_error)
                logger.info(f"Cleaned up cached image due to error: {local_image_path_on_error}")
            except OSError as e_os:
                logger.error(f"Error cleaning up cached image {local_image_path_on_error} during error handling: {e_os}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during image search: {str(e)}")

@app.get("/video/{filename}")
async def get_video(filename: str):
    """Streams a video from GCS or local cache."""
    try:
        logger.info(f"Requesting video: {filename}")
        vpath = VideoPath(filename)
        local_path = storage.local_file(vpath.file_name()) # Downloads from GCS if not in cache
        logger.info(f"Streaming video '{filename}' from local cache: {local_path}")

        def iterfile():
            with open(local_path, mode="rb") as file_like:
                yield from file_like

        return StreamingResponse(iterfile(), media_type="video/mp4")

    except FileNotFoundError: # Raised by storage.local_file if GCS blob doesn't exist
        logger.error(f"Video file not found in GCS or cache: {filename}")
        raise HTTPException(status_code=404, detail=f"Video file not found: {filename}")
    except Exception as e:
        logger.exception(f"Error streaming video {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while retrieving the video: {str(e)}")

# uvicorn service:app --reload --host 0.0.0.0 --port 8000
# Ensure the main execution block also uses the logger if needed, or is removed if not for production.
if __name__ == "__main__":
    logger.info("Starting FastAPI server with uvicorn.")
    uvicorn.run(app, host="0.0.0.0", port=8000)

