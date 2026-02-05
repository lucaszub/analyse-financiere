import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, Account


@pytest.fixture
def db():
    """Session SQLite en mémoire, recréée à chaque test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Compte par défaut
    account = Account(id=1, name="Boursorama", account_type="checking")
    session.add(account)
    session.commit()

    yield session

    session.close()
    engine.dispose()
