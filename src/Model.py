from abc import ABC, abstractmethod
from os import environ

TOKEN: str = environ["GITHUB_TOKEN"]
"""GitHub API Token."""

ENDPOINT: str = "https://models.inference.ai.azure.com"
"""Endpoint URL for the Azure Inference API."""

DEFAULT_IMAGE_FORMAT = "jpg"
"""Fallback image format to use if the image file extension is not recognized."""

DEFAULT_TEMPERATURE: float = 1.0

DEFAULT_TOP_P: float = 1.0

DEFAULT_MAX_TOKENS: int = 1000

class Model(ABC):
    def __init__(self, model_name: str, endpoint: str = ENDPOINT, token: str = TOKEN):
        super().__init__()

        self.model_name: str = model_name
        self.endpoint: str = endpoint
        self.token: str = token
 
        self.client = self._init_client(endpoint, token)

    @abstractmethod
    def _init_client(self, endpoint: str, token: str):
        raise NotImplementedError("Must override Model._init_client()")

    @abstractmethod
    def _response(self, messages: list, model_name: str, stream: bool = False, **kwargs) -> dict:
        raise NotImplementedError("Must override Model._response()")

    @abstractmethod
    def describe_image(self, img_path: str, detail: str):
        raise NotImplementedError("Must override Model.describe_image()")