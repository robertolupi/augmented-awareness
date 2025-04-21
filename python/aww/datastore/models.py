from sqlmodel import SQLModel, Field


class Memory(SQLModel):
    """Long-term memory."""

    id: int | None = Field(
        default=None,
        primary_key=True,
        description="unique identifier of the memory (auto-assigned)",
    )
    text: str = Field(description="memory content")
    source_id: str = Field(description="source agent of the memory")
