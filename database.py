import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Manoj%40bonthu9@db.nsxwljvxuitpffntvnfo.supabase.co:5432/postgres?sslmode=require"
)
# Supabase requires SSL — make sure sslmode=require is in the URL
if "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"


def create_tables_if_not_exists(engine):
    """
    Creates the job_posts table in Supabase if it doesn't already exist.
    Supabase manages the database itself — we only need to create the table.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS job_posts (
        id              SERIAL PRIMARY KEY,
        job_role        VARCHAR(255),
        job_location    VARCHAR(255),
        contact_email   VARCHAR(255),
        job_description TEXT,
        raw_post        TEXT,
        date_added      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        print("[DB] Supabase connected. Table 'job_posts' is ready.")
    except Exception as e:
        print(f"[DB] Error creating table: {e}")
        raise


# ── Connect to Supabase & set up table ───────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # check connection is alive before using
    pool_size=5,               # max connections in pool
    max_overflow=10,           # extra connections allowed under load
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
