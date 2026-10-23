from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# SQLite (used in tests) does not support the PostgreSQL-style pool arguments.
# Detect the database type and configure appropriately.
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # StaticPool is required for in-memory SQLite with multiple threads (tests).
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # Bug #11 fix: explicit pool configuration for PostgreSQL.
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,          # number of permanent connections
        max_overflow=20,       # extra connections allowed under burst load
        pool_timeout=30,       # seconds to wait for a connection before raising
        pool_pre_ping=True,    # test connections before using (detects dropped connections)
        pool_recycle=1800,     # recycle connections every 30 min (avoids stale TCP)
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
