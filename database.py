import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/instatranscript.db")

# Fix Render's postgres:// prefix if postgresql is used
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes all database tables and ensures schema migrations are applied."""
    import models  # Ensure models are registered
    Base.metadata.create_all(bind=engine)

    # Safe column migration for SQLite/Postgres if existing tables lack new Clerk fields
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check existing columns in users table
            if DATABASE_URL.startswith("sqlite"):
                cursor = conn.execute(text("PRAGMA table_info(users)"))
                existing_cols = [row[1] for row in cursor.fetchall()]
                if "clerk_id" not in existing_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN clerk_id VARCHAR(255)"))
                    conn.commit()
                if "avatar_url" not in existing_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
                    conn.commit()
            else:
                # PostgreSQL migration
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS clerk_id VARCHAR(255)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)"))
                conn.commit()
    except Exception as e:
        # Schema is either fresh or already has columns
        pass

