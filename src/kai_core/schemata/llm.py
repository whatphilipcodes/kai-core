from pydantic import BaseModel


class ContextUpdateResponse(BaseModel):
    transcript_append: str
    visual_update: str
    should_answer: bool
    answer_text: str
