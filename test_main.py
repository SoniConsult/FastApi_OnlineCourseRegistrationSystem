import pytest
from fastapi.testclient import TestClient
from main import app, create_access_token
from db_config import get_db
from models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import status


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture()
def test_user():
    # Create a test user
    db = SessionLocal()
    user = User(name="test_user", email="testuser@example.com", password="testpassword", role="User")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture()
def admin_user():
    db = SessionLocal()
    user = User(name="admin_user", email="adminuser@example.com", password="adminpassword", role="Admin")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture()
def valid_token(test_user):
    token = create_access_token(data={"sub": test_user.email, "role": test_user.role})
    return token

@pytest.fixture()
def admin_token(admin_user):
    token = create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
    return token


def test_register_user():
    response = client.post("/user/register", json={"name": "new_user", "email": "newuser@example.com", "password": "password", "role": "User"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "User Registered Successfully"}

def test_login_user(test_user):
    response = client.post("/user/login", json={"email": test_user.email, "password": "testpassword"})
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

def test_add_course(admin_token):
    course_data = {"title": "Python 101", "description": "Intro to Python", "available_slots": 30}
    response = client.post("/admin/add_course", json=course_data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Course added successfully"}
