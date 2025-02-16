from video_path import VideoPath
from video_embedding import VideoEmbedding
from pinecone_wrapper import PineconeWrapper
from vector_search_wrapper import VectorSearch
from storage_wrapper import storage
from video_search_results import VideoSearchResults
import json
     
ve = VideoEmbedding()
# pc = PineconeWrapper()
vs = VectorSearch()


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

# def process_video(vpath: VideoPath):
#     video_emb = get_or_create_video_embedding(vpath=vpath)

#     print("length of embedding: ", len(video_emb))
#     print("length of embedding: ", len(video_emb[0]["embedding"]))
#     print("First five values of the first segment are: ", video_emb[0]["embedding"][:5])

#     records = [
#         { 
#             "id" : f"{vpath.file_name()}:{ve['startOffsetSec']}:{ve['endOffsetSec']}",
#             "values" : ve["embedding"],
#             "metadata" : {
#                 "startOffsetSec" : ve["startOffsetSec"],
#                 "endOffsetSec" : ve["endOffsetSec"],
#                 "videoPath" : vpath.path(),
#                 "publicUrl" : vpath.public_url(),
#                 "fileName" : vpath.file_name()
#             }
#         }
#         for ve in video_emb
#     ]
#     vs.insert(records=records,vpath)

def insert_video_to_vector_search(vpath: VideoPath):
    video_emb = get_or_create_video_embedding(vpath=vpath)
    vs.insert(embeddings=video_emb,vpath=vpath)

# insert_video_to_vector_search(vpath=VideoPath("Wildlife.mp4"))
# insert_video_to_vector_search(vpath=VideoPath("sundar.mp4"))
# insert_video_to_vector_search(vpath=VideoPath("shannon.mp4"))

text_emb = ve.get_text_embedding(text="road")
results = vs.query(vector=text_emb,top_k=10)
for r in results:
    print(r)

vsr = VideoSearchResults(results)
[ print(vsr) for vsr in vsr.get_results() ]




# process_video(vpath=VideoPath("sundar.mp4"))

# text_emb = ve.get_text_embedding(text="dog")
# results = pc.query(vector=text_emb,namespace="video",top_k=10)
# for r in results.matches:
#     print(r["id"],"\t",r["score"])

# image_emb = ve.get_image_embedding(image_path=VideoPath("sundar.webp").path())
# results = pc.query(vector=image_emb,namespace="video",top_k=10)
# for r in results.matches:
#     print(r["id"],"\t",r["score"])

# image_emb = ve.get_image_embedding(image_path=VideoPath("gannet.jpg").path())

# results = pc.query(vector=image_emb,namespace="video")

# print(
#     [
#         {r["id"], r["score"]} for r in results.matches
#     ]
# )   
