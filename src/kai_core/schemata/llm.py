from pydantic import BaseModel


class DecodeModalInputResponse(BaseModel):
    transcript: str
    vision: str


class UpdateContextResponse(BaseModel):
    new_scene_description: str
    should_answer: bool


class GenerateAnswerResponse(BaseModel):
    answer: str
