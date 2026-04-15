# database.py
#
# Database engine and session configuration for the PAIR Utility Platform.
# DATABASE_URL is read from the environment. Set it before running:
#   export DATABASE_URL="postgresql://user:password@host:5432/pair_utility"

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/pair_utility",
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
