import random
from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import func

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        email=user.email,
        hashed_password=user.password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_tournament(db: Session, tournament: schemas.TournamentCreate):
    db_tournament = models.Tournament(
        title=tournament.title,
        description=tournament.description,
        reg_start=tournament.reg_start,
        reg_end=tournament.reg_end,
        status="draft" # Початковий статус
    )
    db.add(db_tournament)
    db.commit()
    db.refresh(db_tournament)
    return db_tournament

def update_tournament_status(db: Session, tournament_id: int, status: str):
    db_tournament = db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()
    if db_tournament:
        db_tournament.status = status
        db.commit()
    return db_tournament

def get_user_tournaments(db: Session, user_id: int):
    return db.query(models.Tournament).filter(models.Tournament.creator_id == user_id).all()

def register_team(db: Session, team_data: schemas.TeamCreate):

    tournament = db.query(models.Tournament).filter(models.Tournament.id == team_data.tournament_id).first()
    
    if not tournament or tournament.status != "registration":
        raise HTTPException(status_code=400, detail="Реєстрація на цей турнір закрита або ще не почалася")


    now = datetime.utcnow()
    if not (tournament.reg_start <= now <= tournament.reg_end):
        raise HTTPException(status_code=400, detail="Ви поза межами реєстраційного вікна")


    db_team = models.Team(
        name=team_data.name,
        tournament_id=team_data.tournament_id,
        captain_email=team_data.captain_email,
        captain_name=team_data.captain_name
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)

    # Додавання учасників
    for member in team_data.members:
        db_member = models.TeamMember(
            full_name=member.full_name,
            email=member.email,
            team_id=db_team.id
        )
        db.add(db_member)
    
    db.commit()
    return db_team

def create_submission(db: Session, sub_data: schemas.SubmissionCreate):

    round_obj = db.query(models.Round).filter(models.Round.id == sub_data.round_id).first()
    
    if not round_obj or round_obj.end_time < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Час подачі робіт вичерпано або раунд не знайдено")
    
    db_sub = models.Submission(
        team_id=sub_data.team_id,
        round_id=sub_data.round_id,
        github_link=sub_data.github_link,
        video_link=sub_data.video_link,
        description=sub_data.description
    )
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub

def distribute_submissions_to_jury(db: Session, round_id: int):
    submissions = db.query(models.Submission).filter(models.Submission.round_id == round_id).all()
    jury_members = db.query(models.User).filter(models.User.role == "jury").all()
    
    if not jury_members:
        raise HTTPException(status_code=400, detail="Немає зареєстрованих членів журі")

    assignments = []
    for sub in submissions:
        # Вибираємо 2 випадкових членів журі для кожної роботи (як у ТЗ)
        chosen_jury = random.sample(jury_members, k=min(2, len(jury_members)))
        for jury in chosen_jury:
            eval_record = models.Evaluation(
                submission_id=sub.id,
                jury_id=jury.id,
                tech_score=0, # Початкове значення
                func_score=0
            )
            db.add(eval_record)
    db.commit()
    return {"status": "Роботи розподілено між журі"}

def get_leaderboard(db: Session, tournament_id: int):

    results = db.query(
        models.Team.name,
        func.avg(models.Evaluation.tech_score).label("tech_avg"),
        func.avg(models.Evaluation.func_score).label("func_avg"),
        func.count(models.Submission.id).label("subs_count")
    ).join(models.Submission, models.Team.id == models.Submission.team_id)\
     .join(models.Evaluation, models.Submission.id == models.Evaluation.submission_id)\
     .filter(models.Team.tournament_id == tournament_id)\
     .group_by(models.Team.id)\
     .all()

    leaderboard = []
    for res in results:
        total = (res.tech_avg + res.func_avg) / 2 
        leaderboard.append({
            "team_name": res.name,
            "tech_avg": round(res.tech_avg, 2),
            "func_avg": round(res.func_avg, 2),
            "total_score": round(total, 2),
            "submissions_count": res.subs_count
        })
    
    return sorted(leaderboard, key=lambda x: x["total_score"], reverse=True)
