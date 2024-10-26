from pydantic import BaseModel, EmailStr, Field, HttpUrl, ValidationError, field_validator
from typing import Any, Dict, List, Literal, Optional
import pytest
from datetime import datetime, timezone


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
    presentation_time: PresentationTime
