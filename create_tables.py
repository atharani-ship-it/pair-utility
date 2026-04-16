# create_tables.py
#
# Creates all database tables defined in models/ in one shot.
# Safe to run against an empty database — skips tables that already exist.
#
# Usage (from repository root, with DATABASE_URL set):
#   python create_tables.py

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from database import engine
from models.base import Base

# Import all models so their table definitions are registered with Base.metadata
# before create_all() is called. Order does not matter here.
import models.site
import models.tenant
import models.meter
import models.meter_assignment
import models.meter_reading

def create_tables():
    print(f"Connecting to: {engine.url}")
    print("Creating tables...")

    Base.metadata.create_all(bind=engine)

    tables = sorted(Base.metadata.tables.keys())
    for table in tables:
        print(f"  [OK] {table}")

    print(f"\n{len(tables)} table(s) ready.")

if __name__ == "__main__":
    create_tables()
