from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):

    document_id: str


class RedFlagRequest(BaseModel):

    document_id: str


class ChatMessage(BaseModel):

    role: str = Field(
        ...,
        description=(
            "Message role: user or assistant."
        ),
    )

    content: str = Field(
        ...,
        min_length=1,
        description=(
            "Message content."
        ),
    )


class ResearchAskRequest(BaseModel):

    document_id: str = Field(
        ...,
        description=(
            "Document ID of the indexed "
            "financial document."
        ),
    )

    question: str = Field(
        ...,
        min_length=1,
        description=(
            "Natural-language financial "
            "research question."
        ),
    )

    conversation_id: str | None = Field(
        default=None,
        description=(
            "Conversation ID. If omitted, "
            "a new conversation is created."
        ),
    )

    chat_history: list[ChatMessage] = Field(
        default_factory=list,
        description=(
            "Optional previous messages."
        ),
    )


class ResearchSource(BaseModel):

    filename: str | None = None

    page: int | None = None

    chunk_index: int | None = None

    source: str | None = None


class ResearchAskResponse(BaseModel):

    document_id: str

    question: str

    answer: str

    conversation_id: str

    sources: list[ResearchSource] = Field(
        default_factory=list
    )