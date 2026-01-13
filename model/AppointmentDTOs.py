from datetime import datetime
from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    patient_id: int
    appointment_time: datetime

class AppointmentUpdate(BaseModel):
    appointment_time: datetime | None = None

class AppointmentDoctorView(BaseModel):
    id: int
    appointment_time: datetime
    patient_name: str
    patient_email: str

class AppointmentPatientView(BaseModel):
    id: int
    appointment_time: datetime
    doctor_name: str
