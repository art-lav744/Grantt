import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime
from .database import Base
from sqlalchemy.orm import relationship

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    TEAM = "team"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default=UserRole.TEAM)
    tournaments = relationship("Tournament", back_populates="creator")

class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    status = Column(String, default="open")
    creator_id = Column(Integer, ForeignKey("users.id"))
    reg_start = Column(DateTime)
    reg_end = Column(DateTime)
    creator = relationship("User", back_populates="tournaments")

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    captain_email = Column(String)
    captain_name = Column(String)
    members = relationship("TeamMember", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String)
    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="members")