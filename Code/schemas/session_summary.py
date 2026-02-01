from pydantic import BaseModel, Field
from typing import List, Dict

class SessionSummary(BaseModel):
    """
    Structured semantic summary of a chat session,
    used for context recall and augmentation.
    """

    session_intent: str | None = Field(
        default=None,
        description="Overall goal or intent of the session"
    )

    user_profile: Dict = Field(
        default_factory=dict,
        description="User preferences, constraints, or background inferred"
    )

    key_facts: List[str] = Field(
        default_factory=list,
        description="Important factual information mentioned"
    )

    decisions: List[str] = Field(
        default_factory=list,
        description="Decisions or conclusions made"
    )

    constraints: List[str] = Field(
        default_factory=list,
        description="Technical or contextual constraints to respect"
    )

    open_questions: List[str] = Field(
        default_factory=list,
        description="Unresolved questions needing follow-up"
    )

    todos: List[str] = Field(
        default_factory=list,
        description="Action items or next steps"
    )

    summary_text: str | None = Field(
        default=None,
        description="One-paragraph human-readable summary"
    )
    

class MessageRange(BaseModel):
    """
    Represents a range of messages in a chat session.
    """

    start_index: int = Field(
        ...,
        description="Starting index of the message range (inclusive)"
    )

    end_index: int = Field(
        ...,
        description="Ending index of the message range (exclusive)"
    )