import uuid

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import User
from .security import get_password_hash


def seed_users():
    db: Session = SessionLocal()
    try:
        # Check if users already exist
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Seeding admin user...")
            admin = User(
                id=uuid.uuid4(),
                username="admin",
                password_hash=get_password_hash("admin"),
                role="ADMIN"
            )
            db.add(admin)

        user = db.query(User).filter(User.username == "user").first()
        if not user:
            print("Seeding regular user...")
            user = User(
                id=uuid.uuid4(),
                username="user",
                password_hash=get_password_hash("user"),
                role="USER"
            )
            db.add(user)

        db.commit()
        print("Seeding completed successfully.")
    except Exception as e:
        print(f"Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # This will be called from main.py on startup or manually
    seed_users()
