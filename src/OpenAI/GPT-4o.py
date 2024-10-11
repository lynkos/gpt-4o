# OpenAI GPT-4o API example
from base64 import b64encode
from json import dumps, loads
from src.Model import Model, TOKEN, ENDPOINT, DEFAULT_IMAGE_FORMAT, DEFAULT_TEMPERATURE, DEFAULT_TOP_P, DEFAULT_MAX_TOKENS
from openai import OpenAI
from os.path import splitext

MODEL_NAME = "gpt-4o"

DEFAULT_IMAGE_DETAIL = "low"

class GPT4o(Model):
    def __init__(self, endpoint: str = ENDPOINT, token: str = TOKEN):
        super().__init__(model_name = MODEL_NAME, endpoint = endpoint, token = token)

    def _init_client(self, endpoint: str, token: str):
        return OpenAI(base_url = endpoint, api_key = token)

    def _response(self, messages: list, temperature: float = DEFAULT_TEMPERATURE, top_p: float = DEFAULT_TOP_P, max_tokens: int = DEFAULT_MAX_TOKENS, **kwargs):
        return self.client.chat.completions.create(messages = messages,
                                                   model = self.model_name,
                                                   stream = True,
                                                   temperature = temperature,
                                                   top_p = top_p,
                                                   max_tokens = max_tokens,
                                                   **kwargs)

    def _get_img_data_url(self, img_path: str) -> str:
        """
        Helper function to converts an image file to a data URL string.

        Args:
            img_path (str): The path to the image file.

        Returns:
            str: The data URL of the image.
        """
        img_format = splitext(img_path)[1]

        try:
            with open(img_path, "rb") as image:
                image_data = b64encode(image.read()).decode("utf-8")

        except FileNotFoundError:
            print(f"Could not read '{img_path}'.")
            exit(1)

        # [1:] removes leading dot from extension
        return f"data:image/{img_format[1:] if img_format else DEFAULT_IMAGE_FORMAT};base64,{image_data}"

    def describe_image(self, img_path: str, detail: str = DEFAULT_IMAGE_DETAIL):
        response = self._response(
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that describes images in details.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "What's in this image?",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": self._get_img_data_url(img_path),
                                "detail": detail
                            }
                        }
                    ]
                }
            ]
        )

        for update in response:
            if update.choices[0].delta.content:
                print(update.choices[0].delta.content, end = "")


if __name__ == "__main__":
    model = GPT4o()
    model.describe_image("sample.jpg")
    print()
    
exit(0)
    # MULTI-TURN + STREAMED OUTPUT EXAMPLE
    # response = (
    #     messages = [
    #         {
    #             "role": "system",
    #             "content": "You are a personal trainer and helpful assistant, specializing in nutrition.",
    #         },
    #         {
    #             "role": "user",
    #             "content": "Provide the recipe for a breakfast item that's nutritious, delicious, quick, and easy to make.",
    #         },
    #         # {
    #         #     "role": "assistant",
    #         #     "content": "The capital of France is Paris.",
    #         # },
    #         # {
    #         #     "role": "user",
    #         #     "content": "What about Spain?",
    #         # }
    #     ],
    # )


# IDENTIFY AND INVOKE TOOLS
# Define a function that returns flight information between two cities (mock implementation)
def get_flight_info(origin_city: str, destination_city: str):
    if origin_city == "Seattle" and destination_city == "Miami":
        return dumps({
            "airline": "Delta",
            "flight_number": "DL123",
            "flight_date": "May 7th, 2024",
            "flight_time": "10:00AM"})
    return dumps({"error": "No flights found between the cities"})

# Define a function tool that the model can ask to invoke in order to retrieve flight information
tool = {
    "type": "function",
    "function": {
        "name": "get_flight_info",
        "description": """Returns information about the next flight between two cities.
            This includes the name of the airline, flight number and the date and time
            of the next flight""",
        "parameters": {
            "type": "object",
            "properties": {
                "origin_city": {
                    "type": "string",
                    "description": "The name of the city where the flight originates",
                },
                "destination_city": {
                    "type": "string", 
                    "description": "The flight destination city",
                },
            },
            "required": [
                "origin_city",
                "destination_city"
            ],
        },
    },
}

# messages=[
#     {
#         "role": "system",
#         "content": "You are a helpful assistant that helps users find flight information."
#     },
#     {
#         "role": "user",
#         "content": [
#             {
#                 "type": "text",
#                 "text": "I'm interested in going to Miami. What is the next flight there from Seattle?"
#             },
#         ],
#     },
# ]

messages=[
    {"role": "system", "content": "You an assistant that helps users find flight information."},
    {"role": "user", "content": "I'm interested in going to Miami. What is the next flight there from Seattle?"},
]

response = client.chat.completions.create(
    messages = messages, # type: ignore
    tools = [tool], # type: ignore
    model = MODEL_NAME
)

# We expect the model to ask for a tool call
if response.choices[0].finish_reason == "tool_calls":

    # Append the model response to the chat history
    messages.append(response.choices[0].message) # type: ignore

    # We expect a single tool call
    if response.choices[0].message.tool_calls and len(response.choices[0].message.tool_calls) == 1:

        tool_call = response.choices[0].message.tool_calls[0]

        # We expect the tool to be a function call
        if tool_call.type == "function":

            # Parse the function call arguments and call the function
            function_args = loads(tool_call.function.arguments.replace("'", '"'))
            print(f"Calling function `{tool_call.function.name}` with arguments {function_args}")
            callable_func = locals()[tool_call.function.name]
            function_return = callable_func(**function_args)
            print(f"Function returned = {function_return}")

            # Append the function call result fo the chat history
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_call.function.name,
                    "content": function_return,
                }
            )

            # Get another response from the model
            response = client.chat.completions.create(
                messages = messages, # type: ignore
                tools = [tool], # type: ignore
                model = MODEL_NAME
            )

            print(f"Model response = {response.choices[0].message.content}")