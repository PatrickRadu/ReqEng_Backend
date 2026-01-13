

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from pwdlib import PasswordHash
from sqlmodel import select, col
from datetime import datetime, timedelta
import jwt
from fastapi.middleware.cors import CORSMiddleware
from db.db import init_db, SessionDep
from model.models import User, UserLogin, Appointment, ClinicalNote
from model.AppointmentDTOs import (
AppointmentCreate,
AppointmentUpdate,
AppointmentDoctorView,
AppointmentPatientView
)
from model.ClinicalNoteDTO import (
NoteCreate,
NoteRead,
NoteUpdate)
from config import settings
from typing import List
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "patient"

password_hash = PasswordHash.recommended()



def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: SessionDep = None):
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_role(role: str):
    def checker(user: User = Depends(get_current_user)):
        if user.role != role:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user
    return checker

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/register")
def register_user(request: RegisterRequest, session: SessionDep):
    # Check if user already exists
    existing_user = session.exec(select(User).where(User.email == request.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = get_password_hash(request.password)
    new_user = User(
        email=request.email,
        full_name=request.full_name,
        role=request.role,
        hashed_password=hashed_password
    )
    
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role
        }
    }

@app.post("/login")
def login(request: UserLogin, session: SessionDep):
    # Find user by email
    user = session.exec(select(User).where(User.email == request.email)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "role": user.role}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }

@app.get("/hello")
def hello_world(current_user: UserLogin = Depends(get_current_user)):
    return {
        "message": f"Hello, {current_user.full_name}!",
        "user": {
            "email": current_user.email,
            "role": current_user.role
        }
    }

@app.post("/appointments")
def create_appointment(
    request: AppointmentCreate,
    session: SessionDep,
    doctor: User = Depends(require_role("doctor"))
):
    patient = session.get(User, request.patient_id)
    if not patient or patient.role != "patient":
        raise HTTPException(status_code=404, detail="Patient not found")

    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=request.patient_id,
        appointment_time=request.appointment_time
    )

    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    return {"appointment_id": appointment.id}

@app.put("/appointments/{appointment_id}")
def update_appointment(
    appointment_id: int,
    request: AppointmentUpdate,
    session: SessionDep,
    doctor: User = Depends(require_role("doctor"))
):
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Not your appointment")

    if request.appointment_time:
        appointment.appointment_time = request.appointment_time

    session.commit()
    return {"message": "Appointment updated"}

@app.delete("/appointments/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    session: SessionDep,
    doctor: User = Depends(require_role("doctor"))
):
    appointment = session.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Not your appointment")

    session.delete(appointment)
    session.commit()
    return {"message": "Appointment deleted"}

@app.get("/appointments/doctor", response_model=list[AppointmentDoctorView])
def doctor_appointments(
    session: SessionDep,
    doctor: User = Depends(require_role("doctor"))
):
    appointments = session.exec(
        select(Appointment).where(Appointment.doctor_id == doctor.id)
    ).all()

    return [
        AppointmentDoctorView(
            id=a.id,
            appointment_time=a.appointment_time,
            patient_name=session.get(User, a.patient_id).full_name,
            patient_email=session.get(User, a.patient_id).email
        )
        for a in appointments
    ]


@app.get("/appointments/patient", response_model=list[AppointmentPatientView])
def patient_appointments(
    session: SessionDep,
    patient: User = Depends(require_role("patient"))
):
    appointments = session.exec(
        select(Appointment).where(Appointment.patient_id == patient.id)
    ).all()

    return [
        AppointmentPatientView(
            id=a.id,
            appointment_time=a.appointment_time,
            doctor_name=session.get(User, a.doctor_id).full_name
        )
        for a in appointments
    ]

# clinical notes logic
def ensure_psychologist(current_user: User = Depends(get_current_user)) -> User:
    """
    Validation: Hard stop if the user is not a psychologist.
    Used as a dependency in all write-operations.
    """
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=403, 
            detail="Access Forbidden: Only clinical staff can manage notes."
        )
    return current_user

def get_note_or_404(note_id: int, session: SessionDep) -> ClinicalNote:
    """
    Validation: helper to fetch note or throw 404.
    """
    note = session.get(ClinicalNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Clinical note not found")
    return note

def validate_author_ownership(note: ClinicalNote, user: User):
    """
    Validation: Ensure only the original author can edit/delete.
    """
    if note.psychologist_id != user.id:
        raise HTTPException(
            status_code=403, 
            detail="Access Denied: You can only modify notes you created."
        )

# create a clinical note
@app.post("/notes/",tags =["Clinical Notes"], response_model=NoteRead)
def create_clinical_note(
    note_data: NoteCreate,
    session: SessionDep,
    current_user: User = Depends(ensure_psychologist)
):
   
    patient = session.get(User, note_data.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient ID not found")
    
    
    if patient.role != "patient":
        raise HTTPException(status_code=400, detail="Target user is not a patient")

    
    new_note = ClinicalNote(
        content=note_data.content,
        patient_id=note_data.patient_id,
        psychologist_id=current_user.id,
        # is_confidential=note_data.is_confidential,
        created_at=datetime.now()
    )
    
    session.add(new_note)
    session.commit()
    session.refresh(new_note)
    
    
    return NoteRead(
        **new_note.model_dump(), 
        author_name=current_user.full_name
    )

# get list of notes with filters
@app.get("/notes/",tags =["Clinical Notes"], response_model=List[NoteRead])
def get_notes(
    session: SessionDep,
    current_user: User = Depends(ensure_psychologist),
    patient_id: int | None = Query(None, description="Filter by Patient ID"),
    search: str | None = Query(None, description="Search text content"),
    limit: int = 20,
    offset: int = 0
):
    """
    Fetch notes. 
    - If patient_id is provided -> Shows patient history.
    - If search is provided -> Global search for the doctor.
    """
    query = select(ClinicalNote)

    # Filter By Patient
    if patient_id:
        query = query.where(ClinicalNote.patient_id == patient_id)
    
    # Filter By Search Text
    if search:
        query = query.where(col(ClinicalNote.content).icontains(search))

    # Optimization: Join with User table to get Author Names efficiently
    # (For a prototype, we can skip the complex join and just loop, 
    # but strictly speaking a JOIN is better here. Let's keep it simple for now).
    
    # Sort: Newest first
    query = query.order_by(ClinicalNote.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    notes = session.exec(query).all()
    
    results = []
    for note in notes:
        author = session.get(User, note.psychologist_id)
        results.append(NoteRead(
            **note.model_dump(),
            author_name=author.full_name if author else "Unknown"
        ))
        
    return results

# get a single note by ID
@app.get("/{note_id}",tags =["Clinical Notes"], response_model=NoteRead)
def get_single_note(
    note_id: int, 
    session: SessionDep,
    current_user: User = Depends(ensure_psychologist)
):
    note = get_note_or_404(note_id, session)
    author = session.get(User, note.psychologist_id)
    
    return NoteRead(
        **note.model_dump(),
        author_name=author.full_name if author else "Unknown"
    )

# update a clinical note
@app.put("/{note_id}",tags =["Clinical Notes"], response_model=NoteRead)
def update_note(
    note_id: int,
    update_data: NoteUpdate,
    session: SessionDep,
    current_user: User = Depends(ensure_psychologist)
):
    note = get_note_or_404(note_id, session)
    validate_author_ownership(note, current_user)
    
    # Only update fields that were actually sent
    if update_data.content is not None:
        note.content = update_data.content
    # if update_data.is_confidential is not None:
    #     note.is_confidential = update_data.is_confidential
        
    note.updated_at = datetime.now()
    
    session.add(note)
    session.commit()
    session.refresh(note)
    
    return NoteRead(
        **note.model_dump(), 
        author_name=current_user.full_name
    )

# delete a clinical note
@app.delete("/{note_id}",tags =["Clinical Notes"])
def delete_note(
    note_id: int,
    session: SessionDep,
    current_user: User = Depends(ensure_psychologist)
):
    note = get_note_or_404(note_id, session)
    validate_author_ownership(note, current_user)
    
    session.delete(note)
    session.commit()
    
    return {"message": "Clinical note deleted successfully"}

