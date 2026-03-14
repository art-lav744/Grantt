from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, crud, database
from .utils import save_team_image, save_profile_image, save_tournament_image, verify_password, create_access_token, decode_access_token


# ── Setup ────────────────────────────────────────────────────────

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Tournament Platform API")

# Serve uploaded images as static files at /static/team_images/<filename>
app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB ───────────────────────────────────────────────────────────

# Функція для отримання сесії бази даних, яка буде використовуватися в залежностях FastAPI для автоматичного відкриття та закриття сесії при кожному запиті
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Auth ─────────────────────────────────────────────────────────


# Використовуємо OAuth2PasswordBearer для отримання JWT токена
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# Функція для отримання поточного користувача на основі JWT токена
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    # Шукаємо користувача в базі даних за ID, який зберігається в токені (payload["sub"])
    user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="Користувача не знайдено.")
    return user

# Декоратори для перевірки ролей користувача
def require_admin(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Тільки для адміністраторів.")
    return current_user

def require_organizer_or_admin(current_user = Depends(get_current_user)):
    if current_user.role not in ("admin", "organizer"):
        raise HTTPException(status_code=403, detail="Недостатньо прав.")
    return current_user

def require_jury(current_user = Depends(get_current_user)):
    if current_user.role != "jury":
        raise HTTPException(status_code=403, detail="Тільки для журі.")
    return current_user

# ── Users ────────────────────────────────────────────────────────

@app.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud.get_user_by_nickname(db, nickname=user.nickname):
        raise HTTPException(status_code=400, detail="Nickname already taken")
    return crud.create_user(db=db, user=user)

@app.post("/login")
def login_user(data: dict, db: Session = Depends(get_db)):
    email = data.get("email")
    password = data.get("password")

    # Шукаємо користувача
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Користувача не знайдено")

    # Перевіряємо пароль
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Невірний пароль")

    # Повертаємо дані, які чекає index.html та login.html
    return {
        "access_token": create_access_token(user.id, user.role),
        "role": user.role,
        "nickname": user.nickname,
        "user_id": user.id,
        "email": user.email  # додати
    }

@app.post("/users/{user_id}/image", response_model=schemas.UserOut, tags=["User Profile"])
async def upload_profile_image(
                user_id: int,
                file: UploadFile = File(..., description="User profile photo. JPEG, PNG, GIF or WEBP, max 5 MB."),
                db: Session = Depends(get_db), _ = Depends(get_current_user)):
    image_path = await save_profile_image(file)
    return crud.update_user_profile_image(db, user_id=user_id, image_path=image_path)

@app.get("/users/me/team", tags=["User Profile"])
def get_my_team_info(
                user_id: int, 
                db: Session = Depends(get_db), _ = Depends(get_current_user)):
    return db.query(models.Team).filter(models.Team.captain_id == user_id).first()

@app.get("/users/me/evaluations", tags=["User Profile"])
def get_jury_assignments(
                user_id: int,
                db: Session = Depends(get_db), _ = Depends(get_current_user)):
    # Список робіт, які призначені цьому журі
    return db.query(models.Evaluation).filter(models.Evaluation.jury_id == user_id).all()



# ── Tournaments ──────────────────────────────────────────────────

@app.post("/tournaments/", response_model=schemas.TournamentOut, tags=["Admin"])
def create_tournament(
                tournament: schemas.TournamentCreate,
                db: Session = Depends(get_db), _ = Depends(require_admin)):
    return crud.create_tournament(db=db, tournament=tournament)

@app.get("/tournaments/", response_model=List[schemas.TournamentOut], tags=["Public"])
def get_tournaments(status: str = None, db: Session = Depends(get_db)):
    return crud.get_tournaments(db, status=status)

# Зміна статусу турніру
@app.patch("/tournaments/{tournament_id}/status", tags=["Admin"])
def update_status(
                tournament_id: int,
                status: str,
                db: Session = Depends(get_db), _ = Depends(require_organizer_or_admin)):
    
    return crud.update_tournament_status(db, tournament_id, status)

@app.post("/tournaments/{tournament_id}/image", response_model=schemas.TournamentOut, tags=["Admin"])
async def upload_tournament_image(
                tournament_id: int,
                file: UploadFile = File(..., description="Tournament cover/banner. JPEG, PNG, GIF or WEBP, max 5 MB."),
                db: Session = Depends(get_db), _ = Depends(require_organizer_or_admin)):
    
    image_path = await save_tournament_image(file)
    return crud.update_tournament_image(db, tournament_id=tournament_id, image_path=image_path)

@app.get("/tournaments/{tournament_id}/leaderboard", response_model=List[schemas.LeaderboardEntry], tags=["Public"])
def read_leaderboard(
                tournament_id: int,
                db: Session = Depends(get_db)):
    
    return crud.get_leaderboard(db, tournament_id=tournament_id)

# ── Teams ────────────────────────────────────────────────────────

@app.post("/teams/", response_model=schemas.TeamOut, tags=["Teams"])
def register_new_team(
                team: schemas.TeamCreate,
                db: Session = Depends(get_db), _ = Depends(get_current_user)):
    return crud.register_team(db=db, team_data=team)

@app.post("/teams/{team_id}/image", response_model=schemas.TeamOut, tags=["Teams"])
async def upload_team_image(
                team_id: int,
                file: UploadFile = File(..., description="Team logo/avatar. JPEG, PNG, GIF or WEBP, max 5 MB."),
                db: Session = Depends(get_db), _ = Depends(get_current_user)):
    image_path = await save_team_image(file)
    return crud.update_team_image(db, team_id=team_id, image_path=image_path)

# Найти усі турніри користувача
@app.get("/members/{email}/tournaments")
def get_my_tournaments(
                email: str,
                db: Session = Depends(get_db), _ = Depends(get_current_user)):
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

# ── Rounds ───────────────────────────────────────────────────────

@app.post("/rounds/", tags=["Admin"])
def create_round(
                round_data: schemas.RoundCreate,
                db: Session = Depends(get_db), _ = Depends(require_organizer_or_admin)):
    
    return crud.create_round(db, round_data)

@app.post("/rounds/{round_id}/distribute", tags=["Admin"])
def distribute_works(
                round_id: int,
                db: Session = Depends(get_db), _ = Depends(require_organizer_or_admin)):
    
    return crud.distribute_submissions_to_jury(db, round_id)

# ── Submissions ──────────────────────────────────────────────────

@app.post("/submissions/", tags=["Teams"])
def submit_work(
                sub: schemas.SubmissionCreate, 
                db: Session = Depends(get_db), _ = Depends(get_current_user)):
    return crud.create_submission(db, sub)

# ── General ──────────────────────────────────────────────────────

@app.get("/")
def home():
    return {"status": "ok"}