from pydantic import BaseModel, EmailStr, Field, HttpUrl, ValidationError, field_validator
from typing import Any, Dict, List, Literal, Optional, TypedDict
import pytest
from datetime import datetime, timezone


class UsersSchema(TypedDict):
    id: int
    name: str
    created_at: str
    sortable_name: str
    short_name: str
    email: str


class MediaComment(BaseModel):
    content_type: str
    display_name: str
    media_id: str
    media_type: str
    url: HttpUrl


class SubmissionComment(BaseModel):
    id: int
    author_id: int
    author_name: str
    author: Optional[Dict[str, Any]]
    comment: str
    created_at: datetime
    edited_at: datetime
    media_comment: Optional[MediaComment] = None


class SubmissionSchema(BaseModel):
    class Config:
        extra = "allow"  # Allow extra fields and can retrieve them without throwing an error

    assignment_id: int
    assignment: Optional[Dict[str, Any]] = None
    course: Optional[Dict[str, Any]] = None
    attempt: Optional[int] = None
    body: Optional[str] = None
    grade: Optional[str] = None
    grade_matches_current_submission: Optional[bool] = None
    html_url: Optional[HttpUrl] = None
    preview_url: Optional[HttpUrl] = None
    score: Optional[float] = None
    submission_comments: Optional[List[SubmissionComment]] = None
    submission_type: Optional[
        Literal[
            "online_text_entry", "online_url", "online_upload", "online_quiz", "media_recording", "student_annotation"
        ]
    ] = None
    submitted_at: Optional[datetime] = None
    url: Optional[HttpUrl] = None
    user_id: int
    grader_id: Optional[int] = None
    graded_at: Optional[datetime] = None
    user: Optional[Dict[str, Any]] = None
    late: bool = False
    assignment_visible: bool = True
    missing: bool = False
    excused: Optional[bool] = None
    late_policy_status: Optional[Literal["late", "missing", "extended", "none"]] = None
    points_deducted: Optional[float] = None
    seconds_late: Optional[int] = None
    workflow_state: str
    extra_attempts: Optional[int] = None
    anonymous_id: Optional[str] = None
    posted_at: Optional[datetime] = None
    read_status: Optional[str] = None
    redo_request: bool
    attachments: Optional[List[Dict[str, Any]]] = None


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
    allowed_attempts: int = Field(ge=1, description="Allowed attempts must be at least 1")
    questions: List[Question]


class ModuleSchema(BaseModel):
    id: int
    workflow_state: str = "active"  # Default value
    position: int
    name: str
    unlock_at: Optional[datetime] = None
    require_sequential_progress: bool
    prerequisite_module_ids: List[int]
    items_count: int
    items_url: HttpUrl
    items: Optional[List] = None
    state: Optional[str] = None
    completed_at: Optional[datetime] = None
    publish_final_grade: Optional[bool] = None
    published: Optional[bool] = None


class AssignmentSchema(BaseModel):
    id: int
    description: str
    due_at: Optional[datetime] = None
    unlock_at: Optional[datetime] = None
    lock_at: Optional[datetime] = None
    points_possible: float
    grading_type: str
    assignment_group_id: int
    grading_standard_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    peer_reviews: bool
    automatic_peer_reviews: bool
    position: int
    grade_group_students_individually: bool
    anonymous_peer_reviews: bool
    group_category_id: Optional[int] = None
    post_to_sis: bool
    moderated_grading: bool
    omit_from_final_grade: bool
    intra_group_peer_reviews: bool
    anonymous_instructor_annotations: bool
    anonymous_grading: bool
    graders_anonymous_to_graders: bool
    grader_count: int
    grader_comments_visible_to_graders: bool
    final_grader_id: Optional[int] = None
    grader_names_visible_to_final_grader: bool
    allowed_attempts: int
    annotatable_attachment_id: Optional[int] = None
    hide_in_gradebook: bool
    secure_params: str
    lti_context_id: str
    course_id: int
    name: str
    submission_types: List[str]
    has_submitted_submissions: bool
    due_date_required: bool
    max_name_length: int
    in_closed_grading_period: bool
    graded_submissions_exist: bool
    is_quiz_assignment: bool
    can_duplicate: bool
    original_course_id: Optional[int] = None
    original_assignment_id: Optional[int] = None
    original_lti_resource_link_id: Optional[int] = None
    original_assignment_name: Optional[str] = None
    original_quiz_id: Optional[int] = None
    workflow_state: str
    important_dates: bool
    muted: bool
    html_url: str
    has_overrides: bool
    needs_grading_count: int
    quiz_id: Optional[int] = None
    anonymous_submissions: Optional[bool] = None
    published: bool
    unpublishable: bool
    only_visible_to_overrides: bool
    visible_to_everyone: bool
    locked_for_user: bool
    submissions_download_url: str
    post_manually: bool
    anonymize_students: bool
    require_lockdown_browser: bool
    restrict_quantitative_data: bool


############# MODULE ITEM ############
class CompletionRequirement(BaseModel):
    type: str
    min_score: Optional[int] = None
    completed: bool


class ContentDetails(BaseModel):
    points_possible: Optional[int] = None
    due_at: Optional[datetime] = None
    unlock_at: Optional[datetime] = None
    lock_at: Optional[datetime] = None


class ModuleItemSchema(BaseModel):
    id: int
    module_id: int
    position: int
    title: str
    indent: int
    type: str
    content_id: Optional[int] = None
    html_url: HttpUrl
    url: Optional[HttpUrl] = None
    page_url: Optional[str] = None
    external_url: Optional[HttpUrl] = None
    new_tab: Optional[bool] = None
    completion_requirement: Optional[CompletionRequirement] = None
    content_details: Optional[ContentDetails] = None
    published: Optional[bool] = None


############### Page schema  ###############
class LastEditedBy(BaseModel):
    anonymous_id: Optional[str] = None
    avatar_image_url: Optional[HttpUrl] = None
    display_name: Optional[str] = None
    html_url: Optional[HttpUrl] = None
    id: Optional[int] = None
    pronouns: Optional[str] = None


class BlockEditorAttributes(BaseModel):
    id: int
    version: str
    blocks: str


class PageSchema(BaseModel):
    page_id: int
    url: str
    title: str
    created_at: datetime
    updated_at: datetime
    hide_from_students: bool
    editing_roles: str
    last_edited_by: Optional[LastEditedBy] = None
    body: Optional[str] = None
    published: bool
    publish_at: Optional[datetime] = None
    front_page: bool
    locked_for_user: bool
    lock_info: Optional[Dict[str, Any]] = None
    lock_explanation: Optional[str] = None
    editor: Optional[Literal["rce", "block_editor"]] = None
    block_editor_attributes: Optional[BlockEditorAttributes] = None


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
