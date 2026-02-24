from pinecone_client import index
from embedder import generate_embedding
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import JsonOutputParser

from utility.config import GROQ_API_KEY, LLM_MODEL
from utility.schema import AIResponse
from langchain_core.output_parsers import PydanticOutputParser

# from langchain_openai import ChatOpenAI

parser = PydanticOutputParser(pydantic_object=AIResponse)
format_instructions = parser.get_format_instructions()
from dotenv import load_dotenv
load_dotenv()

# client = Groq(api_key=GROQ_API_KEY)
llm = ChatGroq(api_key=GROQ_API_KEY, model=LLM_MODEL)
# llm = ChatOpenAI(model_name="gpt-4")

# def retrieve(query: str,current_post_id:str, top_k=3):
#     embedding = generate_embedding(query)

#     res = index.query(
#         vector=embedding,
#         top_k=top_k,
#         include_metadata=True,
#         filter={"postId": {"$eq": current_post_id}},
#     )

#     return [match["metadata"] for match in res["matches"]]

def retrieve(query: str, current_post_id: str, top_k=5):
    embedding = generate_embedding(query)

    # 1. Semantic search
    res = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )

    docs = [match["metadata"] | {"_id": match["id"]} for match in res["matches"]]

    # 2. Always fetch current post explicitly
    current = index.fetch(ids=[current_post_id])

    if current and current["vectors"]:
        current_doc = current["vectors"][current_post_id]["metadata"]
        current_doc["_id"] = current_post_id

        # Inject current post if missing
        if current_post_id not in [d["_id"] for d in docs]:
            docs.insert(0, current_doc)

    return docs

def detect_youtube_links(posts):
    videos = []
    for p in posts:
        for link in p.get("links", []):
            url = link.get("url", "")
            if "youtube.com" in url or "youtu.be" in url:
                videos.append({
                    "title": link.get("title", p["title"]),
                    "url": url
                })
    return videos

def ask_ai(query: str, current_post_id: str, SYSTEM_PROMPT:str) :
    docs = retrieve(query,current_post_id)
    # print("Retrieved docs:", docs)
     
    rag_context = ""
    
    for d in docs:
        rag_context += f"""
        Title: {d['title']}
        Description: {d['description']}
        Links: {d.get('links', [])}
        Author: {d['authorName']}
        Email: {d['authoremail']}
        PostId: {d['_id']}
        Category: {d['category']}
        Documents: {d.get('documents', [])}
        Profile: {d['profile']}
        Image: {d['image']}
        """
    
    template = """
      SYSTEM PROMPT:
      {SYSTEM_PROMPT}

      OUTPUT FORMAT (MANDATORY):
      {format_instructions}

      DATA:

      Current Post ID:
      {current_post_id}

      RAG Context (array of posts with fields like title, description, _id, links, etc):
      {rag_context}

      User Query:
      {query}
    """

    prompt = ChatPromptTemplate.from_template(template=template)

    chain =  prompt | llm | parser
    response = chain.invoke({
        "rag_context": rag_context,
        "query": query,
        "current_post_id": current_post_id,
        "format_instructions": format_instructions,
        "SYSTEM_PROMPT":SYSTEM_PROMPT
    })

    print("current_post_id:", current_post_id)

    return response.dict()
