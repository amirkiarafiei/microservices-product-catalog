from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..config import settings

DATABASE_URL = settings.DATABASE_URL

# Create engine only if DATABASE_URL is set, to avoid errors during discovery/import
# if DATABASE_URL will be overridden by fixtures anyway.
# However, many things depend on 'engine' and 'SessionLocal' at module level.
# For now, let's just make sure it doesn't fail if DATABASE_URL is None, 
# although create_engine(None) will fail.

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # Fallback or placeholder to avoid module-level import errors
    engine = None
    SessionLocal = None

Base = declarative_base()

def get_db():
    if SessionLocal is None:
        raise RuntimeError("SessionLocal is not initialized. Check DATABASE_URL.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
