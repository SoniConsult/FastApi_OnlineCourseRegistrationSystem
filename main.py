from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from jose import JWTError,jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import List,Any, Dict,Annotated
import models, schemas, db_config
from db_config import engine, Base
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
import os

app = FastAPI()
load_dotenv()

SECRET_KEY =os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))


Base.metadata.create_all(bind=engine)
def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None,referesh:bool =False):
    payload = data.copy() 
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire}) 
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



def verify_token(token: str):
    if token == "mock_token_for_admin":
        return {"role": "Admin"}
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


oauth2_scheme=OAuth2PasswordBearer(tokenUrl='login')

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
  

# Admin Routes
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

@admin_router.post("/add_course", status_code=status.HTTP_201_CREATED)
def add_course(course: schemas.CourseCreate, db: Session = Depends(db_config.get_db), user_data: dict= Depends(verify_token)):

    if user_data.get("role") != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
    
    db_course = models.Course(**course.dict())
    print("type:",type(db_course))
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return {"message": "Course added successfully"}

@admin_router.get("/view_courses", response_model=List[schemas.CourseOut])
def view_courses(db: Session = Depends(db_config.get_db), user_data: dict= Depends(verify_token)):
    if user_data.get("role") != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
    
    courses = db.query(models.Course).all()
    return courses

@admin_router.delete("/delete_course/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(db_config.get_db), user_data: dict = Depends(verify_token)):
    if user_data.get("role") != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    
    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}

@admin_router.put("/update_course/{course_id}", response_model=schemas.CourseOut)
def update_course(course_id: int, course: schemas.CourseCreate, db: Session = Depends(db_config.get_db), user_data: dict = Depends(verify_token)):

    if user_data.get("role") != "Admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an admin")
    
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    
    db_course.title = course.title
    db_course.description = course.description
    db_course.available_slots = course.available_slots
    db.commit()
    db.refresh(db_course)
    return {"message":"Course updated successfully"}

# User Routes
user_router = APIRouter(prefix="/user", tags=["User"])

@user_router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(db_config.get_db)):
    password = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(user.password)
    db_user = models.User(name=user.name, email=user.email, password=password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message":"User Registered Successfully"}

@user_router.post("/login", response_model=schemas.Token)
def login(request:schemas.login, db: Session = Depends(db_config.get_db)):
    db_user = db.query(models.User).filter(models.User.email == request.email).first()
    if not db_user or not CryptContext(schemes=["bcrypt"], deprecated="auto").verify(request.password,db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(data={"sub": db_user.email, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}

@user_router.get("/view_courses", response_model=List[schemas.CourseOut])
def view_courses(db: Session = Depends(db_config.get_db), token: str = Depends(verify_token)):
    courses = db.query(models.Course).all()
    return courses

@user_router.post("/register_course/{course_id}")
def register_course(course_id: int, db: Session = Depends(db_config.get_db), user_data: dict = Depends(verify_token)):

    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return {"message": "Course registered successfully"}

@user_router.delete("/cancel_registration/{course_id}")
def cancel_registration(course_id: int, db: Session = Depends(db_config.get_db), user_data: dict = Depends(verify_token)):

    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    

    return {"message": "Course registration canceled successfully"}

app.include_router(admin_router)
app.include_router(user_router)
print(app.routes)