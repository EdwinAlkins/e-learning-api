import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.schemas.user import UserCreate, UserUpdate
from src.database import BaseModel
from src.crud.user import (
    create_user,
    get_user_by_email,
    get_user,
    get_users,
    update_user,
    delete_user,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    BaseModel.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_user(db_session):
    user = create_user(db_session, UserCreate(email="test@example.com", name="test"))
    assert user.email == "test@example.com"
    assert user.name == "test"


def test_get_user_by_email(db_session):
    user = create_user(db_session, UserCreate(email="test@example.com", name="test"))
    assert get_user_by_email(db_session, "test@example.com") == user


def test_get_user_by_id(db_session):
    user = create_user(db_session, UserCreate(email="test@example.com", name="test"))
    assert get_user(db_session, user.uid) == user


def test_get_user_by_name(db_session):
    user = create_user(db_session, UserCreate(email="test@example.com", name="test"))
    assert get_user(db_session, user.uid) == user


def test_get_users(db_session):
    user = create_user(db_session, UserCreate(email="test@example.com", name="test"))
    assert get_users(db_session) == [user]


def test_update_user(db_session):
    user = create_user(db_session, UserCreate(email="test@example.com", name="test"))
    updated_user = update_user(
        db_session, user.uid, UserUpdate(name="test2", email="test@example.com")
    )
    assert updated_user.name == "test2"
    assert updated_user.email == "test@example.com"


def test_delete_user(db_session):
    user = create_user(db_session, UserCreate(email="test@example.com", name="test"))
    assert delete_user(db_session, user.uid) == True
