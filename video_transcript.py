# creates a video transcript

from moviepy.editor import VideoFileClip
from gemini_wrapper import gemini
from pydantic import BaseModel
from video_path import VideoPath
from gemini_wrapper import gemini
from storage_wrapper import storage
import json,os

class TranscriptEntry(BaseModel):
    time_start : int
    time_end : int
    speaker : str
    transcript : str

class Transcript(BaseModel):
    transcript : list[TranscriptEntry]

class VideoTranscript:

    def __init__(self, file_name : str):
        self.vpath = VideoPath(file_name=file_name)
        self.data = None

    # def __init__(self, video_path : VideoPath):
    #     self.path = video_path
    #     self.data = None

    def json_obj(self):
        return self.data

    def json_str(self):
        return json.dumps(self.data)

    # video = VideoPath(file_name="shannon.mp4")
    def create(self):
        # create the transcript by prompting gemini
        transcript = gemini.typed_content_video(path=self.vpath.path(),
            prompt="Create a full transcript of this video",
            response_type=Transcript
        )
        # convert to json object
        self.data = transcript.model_dump(mode="python")
        # write to gcs storage
        # print(transcript.model_dump(mode="json"))
        storage.write_json(self.data, self.path.file_name_transcript())

    def chunks(self):
        if self.data is None:
            raise Exception("data not set")
        
        for te in self.data.transcript:
            print(te.transcript)

    def split_video_into_segments(self, input_file,output_dir = "", segment_length=240):
        """Splits a video into segments of a specified length.

        Args:
            input_path: Path to the input video file.
            output_dir: Directory to save the output segments.
            segment_length: Length of each segment in seconds (default: 240 seconds = 4 minutes).
        """
        try:
            clip = VideoFileClip(input_file)
            total_duration = clip.duration

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            base_name, ext = os.path.splitext(os.path.basename(input_file))
            segment_index = 1
            start_time = 0
            output_paths = []

            while start_time < total_duration:
                end_time = min(start_time + segment_length, total_duration)
                segment = clip.subclip(start_time, end_time)
                output_path = os.path.join(output_dir, f"{base_name}_segment_{segment_index}{ext}")
                output_paths.append(output_path)
                segment.write_videofile(output_path)
                segment_index += 1
                start_time = end_time

            clip.close()
            print(f"Video '{input_file}' split into segments in '{output_dir}'.")
            return output_paths

        except Exception as e:
            print(f"Error splitting video: {e}")

    # # Example Usage (replace with your paths):
    # input_video_path = "/path/to/your/video.mp4"
    # output_directory = "/path/to/output/directory"
    # split_video_into_segments(input_video_path, output_directory)


vt = VideoTranscript(".cache/sundar.mp4")

clips = vt.split_video_into_segments(
    input_file=".cache/sundar.mp4",
    output_dir=".clips", 
    segment_length=120
)

print(clips)
# vt.create()
# vt.chunks()



