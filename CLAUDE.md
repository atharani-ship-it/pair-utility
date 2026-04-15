# CLAUDE.md

This repository contains the PAIR Utility Platform work.

## Scope
Work inside this project folder only.
Do not move files into a new src structure unless first approved.
Do not break the existing Streamlit demo app.

## Current known files
- `app.py` is the existing Streamlit demo app and must not be broken.
- `live_billing.py` exists and should be inspected before changes.
- Images and PDF assets already exist in this folder.

## Build intent
Add the new production-grade billing/backend structure carefully alongside the existing demo.

Priority order:
1. Billing accuracy
2. Payment tracking
3. Meter data ingestion
4. Monitoring

This is a billing-first system, not a BMS.

## Rules
- Do not modify the existing Streamlit demo unless explicitly approved.
- First inspect the current project structure and explain what should be kept.
- Propose the new folder/file structure before creating it.
- Show every file before moving to the next step.
- Do not invent fields or endpoints not in the master brief.
- Use Decimal for calculations, never float.
- Keep constants centralized in `constants.py`.

## Meter API essentials
- Base URL: `http://122.224.159.102:5305`
- client_id: `xintai`
- client_secret: `xintai`
- meterNo: `0025091007`

Required headers for all requests:
- `content-Type: application/json`
- `charset: UTF-8`
- `access_token: [token]`
- `client_id: xintai`
- `User-Agent: PostmanRuntime/7.32.3`

## Billing constants
- `RTH_CONVERSION_FACTOR = 3.51685`
- `RATE_PER_RTH = 0.95`
- `SERVICE_FEE = 85.00`
- `VAT_RATE = 0.05`
- `TOKEN_REFRESH_BUFFER = 300`

## Billing formula
- `usage_kwh = closing_read - opening_read`
- `usage_rth = usage_kwh / 3.51685`
- `cons_charge = round(usage_rth * 0.95, 2)`
- `subtotal = round(cons_charge + 85.00, 2)`
- `vat = round(subtotal * 0.05, 2)`
- `grand_total = round(subtotal + vat, 2)`

Validation test:
- opening = 28410
- closing = 62020
- expected grand_total = 9622.21