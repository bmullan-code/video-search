# converts a vector search results into a useable set of 
# of video search results (filename, public path, time offsets etc.)

from video_path import VideoPath

class VideoSearchResults:

    def __init__(self, vector_search_results = []):

        self.vector_search_results = vector_search_results

        # input : {'id': 'Wildlife.mp4:0.0:4.0', 'distance': 0.09969311952590942}
        # output :  {"publicUrl":","startOffsetSec":"endOffsetSec":"","score":""}

        self.results = []
        for vsr in self.vector_search_results:
            (filename,start,end) = tuple(filter(None,vsr["id"].split(":")))
            self.results.append(
                { 
                    "publicUrl":VideoPath(filename).public_url(),
                    "startOffsetSec":int(float(start)),
                    "endOffsetSec":int(float(end)),
                    "score":vsr["distance"]
                }
            )

    def get_results(self):
        return self.results
