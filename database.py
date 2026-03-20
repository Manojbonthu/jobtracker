import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:YOURPASSWORD@db.xxxx.supabase.co:5432/postgres"
)

if "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

def create_tables_if_not_exists(engine):
    create_sql = """
    CREATE TABLE IF NOT EXISTS job_posts (
        id              SERIAL PRIMARY KEY,
        job_role        VARCHAR(255),
        company_name    VARCHAR(255),
        job_location    VARCHAR(255),
        contact_email   VARCHAR(255),
        apply_link      TEXT,
        salary          VARCHAR(255),
        job_description TEXT,
        raw_post        TEXT,
        date_added      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    migrations = [
        "ALTER TABLE job_posts ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);",
        "ALTER TABLE job_posts ADD COLUMN IF NOT EXISTS apply_link TEXT;",
        "ALTER TABLE job_posts ADD COLUMN IF NOT EXISTS salary VARCHAR(255);",
    ]
    try:
        with engine.connect() as conn:
            conn.execute(text(create_sql))
            for m in migrations:
                conn.execute(text(m))
            conn.commit()
        print("[DB] Supabase connected. Table 'job_posts' is ready.")
    except Exception as e:
        print(f"[DB] Error: {e}")
        raise

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"sslmode": "require"},
)

create_tables_if_not_exists(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
