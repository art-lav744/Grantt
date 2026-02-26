from passlib.context import CryptContext
import os
import uuid
from fastapi import UploadFile, HTTPException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_BASE_DIR = "uploads"
ALLOWED_EXTENSIONS = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE_MB = 5

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str):
    return pwd_context.hash(password)

async def _save_image(file: UploadFile, subfolder: str) -> str:
    """
    Core image upload helper. Validates type & size, then saves to
    uploads/<subfolder>/<uuid>.<ext>. Returns the relative file path.
    """
    if file.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Allowed: JPEG, PNG, GIF, WEBP."
        )

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    directory = os.path.join(UPLOAD_BASE_DIR, subfolder)
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, unique_filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    return file_path

# ── Public wrappers — one per entity ─────────────────────────────────────────

async def save_team_image(file: UploadFile) -> str:
    """Save a team logo/avatar to uploads/team_images/"""
    return await _save_image(file, "team_images")

async def save_profile_image(file: UploadFile) -> str:
    """Save a user profile photo to uploads/profile_images/"""
    return await _save_image(file, "profile_images")

async def save_tournament_image(file: UploadFile) -> str:
    """Save a tournament cover/banner to uploads/tournament_images/"""
    return await _save_image(file, "tournament_images")
