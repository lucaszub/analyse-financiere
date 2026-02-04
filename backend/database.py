# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///../finance.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crée toutes les tables dans la base de données"""
    Base.metadata.create_all(bind=engine)
    print("✓ Base de données initialisée")

def get_db():
    """
    Dependency pour FastAPI qui fournit une session de base de données
    et la ferme automatiquement après utilisation
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()