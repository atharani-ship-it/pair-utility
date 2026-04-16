# seed.py
#
# One-time setup script: creates the Site and Meter records for the
# Abu Dhabi Gate City installation.
#
# Safe to run multiple times — checks for existing records before inserting.
#
# Usage (from repository root):
#   python seed.py

# Note: requires DATABASE_URL to be set in the environment.

import os
import sys

# Ensure project root is on the path when run directly.
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal
from models import Site, Meter  # triggers Base.metadata registration


def seed():
    db = SessionLocal()
    try:
        # ── Site ──────────────────────────────────────────────────────────────
        site = db.query(Site).filter(Site.site_code == "ADGC-001").first()

        if site:
            print(f"[SKIP] Site already exists: site_id={site.id}")
        else:
            site = Site(
                site_code="ADGC-001",
                name="Abu Dhabi Gate City",
                city="Abu Dhabi",
                country="UAE",
                is_active=True,
            )
            db.add(site)
            db.flush()  # assigns site.id before we reference it below
            print(f"[OK]   Site created:  site_id={site.id}")

        # ── Meter ─────────────────────────────────────────────────────────────
        meter = (
            db.query(Meter)
            .filter(Meter.meter_number == "0025091007")
            .first()
        )

        if meter:
            print(f"[SKIP] Meter already exists: meter_id={meter.id}")
        else:
            meter = Meter(
                site_id=            site.id,
                meter_number=       "0025091007",
                meter_size_dn=      "DN50",
                communication_mode= "MBUS",
                status=             "active",
            )
            db.add(meter)
            db.flush()
            print(f"[OK]   Meter created: meter_id={meter.id}")

        db.commit()

        # ── Summary ───────────────────────────────────────────────────────────
        print()
        print("── Seed complete ──────────────────────────────────────")
        print(f"  site_id  = {site.id}")
        print(f"  meter_id = {meter.id}")
        print("───────────────────────────────────────────────────────")
        print()
        print("Use meter_id above when calling ingest_latest_reading().")

    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Seed failed, rolled back. Reason: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
