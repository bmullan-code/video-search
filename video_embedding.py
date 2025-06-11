# from dotenv import load_dotenv # Removed
# import os # Removed
import vertexai
from vertexai.vision_models import MultiModalEmbeddingModel
from vertexai.vision_models import Video as VMVideo
from vertexai.vision_models import Image as VMImage
from vertexai.vision_models import VideoSegmentConfig
from moviepy import VideoFileClip
from storage_wrapper import storage
from video_path import VideoPath
from moviepy.editor import VideoFileClip
import logging
import config # Added config import

# load_dotenv() # Removed

# Configure logger for this module
logger = logging.getLogger(__name__)

class VideoEmbedding:

    # initialized with the vertexai project id and location and the id of the embedding model
    def __init__(
            self, 
            project = config.PROJECT_ID,
            location = config.LOCATION,
            model : str = config.MULTIMODAL_EMBEDDING_MODEL
    ):
        self.project = project  # Instance attribute
        self.location = location  # Instance attribute
        vertexai.init(project=self.project, location=self.location)
        self.mm_embedding_model = MultiModalEmbeddingModel.from_pretrained(model)

    # multimodal embedding model only processes 2 mins of video at a time, if longer than 2 mins 
    # need to generate multiple configs
    def get_video_segment_configs(self,length : int, interval = 120, interval_sec = 4):

        ranges = []
        start = 0
        while start < length:
            end = min(start + interval, length)  # Ensure end doesn't exceed total_length
            ranges.append(
                VideoSegmentConfig(
                    start_offset_sec=start,
                    end_offset_sec=end,
                    interval_sec=interval_sec
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

    # called by the client to create a video embedding for a full file 
    # regardless of length
    def get_video_embedding(self,video_path: VideoPath):

        len, fps, (width, height) = self.video_len(video_path.file_name())
        logger.info(f"Video length for {video_path.file_name()}: {len} seconds, FPS: {fps}, Dimensions: {width}x{height}")
        # can only process 120 seconds at a time, so have to split the calls.
        configs = self.get_video_segment_configs(int(len))
        # get the embeddings for each config
        embeddings = [ self.get_video_embedding_config(video_path,video_segment_config=config) for config in configs]
        # return flattened list
        return [ x for xs in embeddings for x in xs ]

    def get_video_embedding_with_cache(self, vpath: VideoPath, force_refresh: bool = False):
        """
        Gets video embeddings, using GCS as a cache.
        If embeddings exist in GCS and force_refresh is False, reads from GCS.
        Otherwise, generates new embeddings, saves them to GCS, and returns them.
        """
        cache_file_name = vpath.file_name_json()
        if not force_refresh and storage.exists(cache_file_name):
            logger.info(f"Reading video embeddings from GCS cache: {cache_file_name}")
            try:
                embeddings = storage.read_json(cache_file_name)
                return embeddings
            except Exception as e:
                logger.error(f"Failed to read embeddings from GCS cache {cache_file_name}: {e}. Will regenerate.")

        if force_refresh:
            logger.info(f"Force refresh requested for video embeddings: {vpath.file_name()}")
        else:
            logger.info(f"No cache found or error reading cache for video embeddings: {vpath.file_name()}. Generating new embeddings.")

        # Generate new embeddings using the existing method
        video_emb = self.get_video_embedding(vpath) # This internally uses self.mm_embedding_model

        if video_emb:
            logger.info(f"Successfully generated new video embeddings for: {vpath.file_name()}")
            try:
                storage.write_json(video_emb, cache_file_name)
                logger.info(f"Successfully wrote new video embeddings to GCS cache: {cache_file_name}")
            except Exception as e:
                logger.error(f"Failed to write video embeddings to GCS cache {cache_file_name}: {e}")
        else:
            logger.warning(f"Failed to generate video embeddings for: {vpath.file_name()}. Returning empty list.")
            return [] # Or raise an exception

        return video_emb

    # returns the video embedding for the specified config (start and end offsets)
    def get_video_embedding_config(self,
        video_path: VideoPath,
        dimension: int | None = 1408,
        video_segment_config: VideoSegmentConfig | None = None
    ) -> list[float]:
        logger.info(f"Processing video segment for {video_path.file_name()}: {str(video_segment_config)}")
        video = VMVideo.load_from_file(video_path.path())
        embedding = self.mm_embedding_model.get_embeddings(
            video=video,
            dimension=dimension,
            video_segment_config=video_segment_config
        )
        return [{"startOffsetSec": ve.start_offset_sec, "endOffsetSec": ve.end_offset_sec, "embedding": ve.embedding} for ve in embedding.video_embeddings]

    # returns a text embedding for the passed text
    def get_text_embedding(self, text: str = "banana muffins", dimension: int | None = 1408) -> list[float]:
        embedding = self.mm_embedding_model.get_embeddings(
            contextual_text=text,
            dimension=dimension
        )
        return embedding.text_embedding
    
    # returns an image embedding for the image at image_path
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
    
    # uses moviepy to get the length of a video
    # file must be local, so will be copied to storage cache directory
    def video_len(self,filename):
        # Ensure that storage.local_file is robust enough or handle potential errors here
        try:
            local_file_path = storage.local_file(filename)
            clip = VideoFileClip(local_file_path)
        except Exception as e:
            logger.error(f"Error processing video file {filename} with MoviePy: {e}")
            # Depending on desired behavior, re-raise or return default/error values
            raise # Re-raise the exception to be handled by the caller

        duration       = clip.duration
        fps            = clip.fps
        width, height  = clip.size
        return duration, fps, (width, height)
