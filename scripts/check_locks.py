
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DATABASE_URL = "postgresql://user:password@localhost:5432/pricing_db"

def check_locked_prices():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        result = session.execute(text("SELECT id, name, locked, locked_by_saga_id FROM prices WHERE locked = true"))
        locked_prices = result.fetchall()
        if not locked_prices:
            print("No prices are currently locked.")
        else:
            print(f"Found {len(locked_prices)} locked prices:")
            for p in locked_prices:
                print(f"  - ID: {p.id}, Name: {p.name}, Saga ID: {p.locked_by_saga_id}")
    finally:
        session.close()

if __name__ == "__main__":
    check_locked_prices()
