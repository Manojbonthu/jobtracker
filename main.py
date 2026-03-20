import os
import json
import re
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from groq import Groq
from typing import List

from database import engine, get_db, Base
from models import JobPost
from schemas import JobPostCreate, JobPostResponse

load_dotenv()

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="JobTracker Dashboard", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SYSTEM_PROMPT = (
    "You are a job post parser. Extract the following fields from the LinkedIn job post "
    "and return ONLY valid JSON with these exact keys: job_role, job_location, contact_email, "
    "job_description. If a field is not found, return null for that field. "
    "Do not include any explanation or markdown, only raw JSON."
)


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


@app.post("/extract", response_model=JobPostResponse)
def extract_job(payload: JobPostCreate, db: Session = Depends(get_db)):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")

    raw_post = payload.raw_post.strip()
    if not raw_post:
        raise HTTPException(status_code=400, detail="raw_post cannot be empty")

    # Call Groq API
    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_post},
            ],
            model="llama-3.3-70b-versatile" ,# ✅ Active on Groq
            temperature=0.1,
            max_tokens=1024,
        )
        llm_response = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq API error: {str(e)}")

    # Parse JSON from LLM response
    try:
        # Strip markdown code fences if present
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", llm_response, flags=re.MULTILINE).strip()
        extracted = json.loads(cleaned)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=422,
            detail=f"LLM returned invalid JSON: {llm_response[:300]}",
        )

    # Save to database
    job = JobPost(
        job_role=extracted.get("job_role"),
        job_location=extracted.get("job_location"),
        contact_email=extracted.get("contact_email"),
        job_description=extracted.get("job_description"),
        raw_post=raw_post,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.get("/jobs", response_model=List[JobPostResponse])
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(JobPost).order_by(JobPost.date_added.desc()).all()
    return jobs


@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobPost).filter(JobPost.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted successfully"}
