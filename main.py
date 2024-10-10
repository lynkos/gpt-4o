from base64 import b64encode
from json import dumps, loads
from os import environ
from openai import OpenAI

TOKEN = environ["GITHUB_TOKEN"]
ENDPOINT = "https://models.inference.ai.azure.com"
MODEL_NAME = "gpt-4o"

client = OpenAI(
    base_url = ENDPOINT,
    api_key = TOKEN,
)

# BASIC EXAMPLE
response = client.chat.completions.create(
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
    temperature = 1.0,
    top_p = 1.0,
    max_tokens = 1000,
    model = MODEL_NAME
)

print(response.choices[0].message.content)

# MULTI-TURN + STREAMED OUTPUT EXAMPLE
response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": "What is the capital of France?",
        },
        {
            "role": "assistant",
            "content": "The capital of France is Paris.",
        },
        {
            "role": "user",
            "content": "What about Spain?",
        }
    ],
    #temperature = 1.0,
    #top_p = 1.0,
    #max_tokens = 1000,
    model = MODEL_NAME,
    stream = True
)

for update in response:
    if update.choices[0].delta.content:
        print(update.choices[0].delta.content, end="")

# IMAGE INPUT
def get_image_data_url(image_file: str, image_format: str) -> str:
    """
    Helper function to converts an image file to a data URL string.

    Args:
        image_file (str): The path to the image file.
        image_format (str): The format of the image file.

    Returns:
        str: The data URL of the image.
    """
    try:
        with open(image_file, "rb") as f:
            image_data = b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        print(f"Could not read '{image_file}'.")
        exit(1)
    return f"data:image/{image_format};base64,{image_data}"

response = client.chat.completions.create(
    messages=[
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
                        "url": get_image_data_url("sample.jpg", "jpg"),
                        "detail": "low"
                    },
                },
            ],
        },
    ],
    model = MODEL_NAME,
)

print(response.choices[0].message.content)

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