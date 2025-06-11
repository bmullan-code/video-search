# from dotenv import load_dotenv # Removed
from fastapi import FastAPI, HTTPException, UploadFile, File, Query # Added Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from video_path import VideoPath
from video_embedding import VideoEmbedding
# from vector_search_wrapper import vs # Removed
# from chromadb_wrapper import cdb # Removed
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
from vector_store_factory import get_vector_store # Added factory import

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
origins = getattr(config, "CORS_ORIGINS", [ # This is the correct definition
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
])

# Remove duplicate origins definition:
# origins = [
#     "http://localhost",
#     "http://localhost:3000",
#     "http://localhost:8080",
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, etc.)
    allow_headers=["*"],  # Allow all headers
)

ve = VideoEmbedding()
# Use factory for VECTOR_STORE
vector_store = get_vector_store()

@app.post("/process_video/", status_code=201)
async def process_video_route(file: UploadFile = File(...)):
    """Processes a video file and adds its embeddings to Pinecone."""
    try:
        logger.info(f"Received request to process video: {file.filename}")

        original_filename = file.filename
        safe_basename = os.path.basename(original_filename)
        if not safe_basename or safe_basename in [".", ".."] or safe_basename != original_filename: # Added original_filename check
            logger.error(f"Invalid video filename uploaded: {original_filename}")
            raise HTTPException(status_code=400, detail="Invalid video filename.")

        # Use safe_basename for VideoPath and further operations
        vpath = VideoPath(safe_basename)
        logger.info(f"Processing sanitized video filename: {safe_basename}")

        contents = await file.read()

        # File Type and Size Validation (Basic)
        ALLOWED_VIDEO_CONTENT_TYPES = ["video/mp4"]
        MAX_VIDEO_SIZE_MB = 100  # Adjust as needed
        MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024

        if file.content_type not in ALLOWED_VIDEO_CONTENT_TYPES:
            logger.error(f"Invalid video content type: {file.content_type} for file {safe_basename}")
            raise HTTPException(status_code=400, detail=f"Invalid video file type. Allowed: {', '.join(ALLOWED_VIDEO_CONTENT_TYPES)}")

        if len(contents) == 0:
            logger.error(f"Empty video file uploaded: {safe_basename}")
            raise HTTPException(status_code=400, detail="Empty video file.")

        if len(contents) > MAX_VIDEO_SIZE_BYTES: # Check size of read contents
            logger.error(f"Video file too large: {safe_basename}, size: {len(contents)} bytes. Max: {MAX_VIDEO_SIZE_BYTES} bytes.")
            raise HTTPException(status_code=413, detail=f"Video file too large. Max size: {MAX_VIDEO_SIZE_MB}MB.")

        # Save to local cache first, using the sanitized name via vpath
        local_video_path = f"{storage.cache}/{vpath.file_name()}" # vpath.file_name() is from safe_basename
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

        # The 'records' transformation is now handled by the specific vector store wrapper.
        # Directly pass embedding_results (video_emb_data) and vpath.
        vector_store.insert(embedding_results=video_emb_data, vpath=vpath)
        logger.info(f"Embeddings for {file.filename} processed via vector store.")

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

    except FileNotFoundError as fnf_error:
        # Use safe_basename or original_filename in log, depending on when error might occur
        logger.error(f"File not found during video processing for {original_filename if 'original_filename' in locals() else file.filename}: {fnf_error}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(fnf_error)}")
    except HTTPException as http_exc: # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        logger.exception(f"Error processing video {original_filename if 'original_filename' in locals() else file.filename}: {e}")
        # Clean up cached file if it exists and an error occurs mid-processing
        # Ensure local_video_path was defined; it might not be if error is very early
        if 'local_video_path' in locals() and os.path.exists(local_video_path):
            try:
                os.remove(local_video_path)
                logger.info(f"Cleaned up cached video file due to error: {local_video_path}")
            except OSError as e_os:
                logger.error(f"Error cleaning up cached video file {local_video_path} during error handling: {e_os}")
        elif 'safe_basename' in locals(): # Fallback if local_video_path wasn't formed
             local_video_path_on_error = f"{storage.cache}/{safe_basename}"
             if os.path.exists(local_video_path_on_error):
                try:
                    os.remove(local_video_path_on_error)
                    logger.info(f"Cleaned up cached video file due to error: {local_video_path_on_error}")
                except OSError as e_os:
                    logger.error(f"Error cleaning up cached video file {local_video_path_on_error} during error handling: {e_os}")
        if os.path.exists(local_video_path_on_error):
            try:
                os.remove(local_video_path_on_error)
                logger.info(f"Cleaned up cached video file due to error: {local_video_path_on_error}")
            except OSError as e_os:
                logger.error(f"Error cleaning up cached video file {local_video_path_on_error} during error handling: {e_os}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing the video: {str(e)}")

@app.get("/search_by_text/")
async def search_by_text(
    text: str = Query(..., min_length=1, max_length=500, description="Text to search for in videos."),
    top_k: int = Query(10, ge=1, le=50, description="Number of top results to return.")
):
    """Searches for videos by text query."""
    try:
        # Input 'text' is already validated by FastAPI's Query for length.
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
        logger.info(f"Received request to search by image: {file.filename}, top_k: {top_k}")

        original_filename = file.filename
        safe_basename = os.path.basename(original_filename)
        if not safe_basename or safe_basename in [".", ".."] or safe_basename != original_filename: # Added original_filename check
            logger.error(f"Invalid image filename uploaded: {original_filename}")
            raise HTTPException(status_code=400, detail="Invalid image filename.")

        logger.info(f"Processing sanitized image filename: {safe_basename}")
        contents = await file.read()

        # File Type and Size Validation
        ALLOWED_IMAGE_CONTENT_TYPES = ["image/jpeg", "image/png"]
        MAX_IMAGE_SIZE_MB = 10
        MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

        if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            logger.error(f"Invalid image content type: {file.content_type} for file {safe_basename}")
            raise HTTPException(status_code=400, detail=f"Invalid image file type. Allowed: {', '.join(ALLOWED_IMAGE_CONTENT_TYPES)}")

        if len(contents) == 0:
            logger.error(f"Empty image file uploaded: {safe_basename}")
            raise HTTPException(status_code=400, detail="Empty image file.")

        if len(contents) > MAX_IMAGE_SIZE_BYTES:
            logger.error(f"Image file too large: {safe_basename}, size: {len(contents)} bytes. Max: {MAX_IMAGE_SIZE_BYTES} bytes.")
            raise HTTPException(status_code=413, detail=f"Image file too large. Max size: {MAX_IMAGE_SIZE_MB}MB.")

        # Save to local cache for embedding generation, using sanitized name
        local_image_path = f"{storage.cache}/{safe_basename}"
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
        logger.error(f"File not found during image search processing for {original_filename if 'original_filename' in locals() else file.filename}: {fnf_error}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(fnf_error)}")
    except HTTPException as http_exc: # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        logger.exception(f"Error searching by image {original_filename if 'original_filename' in locals() else file.filename}: {e}")
        # Clean up cached file if it exists and an error occurs mid-processing
        # Ensure local_image_path was defined
        if 'local_image_path' in locals() and os.path.exists(local_image_path):
            try:
                os.remove(local_image_path)
                logger.info(f"Cleaned up cached image due to error: {local_image_path}")
            except OSError as e_os:
                logger.error(f"Error cleaning up cached image {local_image_path} during error handling: {e_os}")
        elif 'safe_basename' in locals(): # Fallback if local_image_path wasn't formed
            local_image_path_on_error = f"{storage.cache}/{safe_basename}"
        if os.path.exists(local_image_path_on_error):
            try:
                os.remove(local_image_path_on_error)
                logger.info(f"Cleaned up cached image due to error: {local_image_path_on_error}")
            except OSError as e_os:
                logger.error(f"Error cleaning up cached image {local_image_path_on_error} during error handling: {e_os}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during image search: {str(e)}")

@app.get("/video/{filename}")
async def get_video(filename: str): # filename comes from path parameter
    """Streams a video from GCS or local cache."""
    try:
        # Sanitize filename for path traversal
        if os.path.basename(filename) != filename:
            logger.error(f"Invalid filename requested for streaming: {filename}. Contains path components.")
            raise HTTPException(status_code=400, detail="Invalid filename format.")

        logger.info(f"Requesting video: {filename}")
        vpath = VideoPath(filename) # VideoPath now gets a safe basename
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

