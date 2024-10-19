from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional


class Answer(BaseModel):
    answer_text: str
    answer_weight: int = Field(
        ge=0, le=100, description="Weight must be between 0 and 100"
    )


class Question(BaseModel):
    question_name: str
    question_text: str
    question_type: str
    points_possible: int
    answers: List[Answer]


class QuizSchema(BaseModel):
    title: str
    description: str
    quiz_type: str = "assignment"  # Default value is 'assignment'
    time_limit: int = Field(ge=1, description="Time limit must be at least 1 minute")
    shuffle_answers: bool = False
    allowed_attempts: int = Field(
        ge=1, description="Allowed attempts must be at least 1"
    )
    questions: List[Question]
