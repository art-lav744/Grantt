from app.database import SessionLocal
from app import models
from app.utils import hash_password

def create_admin():
    db = SessionLocal()
    try:
        # Перевіряємо, чи є вже такий адмін
        admin_email = "admin@test.com"
        db_admin = db.query(models.User).filter(models.User.email == admin_email).first()

        if not db_admin:
            print(f"Створюю адміністратора: {admin_email}...")
            new_admin = models.User(
                email=admin_email,
                nickname="BigAdmin",
                hashed_password=hash_password("admin123"), # Пароль буде захешовано
                role="admin"
            )
            db.add(new_admin)
            db.commit()
            print("Адміністратора успішно створено!")
            print("Логін: admin@test.com")
            print("Пароль: admin123")
        else:
            print(f"Адміністратор {admin_email} вже існує.")
    except Exception as e:
        print(f"Помилка: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()