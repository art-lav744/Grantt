import io
from PIL import Image

from passlib.context import CryptContext
import os
import uuid
from fastapi import UploadFile, HTTPException

from jose import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "secret-token-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 години

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_BASE_DIR = "uploads"
ALLOWED_EXTENSIONS = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE_MB = 5


# ── Hash ────────────────────────────────────────────────────────

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str):
    return pwd_context.hash(password)

def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }# Шифруємо та повертаємо JWT токен з корисним навантаженням (user_id, role, exp) та секретним ключем
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])# Декодуємо та перевіряємо JWT токен, повертаючи корисне навантаження (payload) або викликаючи помилку при невірному токені
    except Exception:
        raise HTTPException(status_code=401, detail="Unvalid token")


# ── Image ───────────────────────────────────────────────────────

def _process_image(contents: bytes, target_size: int = 400) -> bytes:
    """Відкриває зображення, обрізає до квадрату, змінює розмір і зберігає у JPEG форматі."""

    # Перевірка на пошкодження файлу
    try:
        image = Image.open(io.BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=400, detail="File is corrupted or not a valid image.")
    
    # RGB 
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    
    # Обрізає до квадрату
    w, h = image.size
    min_side = min(w, h)
    left = (w - min_side) // 2
    top = (h - min_side) // 2
    image = image.crop((left, top, left + min_side, top + min_side))
    
    # Змінює розмір
    image = image.resize((target_size, target_size), Image.LANCZOS)
    
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=85)
    return output.getvalue()


# Напишіть process=False якщо виклик для фото турніру а не профілю чи команди
async def _save_image(file: UploadFile, subfolder: str, process: bool = True) -> str:
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type '{file.content_type}'.")
    # Перевірка на порожній файл та розмір файлу
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="File is empty.")
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File too large ({size_mb:.1f} MB). Max {MAX_FILE_SIZE_MB} MB.")

    if process:
        contents = _process_image(contents)
    else:
        # Додаткова перевірка на пошкодження файлу, якщо не обробляємо його (наприклад, для фото турніру)
        try:
            Image.open(io.BytesIO(contents)).verify()
        except Exception:
            raise HTTPException(status_code=400, detail="File is corrupted or not a valid image.")

    ext = "jpg" if process else (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg")
    file_path = os.path.join(UPLOAD_BASE_DIR, subfolder, f"{uuid.uuid4().hex}.{ext}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(contents)

    return file_path

# ── Public wrappers

async def save_team_image(file: UploadFile) -> str:
    """Save a team logo/avatar to uploads/team_images/"""
    return await _save_image(file, "team_images")

async def save_profile_image(file: UploadFile) -> str:
    """Save a user profile photo to uploads/profile_images/"""
    return await _save_image(file, "profile_images")

async def save_tournament_image(file: UploadFile) -> str:
    """Save a tournament cover/banner to uploads/tournament_images/"""
    return await _save_image(file, "tournament_images", process=False)
