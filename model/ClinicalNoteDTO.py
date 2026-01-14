from datetime import datetime
from pydantic import BaseModel, ConfigDict


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
