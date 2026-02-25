from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    nickname: str
    role: Optional[str] = "team"


class TournamentShort(BaseModel):
    id: int
    title: str
    status: str
    class Config:
        from_attributes = True

class UserOut(UserBase):
    id: int
    role: str
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
    status: str
    creator_id: Optional[int] = None#Тимчасовий фікс
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

    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    team_id: int
    round_id: int
    github_link: str
    video_link: Optional[str] = None
    description: Optional[str] = None
        
