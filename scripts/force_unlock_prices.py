
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql://user:password@localhost:5432/pricing_db"

def unlock_all_prices():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        result = session.execute(text("UPDATE prices SET locked = false, locked_by_saga_id = NULL WHERE locked = true"))
        session.commit()
        print(f"Successfully unlocked {result.rowcount} prices.")
    finally:
        session.close()

if __name__ == "__main__":
    unlock_all_prices()
