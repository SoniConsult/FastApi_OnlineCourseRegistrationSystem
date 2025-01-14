from fastapi.testclient import TestClient
# Import your FastAPI app here
import models, schemas  # Import your models and schemas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch
from main import app
from db_config import Base
import db_config

from sqlalchemy.pool import StaticPool

# Set up a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:" 
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False},poolclass=StaticPool)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables in the test database (Ensure this is called before tests run)

client = TestClient(app)

# Dependency override to use the test database
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[db_config.get_db] = override_get_db


def test_add_course():
    print("hello")
    response = client.post("/admin/add_course", json={"title": "Test Course", "description": "Test Description", "available_slots": 10})
    print(response)
    assert response.status_code == 201
    assert response.json() == {"message": "Course added successfully"}
    
def test_view_courses():
    response = client.get("/admin/view_courses")
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    
def setup()->None:
     Base.metadata.create_all(bind=engine)
     session=SessionLocal()
     course=models.Course(title="Test Course", description="Test Description", available_slots=15)
     session.add(course)
     session.commit()
     session.close()
   

def teardown():
    Base.metadata.drop_all(bind=engine)
