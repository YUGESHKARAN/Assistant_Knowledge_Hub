
# from openai import OpenAI
# from utility.config import EMBED_MODEL

# client = OpenAI()

# def generate_embedding(text: str):
#     res = client.embeddings.create(
#         model=EMBED_MODEL,
#         input=text,
#         dimensions=512
#     )
#     return res.data[0].embedding

from pinecone import Pinecone
from utility.config import PINECONE_API_KEY
pc = Pinecone(api_key=PINECONE_API_KEY)

def generate_embedding(text: str):
    embeddings = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=[{"text": text}],
        parameters={
            "input_type": "passage",
            "truncate": "END",
            "dimension": 512
        }
    )
    return embeddings[0]["values"]
