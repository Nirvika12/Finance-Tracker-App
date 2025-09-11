from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

db_config = 'sqlite:///finance_tracker.db'
engine = create_engine(db_config, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

Base.metadata.create_all(bind=engine)


# Dependency for FastAPI endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
