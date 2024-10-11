# Meta Llama 3.2 (90B) Vision Instructions
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (AssistantMessage, ImageContentItem, ImageDetailLevel,
                                       ImageUrl, SystemMessage, TextContentItem, UserMessage)
from azure.core.credentials import AzureKeyCredential
from src.Model import Model, TOKEN, ENDPOINT, DEFAULT_IMAGE_FORMAT, DEFAULT_TEMPERATURE, DEFAULT_TOP_P, DEFAULT_MAX_TOKENS
from os.path import splitext

MODEL_NAME = "Llama-3.2-90B-Vision-Instruct"

DEFAULT_IMAGE_DETAIL = ImageDetailLevel.LOW

class Llama3_2(Model):
    def __init__(self, endpoint: str = ENDPOINT, token: str = TOKEN):
        super().__init__(model_name = MODEL_NAME, endpoint = endpoint, token = token)

    def _init_client(self, endpoint: str, token: str):
        return ChatCompletionsClient(
            endpoint = endpoint,
            credential = AzureKeyCredential(token),
        )

    def _response(self, messages: list, temperature: float = DEFAULT_TEMPERATURE, top_p: float = DEFAULT_TOP_P, max_tokens: int = DEFAULT_MAX_TOKENS, **kwargs):
        return self.client.complete(messages = messages,
                                    model = self.model_name,
                                    stream = True,
                                    temperature = temperature,
                                    top_p = top_p,
                                    max_tokens = max_tokens,
                                    **kwargs)

    # messages = [
    #     SystemMessage(content="You are a helpful assistant."),
    #     UserMessage(content="What is the capital of France?"),
    #     AssistantMessage(content="The capital of France is Paris."),
    #     UserMessage(content="What about Spain?"),
    # ]

    def describe_image(self, img_path: str, detail: ImageDetailLevel = DEFAULT_IMAGE_DETAIL):
        img_format = splitext(img_path)[1]

        response = self._response(
            messages = [
                SystemMessage(content = "You are a helpful assistant that describes images in detail."),
                UserMessage(content = [
                    TextContentItem(text = "What's in this image? Respond in bullet points and organize the content in a logical manner."),
                        ImageContentItem(
                            image_url = ImageUrl.load(image_file = img_path,
                                                      image_format = img_format[1:] if img_format else DEFAULT_IMAGE_FORMAT, # [1:] removes leading dot from extension
                                                      detail = detail
                            )
                        )
                    ]
                )
            ]
        )
        
        for update in response:
            if update.choices:
                print(update.choices[0].delta.content or "", end = "")

if __name__ == "__main__":
    model = Llama3_2()
    model.describe_image("sample.jpg")
    print()

    # model.close()