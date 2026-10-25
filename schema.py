from typing import Optional, List
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    task: str = Field(description="What needs to be done")
    owner: Optional[str] = Field(
        default=None,
        description="Person who explicitly committed to the task. null if not clearly stated.",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="Deadline exactly as stated in the transcript. null if not stated.",
    )
    evidence_quote: str = Field(
        description="Exact sentence copied word-for-word from the transcript supporting this item."
    )


class MeetingSummary(BaseModel):
    summary: str = Field(description="3-4 sentence summary of the meeting")
    decisions: List[str] = Field(description="Decisions that were made")
    action_items: List[ActionItem]