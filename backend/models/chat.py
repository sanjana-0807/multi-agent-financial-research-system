from datetime import datetime, timezone

from beanie import Document
from pydantic import Field


class ChatMessage(Document):

    conversation_id: str

    document_id: str

    role: str

    content: str

    sources: list[dict] = Field(
        default_factory=list
    )

    created_at: datetime = Field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )

    class Settings:
        name = "chat_messages"