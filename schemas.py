from pydantic import BaseModel, EmailStr, Field, HttpUrl, ValidationError, field_validator
from typing import Any, Dict, List, Literal, Optional
import pytest
from datetime import datetime, timezone
from typing import TypedDict, Optional, List


############### TEAM FORMS ###############
class TeamMember(BaseModel):
    name: str
    email: EmailStr


class PresentationTime(BaseModel):
    start: datetime
    end: datetime


class TeamInfo(BaseModel):
    team_name: str
    topic: str
    team_members: List[TeamMember]
    github_repo: str
    # presentation_time: PresentationTime


######## CLASS INFO ########
# course_id: 15319
# presentation_module_title: "Fall 2024 - Presentation"
class ClassInfoSchema(BaseModel):
    course_id: int
    presentation_module_title: str


class StudentRecord(TypedDict, total=True):
    Canvas_ID: str | Literal[""]
    Canvas_Team_Page_State: Literal["", "Created", "Quiz and Feedback added", "Done"]
    Email: str
    Google_Form_ID: str | Literal[""]
    Names: str
    Student_ID: str
    Team_Name: str
    Topic: str
    Github_Repo: str


StudentRecords = List[StudentRecord]
