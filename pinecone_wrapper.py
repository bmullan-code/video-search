# A wrapper around the pinecone api

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
import os,time

class PineconeWrapper:

    def __init__(self, index_name = os.environ["PINECONE_INDEX_NAME"], api_key = os.environ["PINECONE_API_KEY"]):

        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name

        if not self.pc.has_index(index_name):
            print(f"creating index {index_name}")
            self.index = self.pc.create_index(
                name=index_name,
                dimension=1408, # Replace with your model dimensions
                metric="cosine", # Replace with your model metric
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1") 
            )
            while not self.pc.describe_index(index_name).status['ready']:
                time.sleep(1)
        else:
            self.index = self.pc.Index(self.index_name)
        print(self.index_name)

    def get_index(self):
        return self.index
    
    def insert(self, records, namespace=None):
        self.index.upsert(vectors=records,namespace=namespace)
        time.sleep(10)  # Wait for the upserted vectors to be indexed
        print(self.index.describe_index_stats())

    def query(self,vector,namespace=None,top_k=3):
        results = self.index.query(
            namespace=namespace,
            vector=vector,
            top_k=top_k,
            include_values=False,
            include_metadata=True
        )
        return results