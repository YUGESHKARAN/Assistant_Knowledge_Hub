
import os
from dotenv import load_dotenv
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

EMBED_MODEL = "text-embedding-3-small"
# LLM_MODEL = "llama-3.1-8b-instant"
LLM_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
