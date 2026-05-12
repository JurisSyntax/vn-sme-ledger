# VN SME Ledger

An offline-first SME accounting application for the Vietnamese market, built in Python 3.13.

## Features
- Double-entry ledger with automated VAS (TT133) mapping
- Bilingual invoice generation (PDF)
- Offline-first architecture with optional cloud sync
- Analytics dashboard (Cash flow, tax forecast)
- Built for Windows as a standalone executable

## Setup
1. Create a virtual environment: `python -m venv .venv`
2. Activate the virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python main.py`

## Build
```bash
pyinstaller VN_SME_Ledger.spec --clean
```
