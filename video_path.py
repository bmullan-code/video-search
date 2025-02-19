# an abstract type the represents a path to a gcs object which can also return its file name portion 
# and json filename
from dotenv import load_dotenv
from google.cloud import storage
import os

load_dotenv()

class VideoPath:

    # f"gs://{BUCKET_NAME}/{video_file}"
    def __init__(self, path):
        self.gcs_path = path

    # "Wildlife.mp4"
    def __init__(self, file_name :str, bucket_name :str = os.environ["BUCKET_NAME"]):
        self.gcs_path = f"gs://{bucket_name}/{file_name}"
        print(self.gcs_path)

    # returns full gcs uri path
    def path(self):
        return self.gcs_path

    # returns just the filename portion
    def file_name(self):
        return self.path().split("/")[-1]
    
    # returns just the bucket name portion
    def bucket_name(self):
        return self.path().split("/")[2]

    # returns the file name portion but with a json extension
    def file_name_json(self):
        # return self.file_name().replace(".mp4", ".json")
        try:
            base, _ = os.path.splitext(self.file_name()) 
            return f"{base}.json"
        except TypeError:  # Handle cases where file_path is not a string or Path
            return None

    def file_name_transcript(self):
        # return self.file_name().replace(".mp4", ".json")
        try:
            base, _ = os.path.splitext(self.file_name()) 
            return f"{base}.transcript"
        except TypeError:  # Handle cases where file_path is not a string or Path
            return None

    # returns the gcs storage public url for a gs path 
    # eg. https://storage.googleapis.com/mullan-videos/Wildlife.mp4
    def public_url(self):
        return f"https://storage.googleapis.com/{self.bucket_name()}/{self.file_name()}"


if __name__ == "__main__":
    video_path = VideoPath("Wildlife.mp4")
    print(video_path.file_name())
    print(video_path.file_name_json())
    print(video_path.path())
