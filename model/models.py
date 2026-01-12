
from datetime import datetime
from sqlmodel import SQLModel,Field
from pydantic import BaseModel, ConfigDict, EmailStr
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str =Field(index=True, unique=True)
    full_name: str 
    role: str = Field(default="patient")
    hashed_password: str

class ClinicalNote(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)
    patient_id: int = Field(foreign_key="user.id")
    psychologist_id: int = Field(foreign_key="user.id")
    # appointment_id: int | None = Field(default=None, foreign_key="appointment.id")


class NoteCreate(BaseModel):
    patient_id: int
    content: str
    # is_confidential: bool = False  

class NoteUpdate(BaseModel):
    content: str | None = None
    # is_confidential: bool | None = None


class NoteRead(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime | None
    author_name: str  
    # is_confidential: bool
    model_config = ConfigDict(from_attributes=True)