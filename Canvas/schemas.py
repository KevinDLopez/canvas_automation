from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import List, Optional
import pytest


class Answer(BaseModel):
    answer_text: str
    answer_weight: int


class Question(BaseModel):
    question_name: str
    question_text: str
    question_type: str
    points_possible: int
    answers: List[Answer]

    @field_validator("answers")
    def check_total_weight(cls, answers):
        total_weight = sum(answer.answer_weight for answer in answers)
        if total_weight != 100:
            raise ValueError("The total weight of all answers must be 100")
        return answers


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


if __name__ == "__main__":

    def test_answer_weight_validation():
        # * Valid case
        question = Question(
            question_name="Sample Question",
            question_text="What is the answer?",
            question_type="multiple_choice",
            points_possible=10,
            answers=[  # Total weight is 100
                Answer(answer_text="Answer 1", answer_weight=50),
                Answer(answer_text="Answer 2", answer_weight=50),
            ],
        )
        assert question

        # !  Invalid case: total weight not equal to 100
        with pytest.raises(ValidationError):
            Question(
                question_name="Sample Question",
                question_text="What is the answer?",
                question_type="multiple_choice",
                points_possible=10,
                answers=[  # Total weight is 80
                    Answer(answer_text="Answer 1", answer_weight=30),
                    Answer(answer_text="Answer 2", answer_weight=50),
                ],
            )
