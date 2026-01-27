from pinecone_client import index
from embedder import generate_embedding

FIELDS = ["title", "image", "description", "category",
          "_id", "links", "documents", "authorName", "profile", "authoremail"]

def build_text(post):
    """
    Creates a text representation of the post for embedding generation.
    """
    # links_text = ""
    # if post.get("links"):
    #     links_text = "\n".join([
    #         f"{l['title']}: {l['url']}" for l in post["links"]
    #     ])

    # documents_text = ""
    # if post.get("documents"):
    #     documents_text = "\n".join([
    #         f"Document: {doc}" for doc in post["documents"]
    #     ])

    return f"""
    Title: {post['title']}
    Category: {post['category']}
    Author: {post['authorName']}
    Description:{post['description']}
    """

def clean_metadata(post):
    """
    Converts raw post into Pinecone-compatible metadata.
    """

    return {
        "title": post.get("title", ""),
        "image": post.get("image", ""),
        "description": post.get("description", ""),
        "category": post.get("category", ""),
        "_id": post.get("_id", ""),
        "authorName": post.get("authorName", ""),
        "profile": post.get("profile", ""),
        "authoremail": post.get("authoremail", ""),

        # Flatten links (Pinecone-compatible)
        "links": [
            f"{l['title']}: {l['url']}"
            for l in post.get("links", [])
            if "title" in l and "url" in l
        ],

        # Documents must be list of strings
        "documents": post.get("documents", [])
    }


def upsert_post(post: dict):
    filtered = {k: post[k] for k in FIELDS if k in post}
    text = build_text(filtered)

    embedding = generate_embedding(text)
    metadata = clean_metadata(filtered)

    index.upsert(vectors=[{
        "id": filtered["_id"],
        "values": embedding,
        "metadata": metadata
    }])

def delete_post(post_id: str):
    index.delete(ids=[post_id])
