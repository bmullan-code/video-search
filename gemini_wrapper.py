# abstraction around the google genai api for calling gemini
from google import genai
from google.genai.types import Part, GenerateContentConfig
from pydantic import BaseModel
from dotenv import load_dotenv
import os,time


load_dotenv()

class Gemini:

    # initialized with the project id, location and gemini model id
    def __init__(
        self, 
        project = os.environ["PROJECT_ID"], 
        location = os.environ["LOCATION"], 
        model_id = os.environ["GEMINI_MODEL_ID"] 
    ):
        self.client = genai.Client(vertexai=True, project=project, location=location)
        self.model_id = model_id

    # this method prompts gemini with a video part referencing an mp4 file in a gcs storage 
    # location. It expects to return a pydantic BaseModel type which must be passed in 
    # response_type (see pydantic docs for examples of how to create these)
    def typed_content_video(self, 
        path : str, 
        prompt : str = "", 
        system_instructions : str = "", 
        response_type = None):

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=[
                Part.from_uri(
                    file_uri = path,
                    mime_type="video/mp4"
                ),
                prompt
            ],
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_type,
            ),
            # Optional: Use the `media_resolution` parameter to specify the resolution of the input media.
            # config=GenerateContentConfig(
            #     media_resolution=MediaResolution.MEDIA_RESOLUTION_LOW,
            # ),
        )
        return response.parsed

gemini = Gemini()