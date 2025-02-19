import chromadb
from chromadb.config import Settings
from video_path import VideoPath
from dotenv import load_dotenv
import os

load_dotenv()

class ChromaDB:

    def __init__(self, collection_name = os.environ["CHROMADB_COLLECTION_NAME"]):
        self.client = chromadb.PersistentClient(path=".chromadb")
        self.collection = self.client.get_or_create_collection(name=collection_name)

    # converte the embeddings from MultiModalEmbeddings model output to vector search format
    def convertEmbeddings(self, embeddings, vpath: VideoPath):

        ids = [
            f"{vpath.file_name()}:{ve['startOffsetSec']}:{ve['endOffsetSec']}"
            for ve in embeddings
        ] 
        vectors = [
            ve["embedding"] for ve in embeddings
        ]
        return (ids,vectors)

    def insert(self, embeddings,vpath: VideoPath):
        (ids,vectors) = self.convertEmbeddings(embeddings,vpath)
        res = self.collection.add(embeddings=vectors, ids=ids)
     
    def query(self, vector, top_k=3):

        results = self.collection.query(
            query_embeddings=[vector],
            n_results=top_k,
            # where={"metadata_field": "is_equal_to_this"},
            # where_document={"$contains":"search_string"}
        )

        # convert results into standard format for front end.
        zipped = zip(results["ids"][0],results["distances"][0])
        return [{"id":id,"distance":distance} for (id,distance) in zipped]        

cdb = ChromaDB()

