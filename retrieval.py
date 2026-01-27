from pinecone_client import index
from embedder import generate_embedding
from utility.prompt import SYSTEM_PROMPT
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from utility.config import GROQ_API_KEY, LLM_MODEL
from utility.schema import AIResponse
from langchain_core.output_parsers import PydanticOutputParser

from langchain_openai import ChatOpenAI

parser = PydanticOutputParser(pydantic_object=AIResponse)
format_instructions = parser.get_format_instructions()
from dotenv import load_dotenv
load_dotenv()

# client = Groq(api_key=GROQ_API_KEY)
llm = ChatGroq(api_key=GROQ_API_KEY, model=LLM_MODEL)
# llm = ChatOpenAI(model_name="gpt-4")

def retrieve(query: str, top_k=5):
    embedding = generate_embedding(query)

    res = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )

    return [match["metadata"] for match in res["matches"]]

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

def ask_ai(query: str, current_post_id: str) :
    docs = retrieve(query)

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

        ---

        """
    
 

    template = """
You are a personalized AI learning assistant for a tech community platform (like YouTube AI assistant).

You are given:
- A Current Post ID
- A list of posts inside RAG Context

Your first step (MANDATORY):
- Find the post inside RAG Context whose "_id" matches the Current Post ID.
- Treat that matched post as the "Current Post".

If no post matches the ID:
- Respond with:
  "I couldn't find this in the current posts."

Your role:
- Answer the user's question naturally like a real tutor.
- Use ONLY the information from:
  - The matched Current Post
  - And other posts in RAG Context if the query asks for suggestions.
- Do NOT mention words like "RAG", "context", "database", or "posts".
- Never hallucinate.

BEHAVIOR RULES:
1. If the user's query is about:
   - summarizing
   - explaining
   - meaning
   - clarification
   - details of this post  
   → Use ONLY the matched Current Post.

2. If the user's query asks for:
   - related content
   - similar topics
   - recommendations
   - suggested posts
   - suggested videos  
   → Use all RAG Context to construct suggestions.

3. If the answer cannot be found in the provided data, respond with:
   "I couldn't find this in the current posts."

STRICT OUTPUT RULES:
- Return ONLY valid JSON.
- No extra text.
- No markdown code fences.
- Must follow the schema exactly.

CONTENT RULES:
- "content" must be high-quality Markdown:
  - Headings
  - Bullet points
  - Clear explanations
- Answer the user's question directly.
- Do NOT summarize the dataset.
- Do NOT describe where data came from.


SUGGESTION RULES:
- Only populate videos/posts if user explicitly asks:
  "suggest", "recommend", "related", "similar"
- Otherwise:
  - "videos": null
  - "posts": null

FOLLOW-UP SUGGESTIONS RULES:
- Always generate 3 to 5 suggested questions.
- Suggestions must:
  - Be relevant to the current topic
  - Help user learn deeper
  - Be phrased as natural questions
- Use both:
  - The current post topic
  - The user's current question
- Do not repeat the user's query.
- Do not generate generic questions.
- Keep each suggestion under 15 words.


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
        "format_instructions": format_instructions
    })
    print()
    print("rag_context:", rag_context)
    print()

    return response.dict()
