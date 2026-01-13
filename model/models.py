from datetime import datetime

from markdown_it.rules_block import table
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

class Appointment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="user.id", index=True)
    patient_id: int = Field(foreign_key="user.id", index=True)
    appointment_time: datetime

class ClinicalNote(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)
    patient_id: int = Field(foreign_key="user.id")
    psychologist_id: int = Field(foreign_key="user.id")
    # appointment_id: int | None = Field(default=None, foreign_key="appointment.id")