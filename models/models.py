from pydantic import BaseModel, Field


class Message(BaseModel):
    """
    Represents a message entity within our domain.
    This is a core business object, independent of any framework.
    """

    id: int = Field(..., description="The unique identifier for the message.")
    content: str = Field(..., description="The text content of the message.")
    status: str = Field(
        default="pending", description="The current status of the message."
    )

