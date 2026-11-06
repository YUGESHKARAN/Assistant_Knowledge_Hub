from utility.pinecone_client import index
from pipeline.ingestion_pipeline.embedder import generate_embedding

FIELDS = ["title", "tenantId",  "image", "description", "category",
          "_id", "links", "documents", "authorName", "profile", "authorEmail"]

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
        "tenantId": post.get("tenantId", ""),
        "image": post.get("image", ""),
        "description": post.get("description", ""),
        "category": post.get("category", ""),
        "_id": post.get("_id", ""),
        "authorName": post.get("authorName", ""),
        "profile": post.get("profile", ""),
        "authoremail": post.get("authorEmail", ""),

        # Flatten links (Pinecone-compatible)
        "links": [
            f"{l['title']}: {l['url']}"
            for l in post.get("links", [])
            if "title" in l and "url" in l
        ],

        # Documents must be list of strings
        "documents": post.get("documents", [])
    }


def upsert_post(post: dict, tenantId: str):
    filtered = {k: post[k] for k in FIELDS if k in post}
    filtered["tenantId"] = tenantId

    post_id = filtered["_id"]
    existing = index.fetch(ids=[post_id])["vectors"].get(post_id)
    existing_metadata = (existing.get("metadata") or {}) if existing else {}
    if existing and existing_metadata.get("tenantId") != tenantId:
        raise PermissionError(f"Post {post_id} belongs to a different tenant")

    text = build_text(filtered)

    embedding = generate_embedding(text)
    metadata = clean_metadata(filtered)
    # print("metadata", metadata)

    index.upsert(vectors=[{
        "id": post_id,
        "values": embedding,
        "metadata": metadata
    }])

def delete_post(tenantId:str, post_id: str):
    print("deleting postId", post_id)
    print("deleting post_id", post_id)
    index.delete(filter={
        "_id": {"$eq": post_id},
        "tenantId": {"$eq": tenantId}
    })
