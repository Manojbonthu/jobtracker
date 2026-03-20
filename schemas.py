from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobPostBase(BaseModel):
    job_role: Optional[str] = None
    job_location: Optional[str] = None
    contact_email: Optional[str] = None
    job_description: Optional[str] = None
    raw_post: Optional[str] = None


class JobPostCreate(BaseModel):
    raw_post: str


class JobPostResponse(JobPostBase):
    id: int
    date_added: Optional[datetime] = None

    class Config:
        from_attributes = True
