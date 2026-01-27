from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# ---------- Sub Models ----------

class Video(BaseModel):
    title: str = Field(description="Title of the video if available, else 'YouTube Video'")
    url: str = Field(description="YouTube URL only")

class Link(BaseModel):
    title: str = Field(description="Title of the link, e.g., YouTube, Publication")
    url: str = Field(description="URL of the resource")

class SuggestedPost(BaseModel):
    postId: str = Field(description="MongoDB _id of the post")
    title: str = Field(description="Post title")
    authorName: str = Field(description="Author name")
    authorEmail: str = Field(description="Author email")
    category: str = Field(description="Post category")
    profile: str = Field(description="Author profile image URL")
    image: str = Field(description="Post cover image URL")
    links: List[Link] = Field(description="Source links related to the post except YouTube links")


# ---------- Main Response ----------

class AIResponse(BaseModel):
    type: Literal["text", "text_video", "post_suggestions"] = Field(
        description="One of: text, text_video, post_suggestions"
    )

    content: str = Field(
        description="Markdown answer grounded only in RAG context with personalized assistant touch"
    )

    videos: Optional[List[Video]] = Field(
        default=None,
        description="Present only when type=text_video"
    )

    posts: Optional[List[SuggestedPost]] = Field(
        default=None,
        description="Present only when type=post_suggestions"
    )

    suggestions: Optional[List[str]] = Field(
        description="3-5 follow-up questions user might ask next"
    )
