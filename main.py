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
Base.metadata.create_all(bind=engine)

app = FastAPI(title="JobTracker Dashboard", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SYSTEM_PROMPT = """You are a job post parser. Extract the following fields from the LinkedIn job post and return ONLY valid JSON with these exact keys:
- job_role: job title/position
- company_name: company or organisation name
- job_location: city/state/country (if multiple cities listed, join them with comma)
- contact_email: email address if present
- apply_link: Extract ANY job application URL from the post. Look for URLs from these sites: naukri.com, linkedin.com, lnkd.in, indeed.com, internshala.com, foundit.in, shine.com, glassdoor.com, unstop.com, lever.co, greenhouse.io, workday.com, careers pages, or ANY url containing /jobs/, /careers/, /apply/, /job/. Also look for text like "Apply Now", "Apply Here", "Apply at", "Apply link", "Application link" followed by a URL. If multiple URLs found, prefer the direct apply/job URL over company website.
- salary: salary or compensation if mentioned (e.g. "₹6-12 LPA", "Not Disclosed", "$80k-$100k"). Return as short string. If "Not Disclosed" return that.
- job_description: full job description text including responsibilities, requirements and qualifications
If a field is not found, return null. Return ONLY raw JSON, no markdown, no explanation."""


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

    # Duplicate check
    existing = db.query(JobPost).filter(JobPost.raw_post == raw_post).first()
    if existing:
        added_on = existing.date_added.strftime('%b %d, %Y') if existing.date_added else 'a previous date'
        raise HTTPException(
            status_code=409,
            detail=f"Already added on {added_on} — '{existing.job_role or 'Unknown role'}'"
        )

    try:
        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": raw_post},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1500,
        )
        llm_response = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq API error: {str(e)}")

    try:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", llm_response, flags=re.MULTILINE).strip()
        extracted = json.loads(cleaned)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail=f"LLM returned invalid JSON: {llm_response[:300]}")

    # ── Regex fallback: if LLM missed the apply_link, find it ourselves ──
    if not extracted.get("apply_link"):
        job_site_pattern = re.compile(
            r'https?://(?:www\.)?(?:'
            r'naukri\.com/job-listings[^\s\)\"\'<>]+|'
            r'naukri\.com/[^\s\)\"\'<>]*job[^\s\)\"\'<>]*|'
            r'linkedin\.com/jobs/[^\s\)\"\'<>]+|'
            r'lnkd\.in/[^\s\)\"\'<>]+|'
            r'indeed\.com/[^\s\)\"\'<>]*job[^\s\)\"\'<>]*|'
            r'internshala\.com/[^\s\)\"\'<>]*job[^\s\)\"\'<>]*|'
            r'foundit\.in/[^\s\)\"\'<>]+|'
            r'unstop\.com/[^\s\)\"\'<>]+|'
            r'shine\.com/[^\s\)\"\'<>]+|'
            r'glassdoor\.com/job[^\s\)\"\'<>]+|'
            r'lever\.co/[^\s\)\"\'<>]+|'
            r'greenhouse\.io/[^\s\)\"\'<>]+|'
            r'[^\s\)\"\'<>]+/(?:jobs|careers|apply|job)/[^\s\)\"\'<>]+'
            r')',
            re.IGNORECASE
        )
        matches = job_site_pattern.findall(raw_post)
        # Filter out unwanted URLs
        ignore = ['youtube', 'instagram', 'twitter', 'facebook', 'openstreetmap', 'maptiler', 'oracle']
        clean_matches = [u for u in matches if not any(x in u.lower() for x in ignore)]
        if clean_matches:
            extracted["apply_link"] = clean_matches[0]

    job = JobPost(
        job_role=extracted.get("job_role"),
        company_name=extracted.get("company_name"),
        job_location=extracted.get("job_location"),
        contact_email=extracted.get("contact_email"),
        apply_link=extracted.get("apply_link"),
        salary=extracted.get("salary"),
        job_description=extracted.get("job_description"),
        raw_post=raw_post,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@app.get("/jobs", response_model=List[JobPostResponse])
def get_jobs(db: Session = Depends(get_db)):
    return db.query(JobPost).order_by(JobPost.date_added.desc()).all()


@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobPost).filter(JobPost.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"message": f"Job {job_id} deleted successfully"}
