# 💼 JobTracker Dashboard

An AI-powered job tracking dashboard that extracts structured data from LinkedIn job posts using LLM and stores them in a PostgreSQL database.

![JobTracker Dashboard](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)

---

## ✨ Features

- **Paste LinkedIn post** → AI extracts job role, location, email, description automatically
- **Skills detection** — auto-detects tech skills, soft skills, experience from description
- **Expandable rows** — click Details to see full description, skills chips, and original post
- **Copy buttons** — copy email or full raw post in one click
- **Real-time search** — filter jobs by role or location instantly
- **Supabase PostgreSQL** — cloud database, free tier, no local DB needed

---

## 🗂️ Project Structure

```
jobtracker/
├── main.py           # FastAPI app — all API endpoints
├── database.py       # SQLAlchemy + Supabase connection
├── models.py         # ORM model for job_posts table
├── schemas.py        # Pydantic request/response schemas
├── requirements.txt  # Python dependencies
├── render.yaml       # Render.com deployment config
├── .gitignore        # Excludes .env and cache files
├── .env              # ⚠️ NOT committed — your secrets go here
└── static/
    └── index.html    # Single-page frontend (no framework)
```

---

## 🚀 Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/jobtracker.git
cd jobtracker
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres?sslmode=require
```

### 4. Run the app
```bash
uvicorn main:app --reload --port 8000
```

### 5. Open in browser
```
http://localhost:8000
```

---

## 🌐 Deploy to Render (Free)

See full deployment steps below in the [Deployment](#deployment) section.

---

## 🔑 Environment Variables

| Variable | Description | Where to get it |
|---|---|---|
| `GROQ_API_KEY` | Groq LLM API key | [console.groq.com](https://console.groq.com) |
| `DATABASE_URL` | PostgreSQL connection string | Supabase → Settings → Database |

---

## 🗄️ Database Schema

```sql
CREATE TABLE job_posts (
    id              SERIAL PRIMARY KEY,
    job_role        VARCHAR(255),
    job_location    VARCHAR(255),
    contact_email   VARCHAR(255),
    job_description TEXT,
    raw_post        TEXT,
    date_added      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/extract` | Extract job info from raw post via LLM |
| `GET` | `/jobs` | Get all saved jobs |
| `DELETE` | `/jobs/{id}` | Delete a job by ID |

---

## 🛠️ Tech Stack

- **Backend** — FastAPI, SQLAlchemy, Psycopg2
- **LLM** — Groq API (`llama-3.3-70b-versatile`)
- **Database** — PostgreSQL via Supabase
- **Frontend** — Vanilla HTML/CSS/JavaScript
- **Hosting** — Render.com

---

## 📄 License

MIT License — free to use and modify.
