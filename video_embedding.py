
from dotenv import load_dotenv
import os
import vertexai
from vertexai.vision_models import MultiModalEmbeddingModel
from vertexai.vision_models import Video as VMVideo
from vertexai.vision_models import Image as VMImage
from vertexai.vision_models import VideoSegmentConfig
from moviepy import VideoFileClip
from storage_wrapper import storage
from video_path import VideoPath

load_dotenv()

class VideoEmbedding:

    def __init__(self, project = os.environ["PROJECT_ID"], location = os.environ["LOCATION"]):
        self.project = project  # Instance attribute
        self.location = location  # Instance attribute
        vertexai.init(project=self.project, location=self.location)
        self.mm_embedding_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
        # self.video_segment_config = VideoSegmentConfig( 
        #     start_offset_sec = 0, end_offset_sec = 1630, interval_sec = 4
        # )

    def get_video_segment_configs(self,length : int, interval = 120, interval_sec = 4):

        ranges = []
        start = 0
        while start < length:
            end = min(start + interval, length)  # Ensure end doesn't exceed total_length
            ranges.append(
                VideoSegmentConfig( 
                    start_offset_sec = start, end_offset_sec = end, interval_sec = interval_sec
                )
            )
            start = end
        return ranges

    #  "videoEmbeddings": [
    #         {
    #           "startOffsetSec": integer,
    #           "endOffsetSec": integer,
    #           "embedding": [
    #             float,
    #             // array of 1408 float values
    #             float
    #           ]
    #         }

    def get_video_embedding(self,video_path: VideoPath):

        len, fps, (width, height) = self.video_len(video_path.file_name())
        print(f"video len in seconds: {len})")

        # can only process 120 seconds at a time, so have to split the calls.
        configs = self.get_video_segment_configs(int(len))
        # get the embeddings for each config
        embeddings = [ self.get_video_embedding2(video_path,video_segment_config=config) for config in configs]
        # return flattened list
        return [ x for xs in embeddings for x in xs ]

    def get_video_embedding2(self,
        video_path: VideoPath,
        dimension: int | None = 1408,
        video_segment_config: VideoSegmentConfig | None = None
    ) -> list[float]:
        print(f"processing {str(video_segment_config)}")
        video = VMVideo.load_from_file(video_path.path())
        embedding = self.mm_embedding_model.get_embeddings(
            video=video,
            dimension=dimension,
            video_segment_config=video_segment_config
        )
        return [{"startOffsetSec": ve.start_offset_sec, "endOffsetSec": ve.end_offset_sec, "embedding": ve.embedding} for ve in embedding.video_embeddings]

    def get_text_embedding(self, text: str = "banana muffins", dimension: int | None = 1408) -> list[float]:
        embedding = self.mm_embedding_model.get_embeddings(
            contextual_text=text,
            dimension=dimension
        )
        return embedding.text_embedding
    
    def get_image_embedding( self,
        image_path: str = None,
        dimension: int | None = 1408,
    ) -> list[float]:
        image = VMImage.load_from_file(image_path)
        embedding = self.mm_embedding_model.get_embeddings(
            image=image,
            dimension=dimension,
        )
        return embedding.image_embedding
    
    def video_len(self,filename):
        clip = VideoFileClip(storage.local_file(filename))
        duration       = clip.duration
        fps            = clip.fps
        width, height  = clip.size
        return duration, fps, (width, height)