from video_path import VideoPath
from video_embedding import VideoEmbedding
from pinecone_wrapper import PineconeWrapper
from vector_search_wrapper import VectorSearch
from storage_wrapper import storage
from video_search_results import VideoSearchResults
import json
from chromadb_wrapper import cdb
from vector_search_wrapper import vs
from video_transcript import VideoTranscript
from dotenv import load_dotenv

load_dotenv()
     
vector_store = vs if (os.environ["VECTOR_STORE"] == "VECTOR_SEARCH") else cdb
ve = VideoEmbedding()

def get_or_create_video_embedding(vpath: VideoPath):

    if storage.exists(vpath.file_name_json()):
        print(f"reading from gcs:{vpath.file_name_json()}")
        emb_json = storage.read_json(vpath.file_name_json())
        return emb_json
    else:
        print("creating embedding")
        video_emb = ve.get_video_embedding(vpath)
        storage.write_json(video_emb, vpath.file_name_json())
        return video_emb

def process_video(vpath: VideoPath):
    print(f"processing:{vpath.path()}")
    video_emb = get_or_create_video_embedding(vpath=vpath)
    vector_store.insert(embeddings=video_emb)
    # create transcript (using gemini)
    video_transcript = VideoTranscript(video_path=vpath).create()

    # todo - rag based on transcript (chunk into ~30 second blocks) (filter to select transcript search)
    # todo - hybrid search based on transcript (get all transcript segments around a segment (min 4 sec) and store with video embeddings)
    # todo - frame metadata extraction using gemini (store metadata with embeddings ?) filter based on meta data
    # todo - add meta data based on image search in frame eg. a particular person, object, brand etc. 

videos = ["Wildlife.mp4","sundar.mp4","shannon.mpr"]

if __name__ == "__main__":
    for video in videos:
        video_path = VideoPath(video)
        process_video(video_path)