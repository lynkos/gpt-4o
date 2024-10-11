# Cohere Embed V3 Multilingual
from src.Model import TOKEN, ENDPOINT
from azure.ai.inference import EmbeddingsClient
from azure.core.credentials import AzureKeyCredential

MODEL_NAME = "cohere-embed-v3-multilingual"

client = EmbeddingsClient(
    endpoint = ENDPOINT,
    credential = AzureKeyCredential(TOKEN)
)

response = client.embed(
    input=["first phrase", "second phrase", "third phrase"],
    model=MODEL_NAME
)

for item in response.data:
    length = len(item.embedding)
    print(
        f"data[{item.index}]: length={length}, "
        f"[{item.embedding[0]}, {item.embedding[1]}, "
        f"..., {item.embedding[length-2]}, {item.embedding[length-1]}]"
    )

print(response.usage)