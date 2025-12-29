
from sqlmodel import SQLModel,Field
from pydantic import BaseModel, EmailStr
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str =Field(index=True, unique=True)
    full_name: str 
    role: str = Field(default="patient")
    hashed_password: str
    