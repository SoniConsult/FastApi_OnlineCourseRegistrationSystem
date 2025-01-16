from typing import Optional
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str 

class CourseCreate(BaseModel):
    title: str
    description: str
    available_slots: int


class UserOut(BaseModel):
    name: str
    email: str
    role: str

    class Config:
        orm_mode = True


class CourseOut(BaseModel):
    id: int
    title: str
    description: str
    available_slots: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email:Optional[str]=None
    
    
class login(BaseModel):
      email:str
      password:str
      
      
    