from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from video_path import VideoPath
from video_embedding import VideoEmbedding
from vector_search_wrapper import VectorSearch
from video_search_results import VideoSearchResults
from storage_wrapper import storage  # Assuming you have a storage_wrapper module
from video_path import VideoPath
import json
import uvicorn

app = FastAPI(title="Video Search API")

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
vs = VectorSearch()

@app.post("/process_video/", status_code=201)
async def process_video_route(file: UploadFile = File(...)):
    """Processes a video file and adds its embeddings to Pinecone."""
    try:
        vpath = VideoPath(file.filename)  # Create VideoPath from filename
        contents = await file.read()
        # video_emb = ve.get_video_embedding(vpath=vpath)  # Get embeddings
        with open(f"{storage.cache}/{vpath.file_name()}","wb") as f:
            f.write(contents)
        video_emb = ve.get_video_embedding(vpath=vpath)  # Get embeddings


        records = [
            {
                "id": f"{vpath.file_name()}:{ve['startOffsetSec']}:{ve['endOffsetSec']}",
                "values": ve["embedding"],
                "metadata": {
                    "startOffsetSec": ve["startOffsetSec"],
                    "endOffsetSec": ve["endOffsetSec"],
                    "videoPath": vpath.path(),  # Store GCS path
                    "fileName": vpath.file_name(),
                },
            }
            for ve in video_emb
        ]
        pc.insert(records=records, namespace="video")

        storage.write_json(video_emb, vpath.file_name_json()) # Store embedding in GCS

        return {"message": f"Video {file.filename} processed and embeddings added to Pinecone."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {e}")



@app.get("/search_by_text/")
async def search_by_text(text: str, top_k: int = 10):
    """Searches for videos by text query."""
    try:
        text_emb = ve.get_text_embedding(text=text)
        results = vs.query(vector=text_emb, top_k=top_k)
        vsr = VideoSearchResults(results)
        return vsr.get_results()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching by text: {e}")

@app.post("/search_by_image/")
async def search_by_image(file: UploadFile = File(...), top_k: int = 10):
    try:
        image_path = VideoPath(file.filename).path()
        contents = await file.read()
        with open(f"{storage.cache}/{file.filename}", "wb") as f:
            f.write(contents)

        image_emb = ve.get_image_embedding(image_path=f"{storage.cache}/{file.filename}")
        results = vs.query(image_emb,top_k=top_k)
        vsr = VideoSearchResults(results)
        return vsr.get_results()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching by image: {e}")



@app.get("/video/{filename}") # updated route to handle full GCS URI
async def get_video(filename: str):
    """Streams a video from GCS."""

    vpath = VideoPath(filename)
    try:
        # get the file from cache if available
        local_path = storage.local_file(vpath.file_name())
        print(f"streaming video from {local_path}")


        def iterfile():  # Generator to stream the video
            with open(local_path, mode="rb") as file_like:
                yield from file_like

        return StreamingResponse(iterfile(), media_type="video/mp4") # Set appropriate media type

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error getting video: {e}")


# uvicorn service:app --reload

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

