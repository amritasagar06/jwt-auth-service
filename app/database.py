from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# 1. Create the engine
engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)

# 2. Create the Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Define Base HERE (Models will import this)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # We import models HERE inside the function.
    # This prevents the circular import error at startup.
    from app import models 
    Base.metadata.create_all(bind=engine)