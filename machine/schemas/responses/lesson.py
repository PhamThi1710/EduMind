from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    name: str
    type: str 
    document_url: str
    description: str
    course_id: UUID

    class Config:
        from_attributes = True

class GetDocumentResponse(BaseModel):
    id: UUID
    name: str
    type: str 
    document_url: str
    description: str

    class Config:
        from_attributes = True
