
from openai import OpenAI
from utility.config import EMBED_MODEL

client = OpenAI()

def generate_embedding(text: str):
    res = client.embeddings.create(
        model=EMBED_MODEL,
        input=text,
        dimensions=512
    )
    return res.data[0].embedding
