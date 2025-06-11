# abstraction around the google genai api for calling gemini
from google import genai
from google.genai.types import Part, GenerateContentConfig,Candidate
from pydantic import BaseModel
# from dotenv import load_dotenv # Removed
# import os,time,json # os Removed, time and json kept if needed elsewhere, but seems not for this snippet
import time, json # Assuming time and json might be used elsewhere, if not, they can be removed too.
import config # Added config import
import logging # Added logging

# load_dotenv() # Removed

logger = logging.getLogger(__name__) # Added logger

class Gemini:

    # initialized with the project id, location and gemini model id
    def __init__(
        self, 
        project = config.PROJECT_ID,
        location = config.LOCATION,
        model_id = config.GEMINI_MODEL_ID
    ):
        logger.info(f"Initializing Gemini with project: {project}, location: {location}, model_id: {model_id}")
        self.client = genai.Client(vertexai=True, project=project, location=location)
        self.model_id = model_id
        logger.info(
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

        logger.info(f"Requesting typed content for video: {path} with prompt: '{prompt}'")
        
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
            # logger.debug(f"Gemini raw response: {response}") # Be careful with logging full response
            
            # The file writing part seems like debugging code, should be removed or properly handled.
            # For now, I'll comment it out as it's not typical for a wrapper like this.
            # with open("gemini_response.json", 'w') as file:
            #     for c in response.candidates:
            #         logger.debug(f"Candidate: index={c.index}, finishReason={c.finishReason}, finishMessage={c.finishMessage}")
            #         # file.write(str(c.index)+"\n"+str(c.finishReason)+"\n"+str(c.finishMessage)+"\n") # Original had issues
            #         # ct = c.content # ct was unused
            #         # file.write(str(c)) # This would write the object representation, not ideal for JSON
            #     # json.dump(response, file, indent=4) # This would fail as response is not directly serializable

            if response.parsed is None:
                logger.warning(f"Gemini response.parsed is None for video {path}.")
                # Log more details from the response if available and helpful
                for candidate in response.candidates:
                    logger.warning(f"Candidate details: Index: {candidate.index}, Finish Reason: {candidate.finish_reason}, Finish Message: {candidate.finish_message}")
                    if candidate.content:
                         logger.warning(f"Candidate content parts: {candidate.content.parts}")


            return response.parsed
        except Exception as e:
            logger.exception(f"Error calling Gemini for video {path}: {e}")
            return None


gemini = Gemini()