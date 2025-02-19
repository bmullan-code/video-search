# creates a video transcript

from gemini_wrapper import gemini
from pydantic import BaseModel
from video_path import VideoPath
from gemini_wrapper import gemini
from storage_wrapper import storage
import json

class TranscriptEntry(BaseModel):
    time_start : int
    time_end : int
    speaker : str
    transcript : str

class Transcript(BaseModel):
    transcript : list[TranscriptEntry]

class VideoTranscript:

    def __init__(self, file_name : str):
        self.path = VideoPath(file_name=file_name)
        self.data = None

    def __init__(self, video_path : VideoPath):
        self.path = video_path
        self.data = None

    def json_obj(self):
        return self.data

    def json_str(self):
        return json.dumps(self.data)

    # video = VideoPath(file_name="shannon.mp4")
    def create(self):
        # create the transcript by prompting gemini
        transcript = gemini.typed_content_video(video.path(),
            prompt="Create a full transcript of this video",
            response_type=Transcript
        )
        # convert to json object
        self.data = transcript.model_dump(mode="python")
        # write to gcs storage
        # print(transcript.model_dump(mode="json"))
        storage.write_json(self.data, self.path.file_name_transcript())
