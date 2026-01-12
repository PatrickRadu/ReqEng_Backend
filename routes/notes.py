from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select, col
from typing import List, Annotated
from datetime import datetime
from db.db import SessionDep
from model.models import ClinicalNote, User, NoteCreate, NoteUpdate, NoteRead
from auth import get_current_user 

router = APIRouter(prefix="/notes", tags=["Clinical Notes"])

def ensure_psychologist(current_user: User = Depends(get_current_user)) -> User:
    """
    Validation: Hard stop if the user is not a psychologist.
    Used as a dependency in all write-operations.
    """
    if current_user.role != "psychologist":
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
    if note.author_id != user.id:
        raise HTTPException(
            status_code=403, 
            detail="Access Denied: You can only modify notes you created."
        )

# create a clinical note
@router.post("/", response_model=NoteRead)
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
@router.get("/", response_model=List[NoteRead])
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
@router.get("/{note_id}", response_model=NoteRead)
def get_single_note(
    note_id: int, 
    session: SessionDep,
    current_user: User = Depends(ensure_psychologist)
):
    note = get_note_or_404(note_id, session)
    author = session.get(User, note.author_id)
    
    return NoteRead(
        **note.model_dump(),
        author_name=author.full_name if author else "Unknown"
    )

# update a clinical note
@router.put("/{note_id}", response_model=NoteRead)
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
    if update_data.is_confidential is not None:
        note.is_confidential = update_data.is_confidential
        
    note.updated_at = datetime.utcnow()
    
    session.add(note)
    session.commit()
    session.refresh(note)
    
    return NoteRead(
        **note.model_dump(), 
        author_name=current_user.full_name
    )

# delete a clinical note
@router.delete("/{note_id}")
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