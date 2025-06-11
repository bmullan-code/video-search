# A wrapper around the google cloud storage api

# from dotenv import load_dotenv # Removed
from google.cloud import storage
import json
import os
import logging
import config # Added config import

# load_dotenv() # Removed

logger = logging.getLogger(__name__)

class Storage:

    # initialized with a project id, location and bucketname. Assumes an instance per 
    # bucket managed. 
    # certain operations will store copies of the gcs blob in the .cache directory
    # does not support paths in the bucket (ie. files are read and written to top level
    # bucket location)
    def __init__(self, 
        project = config.PROJECT_ID,
        location = config.LOCATION,
        bucket_name = config.BUCKET_NAME,
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
            logger.info(f"JSON data written to {file_name} in bucket {self.bucket_name}")
        except Exception as e:
            logger.error(f"Error writing JSON to GCS for file {file_name}: {e}")
            raise # Re-raise the exception to allow caller to handle

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

    # lists all files in the bucket, optionally filtering by extension
    def list_files(self, extension=None):
        """Lists all files in the GCS bucket.

        Args:
            extension (str, optional): If provided, filters files by this
                                       extension (e.g., ".mp4").
                                       Defaults to None (no filtering).

        Returns:
            list: A list of filenames. Returns an empty list if an error occurs.
        """
        try:
            blobs = self.bucket.list_blobs()
            file_names = [blob.name for blob in blobs]

            if extension:
                file_names = [
                    name for name in file_names if name.endswith(extension)
                ]

            return file_names
        except Exception as e:
            logger.error(f"Error listing files in GCS: {e}")
            return []

    # uploads a local file to the bucket
    def upload_file(self, local_file_path: str, destination_blob_name: str):
        """Uploads a local file to the GCS bucket.

        Args:
            local_file_path (str): Path to the local file to upload.
            destination_blob_name (str): The name for the blob in GCS.
        """
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(local_file_path)
            logger.info(f"File {local_file_path} uploaded to {destination_blob_name} in bucket {self.bucket_name}.")
        except FileNotFoundError:
            logger.error(f"Local file not found for upload: {local_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error uploading file {local_file_path} to GCS as {destination_blob_name}: {e}")
            raise # Re-raise the exception

storage = Storage()

