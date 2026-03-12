from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models
from datetime import datetime, timedelta, timezone

def seed_tournament():
    db = SessionLocal()
    try:
        # Перевіряємо, чи є вже турнір з такою назвою, щоб не плодити дублікати
        tournament = db.query(models.Tournament).filter(models.Tournament.title == "Tech Cup 2026").first()
        
        if not tournament:
            print("Створюю тестовий турнір...")
            new_tournament = models.Tournament(
                title="Tech Cup 2026",
                description="Перший турнір в Івано-Франкiвську",
                status="registration",
                reg_start=datetime.now(timezone.utc) - timedelta(days=1),
                reg_end=datetime.now(timezone.utc) + timedelta(days=14),
                max_teams=10
            )
            db.add(new_tournament)
            db.commit()
            db.refresh(new_tournament)
            print(f"Турнір створено! ID: {new_tournament.id}")
        else:
            print(f"Турнір вже існує під ID: {tournament.id}")
            
    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_tournament()