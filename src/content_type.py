import dataclasses
import mimetypes

import requests


@dataclasses.dataclass
class ContentType:
    mime_type: str

    def is_javascript(self):
        return "javascript" in self.mime_type


class ContentTypeFinder:
    @staticmethod
    def find_type_for(response: requests.Response) -> ContentType:
        return ContentType(
            response.headers.get('content-type', mimetypes.guess_type(response.url)[0])
        )
