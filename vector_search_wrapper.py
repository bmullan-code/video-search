# provides a basic wrapper around vertex ai vector search. 

from dotenv import load_dotenv
import os
from google.cloud import aiplatform
from storage_wrapper import storage
from video_path import VideoPath

load_dotenv()

class VectorSearch:

    # initialize with 3 values from the vector search index and index endpoint. 
    # these values can be looked up in the vector search console in vertexai
    # eg. 
    # VECTOR_SEARCH_INDEX="projects/173481798756/locations/us-central1/indexes/7718532044568920064"
    # DEPLOYED_INDEX_ID="quickstart1_1739716044566"
    # INDEX_ENDPOINT_ID = "1756364272255893504"

    def __init__(self, 
                project = os.environ["PROJECT_ID"], 
                location = os.environ["LOCATION"], 
                index = os.environ["VECTOR_SEARCH_INDEX"],
                index_endpoint_id = os.environ["INDEX_ENDPOINT_ID"],
                deployed_index_id = os.environ["DEPLOYED_INDEX_ID"]
        ):
            self.project = project  # Instance attribute
            self.location = location  # Instance attribute
            aiplatform.init(project=self.project, location=self.location)
            self.index = aiplatform.MatchingEngineIndex(index_name=index)
            self.index_endpoint_id = index_endpoint_id
            self.index_endpoint = aiplatform.MatchingEngineIndexEndpoint(self.index_endpoint_id)
            self.deployed_index_id = deployed_index_id

    # converte the embeddings from MultiModalEmbeddings model output to vector search format
    def convertEmbeddings(self, embeddings, vpath: VideoPath):
        records = [
            { 
                "datapoint_id" : f"{vpath.file_name()}:{ve['startOffsetSec']}:{ve['endOffsetSec']}",
                "feature_vector" : ve["embedding"]
            }
            for ve in embeddings
        ]
        return records

    # insert embeddings in vertexai multimodal embedding model format 
    def insert(self, embeddings,vpath: VideoPath):
        # convert to vector search format
        datapoints = self.convertEmbeddings(embeddings,vpath)
        # insert at most 1000 at a time
        for i in range(0, len(datapoints), 1000):
            # https://cloud.google.com/vertex-ai/docs/reference/rest/v1/projects.locations.indexes/upsertDatapoints
            result = self.index.upsert_datapoints(datapoints=datapoints[i : i + 1000])
            print(result)


    # does a nearest neighbor search based on the passed vector. 
    # the vector could have come from the text or image embedding model     
    def query(self, vector, top_k=3):

        results = self.index_endpoint.find_neighbors(
            deployed_index_id=self.deployed_index_id,
            queries=[vector],
            num_neighbors=top_k,
        )
        return [
            {
                "id": neighbor.id,
                "distance": neighbor.distance
            }
            for idx, neighbor in enumerate(results[0])
        ]

vs = VectorSearch()