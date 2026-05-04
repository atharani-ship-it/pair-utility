# PAIR Utility Project - Current Status

## What exists and works
- Streamlit demo app (app.py)
- Billing system (billing/)
- Data ingestion system (ingestion/)
- Meter handling (meter/)
- Database models (models/)
- Supabase / database connection (database.py)
- Table creation (create_tables.py)
- Seed data (seed.py)
- Invoice generation working (PDF output exists)
- Tests exist (tests/)
- Astro landing page project exists in 02_LANDING_PAGE

## Landing page direction
- The PAIR landing page is being built in 02_LANDING_PAGE.
- Current frontend decision: use plain Astro + custom CSS, not Tailwind.
- Position PAIR as a premium UAE utility operator for chilled water infrastructure, BTU metering, tenant billing, monitoring, and reporting.
- The platform should be described as an operational system, not SaaS or startup software.
- Current UI status: a first hero draft exists in 02_LANDING_PAGE/src/pages/index.astro, but it is not final.
- Logo path works from 02_LANDING_PAGE/public/pair_logo.png, but the logo asset needs proper treatment later.

## Locked landing page structure
1. Hero
2. Problem
3. Solution
4. How It Works
5. Features
6. Built for Commercial Properties
7. Platform Proof
8. Operator Model
9. CTA

## Landing page rules
- No tariff values
- No revenue share language
- No past project claims
- No SaaS/startup language
- Platform = operational system
- Premium UAE utility operator tone
- Chilled water infrastructure / BTU metering / billing operations focus

## What is in progress
- Company profile (content completed, formatting pending)
- System restructuring into AI-compatible project layout
- Brain folder and documentation system
- Landing page content and design refinement

## What is blocked and why
- No centralized documentation for backend system yet
- No clear handover file for AI tools (Claude/Codex)
- Landing page needs full build beyond the first hero draft

## Next action
- Create backend handover document
- Set up .env and secrets handling
- Build the locked 9-section PAIR landing page in 02_LANDING_PAGE using plain Astro + custom CSS

## Do not touch
- billing/
- ingestion/
- meter/
- models/
- app.py
- database.py
