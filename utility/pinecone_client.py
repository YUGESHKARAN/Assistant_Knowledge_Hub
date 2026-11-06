
from pinecone import Pinecone
from utility.config import PINECONE_API_KEY, PINECONE_INDEX

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# if not pc.has_index(PINECONE_INDEX):
#     pc.create_index_for_model(
#         name=PINECONE_INDEX,
#         cloud="aws",
#         region="us-east-1",
#         embed={
#             "model":"llama-text-embed-v2",
#             "field_map":{"text": "chunk_text"}
#         }
#     )



