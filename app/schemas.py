from pydantic import BaseModel, field_validator
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from utils import contains_cyrillic
import re
import email_validator

PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_NUMBER = True
PASSWORD_REQUIRE_SPECIAL = True

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    nickname: str
    role: Optional[str] = "team"

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Пароль має бути не менше {PASSWORD_MIN_LENGTH} символів")
        
        if PASSWORD_REQUIRE_NUMBER and not any(char.isdigit() for char in v):
            raise ValueError("Пароль має містити хоча б одну цифру")
            
        if PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Пароль має містити хоча б один спеціальний символ")
            
        return v

    @field_validator("super().email")
    @classmethod
    def validate_email(cls, v: str):
        if contains_cyrillic(v):
            raise ValueError("Елкткронна адреса не повинна містити КИРИЛИЦІ.")
        else:
            try:
                email_validator.validate_email(v)
            except:
                raise ValueError("Введено некоректний формат електронної адреси.")

        return v


class TournamentShort(BaseModel):
    id: int
    title: str
    status: str
    class Config:
        from_attributes = True

class UserOut(UserBase):
    id: int
    role: str
    profile_image_path: Optional[str] = None  # URL до зображення профілю
    tournaments: list[TournamentShort] = []

    class Config:
        from_attributes = True

class TournamentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    reg_start: datetime
    reg_end: datetime

class TournamentOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    creator_id: Optional[int] = None # тимчасовий фікс
    reg_start: Optional[datetime] = None
    reg_end: Optional[datetime] = None
    max_teams: Optional[int] = None
    cover_image_path: Optional[str] = None # URL до зображення турніру
    teams_count: Optional[int] = None
    # Додаткові атрибути для головної сторінки турнірів
    class Config:
        from_attributes = True

class RoundCreate(BaseModel):
    title: str
    description: str
    requirements: str 
    start_time: datetime
    end_time: datetime
    tournament_id: int
    
class RoundOut(RoundCreate):
    id: int
    status: str = "Draft"
    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    team_name: str
    total_score: float
    tech_avg: float
    func_avg: float
    submissions_count: int

    class Config:
        from_attributes = True

class TeamMemberCreate(BaseModel):
    full_name: str
    email: str

class TeamCreate(BaseModel):
    name: str
    tournament_id: int
    captain_email: str
    captain_name: str
    members: list[TeamMemberCreate] = []

class TeamOut(BaseModel):
    id: int
    name: str
    tournament_id: int
    captain_email: str
    captain_name: str
    image_path: Optional[str] = None  # URL/path до зображення команди

    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    team_id: int
    round_id: int
    github_link: str
    video_link: Optional[str] = None
    description: Optional[str] = None
        
