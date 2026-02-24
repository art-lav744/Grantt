from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, crud, database
from typing import List

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Tournament Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/tournaments/", response_model=schemas.TournamentOut, tags=["Admin"])
def create_tournament(tournament: schemas.TournamentCreate, db: Session = Depends(get_db)):
    return crud.create_tournament(db=db, tournament=tournament)

#Зміна статусу турніра
@app.patch("/tournaments/{tournament_id}/status", tags=["Admin"])
def update_status(tournament_id: int, status: str, db: Session = Depends(get_db)):
    return crud.update_tournament_status(db, tournament_id, status)

@app.post("/teams/", response_model=schemas.TeamOut, tags=["Teams"])
def register_new_team(team: schemas.TeamCreate, db: Session = Depends(get_db)):
    return crud.register_team(db=db, team_data=team)

#найти усі турніри користувача
@app.get("/members/{email}/tournaments")
def get_my_tournaments(email: str, db: Session = Depends(get_db)):
    members = db.query(models.TeamMember).filter(models.TeamMember.email == email).all()
    result = []
    for m in members:
        team = db.query(models.Team).filter(models.Team.id == m.team_id).first()
        tournament = db.query(models.Tournament).filter(models.Tournament.id == team.tournament_id).first()
        result.append({
            "team_id": team.id,
            "team_name": team.name,
            "tournament_id": tournament.id,
            "tournament_title": tournament.title,
            "tournament_status": tournament.status
        })
    return result

@app.get("/")
def home():
    return {"status": "ok"}

@app.post("/rounds/", tags=["Admin"])
def create_round(round_data: schemas.RoundCreate, db: Session = Depends(get_db)):
    return crud.create_round(db, round_data)

@app.post("/submissions/", tags=["Teams"])
def submit_work(sub: schemas.SubmissionCreate, db: Session = Depends(get_db)):
    return crud.create_submission(db, sub)

@app.post("/rounds/{round_id}/distribute", tags=["Admin"])
def distribute_works(round_id: int, db: Session = Depends(get_db)):
    return crud.distribute_submissions_to_jury(db, round_id)

@app.get("/tournaments/{tournament_id}/leaderboard", response_model=List[schemas.LeaderboardEntry], tags=["Public"])
def read_leaderboard(tournament_id: int, db: Session = Depends(get_db)):
    return crud.get_leaderboard(db, tournament_id=tournament_id)

@app.get("/users/me/team", tags=["User Profile"])
def get_my_team_info(user_id: int, db: Session = Depends(get_db)):
    # Команда, де поточний юзер є капітаном
    return db.query(models.Team).filter(models.Team.captain_id == user_id).first()

@app.get("/users/me/evaluations", tags=["User Profile"])
def get_jury_assignments(user_id: int, db: Session = Depends(get_db)):
    # Список робіт, які призначені цьому журі
    return db.query(models.Evaluation).filter(models.Evaluation.jury_id == user_id).all()