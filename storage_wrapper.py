# A wrapper around the google cloud storage api

from dotenv import load_dotenv
from google.cloud import storage
import json
import os

load_dotenv()

class Storage:

    # initialized with a project id, location and bucketname. Assumes an instance per 
    # bucket managed. 
    # certain operations will store copies of the gcs blob in the .cache directory
    # does not support paths in the bucket (ie. files are read and written to top level
    # bucket location)
    def __init__(self, 
        project = os.environ["PROJECT_ID"], 
        location = os.environ["LOCATION"], 
        bucket_name = os.environ["BUCKET_NAME"], 
        cache = ".cache"):

        self.bucket_name = bucket_name
        self.project = project 
        self.location = location 
        self.client = storage.Client(project=self.project)
        self.bucket = self.client.bucket(self.bucket_name)
        # create the cache dir if it does not exist
        if not os.path.isdir(cache):
            os.mkdir(cache)
        self.cache = cache

    # write a python object to the bucket, assumes it is serializable as a json object
    # used for storing the embedding back to gcs (may be reused)
    def write_json(self, json_data, file_name):
        # print(f"writing to {file_name}")
        try:
            blob = self.bucket.blob(file_name)
            blob.upload_from_string(
                data=json.dumps(json_data), 
                content_type='application/json')
            print(f"JSON data written to {file_name} in bucket {self.bucket_name}")
        except Exception as e:
            print(f"Error writing JSON to GCS: {e}")

    # reads a json file from gcs location. 
    def read_json(self, file_name):
        blob = self.bucket.blob(file_name)
        blob_contents = blob.download_as_string()
        emb_json = json.loads(blob_contents)
        return emb_json
    
    # returns true if specified file name exists in bucket
    def exists(self, file_name):
        blob = self.bucket.blob(file_name)
        return blob.exists()
    
    # copies a storage blob to a local file in the cache (or returns it if it already exists)
    def local_file(self, file_name):
        destination_file_name = f"{self.cache}/{file_name}"
        if os.path.isfile(destination_file_name):
            return destination_file_name
        else:
            blob = self.bucket.blob(file_name)
            destination_file_name = f"{self.cache}/{file_name}"
            blob.download_to_filename(destination_file_name)
            return destination_file_name

storage = Storage()

