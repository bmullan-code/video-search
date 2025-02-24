# abstraction around the google genai api for calling gemini
from google import genai
from google.genai.types import Part, GenerateContentConfig,Candidate
from pydantic import BaseModel
from dotenv import load_dotenv
import os,time,json


load_dotenv()

class Gemini:

    # initialized with the project id, location and gemini model id
    def __init__(
        self, 
        project = os.environ["PROJECT_ID"], 
        location = os.environ["LOCATION"], 
        model_id = os.environ["GEMINI_MODEL_ID"] 
    ):
        print("project",project)
        self.client = genai.Client(vertexai=True, project=project, location=location)
        self.model_id = model_id
        print(
        f"Using Vertex AI with project: {self.client._api_client.project} in location: {self.client._api_client.location}"
    )

    # this method prompts gemini with a video part referencing an mp4 file in a gcs storage 
    # location. It expects to return a pydantic BaseModel type which must be passed in 
    # response_type (see pydantic docs for examples of how to create these)
    def typed_content_video(self, 
        path : str, 
        prompt : str = "", 
        system_instructions : str = "", 
        response_type = None):

        print("path",path)
        
        try:
            # see https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1/GenerateContentResponse
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
            # print("response",(response))
            
            with open("gemini_response.json", 'w') as file:
                for c in response.candidates:
                    # print(f"candidate: {c.content}")
                    file.write(c.index,"\n",c.finishReason,"\n",c.finishMessage,"\n")
                    ct = c.content
                    file.write(c)
                # json.dump(response, file, indent=4)

            return response.parsed
        except Exception as e:
            print(e)
            return None


gemini = Gemini()