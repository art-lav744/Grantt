import random
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime
from . import models, schemas
from .utils import hash_password

# ── User ────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_nickname(db: Session, nickname: str):
    return db.query(models.User).filter(models.User.nickname == nickname).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        email=user.email,
        hashed_password=hash_password(user.password),  # Хешуємо пароль перед збереженням
        role=user.role,
        nickname=user.nickname
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_profile_image(db: Session, user_id: int, image_path: str):
    """Saves the profile photo path for a user."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.profile_image_path = image_path
    db.commit()
    db.refresh(user)
    return user

# ── Tournaments ─────────────────────────────────────────────────

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

def get_tournaments(db: Session, status: str = None):
    query = db.query(models.Tournament)
    if status:
        query = query.filter(models.Tournament.status == status)
    tournaments = query.all()
    
    result = []
    for t in tournaments:
        teams_count = db.query(models.Team).filter(models.Team.tournament_id == t.id).count()
        result.append({
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "creator_id": t.creator_id,
            "cover_image_path": t.cover_image_path,
            "max_teams": t.max_teams,
            "teams_count": teams_count
        })
    return result

def get_user_tournaments(db: Session, user_id: int):
    return db.query(models.Tournament).filter(models.Tournament.creator_id == user_id).all()

def update_tournament_image(db: Session, tournament_id: int, image_path: str):
    """Saves the cover/banner image path for a tournament."""
    tournament = db.query(models.Tournament).filter(models.Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    tournament.cover_image_path = image_path
    db.commit()
    db.refresh(tournament)
    return tournament

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
# Формуємо список для лідерборду з обчисленням загального балу та округленням до 2 знаків після коми
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

# ── Team ────────────────────────────────────────────────────────

def register_team(db: Session, team_data: schemas.TeamCreate):
    # 1. Шукаємо турнір
    tournament = db.query(models.Tournament).filter(models.Tournament.id == team_data.tournament_id).first()
    
    if not tournament:
        raise HTTPException(status_code=404, detail="Турнір не знайдено")

    # 2. Перевірка статусу та часового вікна
    if tournament.status != "registration":
        raise HTTPException(status_code=400, detail="Реєстрація на цей турнір закрита або ще не почалася")

    now = datetime.utcnow()
    if not (tournament.reg_start <= now <= tournament.reg_end):
        raise HTTPException(status_code=400, detail="Ви поза межами реєстраційного вікна")

    # 3. ПЕРЕВІРКА: Максимальна кількість команд у турнірі
    current_teams_count = db.query(models.Team).filter(models.Team.tournament_id == team_data.tournament_id).count()
    if tournament.max_teams and current_teams_count >= tournament.max_teams:
        raise HTTPException(status_code=400, detail=f"Усі місця на турнір зайняті (макс. {tournament.max_teams})")

    # 4. ПЕРЕВІРКА: Максимальна кількість людей у команді
    # Наприклад, ліміт 5 (можна винести в константу або поле турніру)
    MAX_MEMBERS = 5
    if len(team_data.members) > MAX_MEMBERS:
        raise HTTPException(status_code=400, detail=f"Максимальна кількість учасників — {MAX_MEMBERS}")

    # 5. ПЕРЕВІРКА: Унікальність імейлів (капітан + учасники)
    # Збираємо всі email в один список
    all_emails = [team_data.captain_email] + [m.email for m in team_data.members]
    
    # Перевірка на дублікати всередині самої форми
    if len(all_emails) != len(set(all_emails)):
        raise HTTPException(status_code=400, detail="Один і той самий email вказано кілька разів")

    # Перевірка, чи ці імейли вже зареєстровані В ЦЬОМУ турнірі
    for email in all_emails:
        # Шукаємо серед капітанів інших команд
        exists_as_captain = db.query(models.Team).filter(
            models.Team.tournament_id == team_data.tournament_id,
            models.Team.captain_email == email
        ).first()
        
        # Шукаємо серед учасників інших команд
        exists_as_member = db.query(models.TeamMember).join(models.Team).filter(
            models.Team.tournament_id == team_data.tournament_id,
            models.TeamMember.email == email
        ).first()

        if exists_as_captain or exists_as_member:
            raise HTTPException(status_code=400, detail=f"Учасник з email {email} вже зареєстрований у цьому турнірі")

    # Якщо всі перевірки пройшли успішно — створюємо команду
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

def update_team_image(db: Session, team_id: int, image_path: str):
    """Saves the image path for a team after the file has been uploaded."""
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    team.image_path = image_path
    db.commit()
    db.refresh(team)
    return team

# ── Rounds ──────────────────────────────────────────────────────

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
