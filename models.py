from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from database import Base


class JobPost(Base):
    __tablename__ = "job_posts"

    id = Column(Integer, primary_key=True, index=True)
    job_role = Column(String(255), nullable=True)
    job_location = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=True)
    raw_post = Column(Text, nullable=True)
    date_added = Column(TIMESTAMP, server_default=func.now())
