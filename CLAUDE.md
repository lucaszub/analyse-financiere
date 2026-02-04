# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal finance manager for tracking and categorizing bank transactions. Built with a **FastAPI backend** (SQLAlchemy + SQLite) and a **Streamlit frontend**. Currently supports Boursorama/BoursoBank CSV imports only.

## Commands

```bash
# Activate virtualenv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (creates tables, seeds categories from category.json, creates default accounts)
python init_data.py

# Start FastAPI backend (must be running for Streamlit to work)
uvicorn backend.main:app --reload

# Start Streamlit frontend (separate terminal)
streamlit run app.py
```

Both the backend (port 8000) and the Streamlit app must run simultaneously. The frontend calls the API at `http://localhost:8000`.

## Architecture

**Two-process architecture**: Streamlit frontend communicates with FastAPI backend via HTTP REST calls. They share the same SQLite database (`finance.db` at project root).

### Backend (`backend/`)
- `main.py` - FastAPI app with all endpoints. Uses `_enrich_transactions()` helper to flatten category relationship data into response dicts.
- `models.py` - SQLAlchemy models: `Account`, `Category` (3-level hierarchy: parent > sub > name), `Transaction`, `CategorizationRule`
- `schemas.py` - Pydantic schemas for request/response validation
- `crud.py` - Database operations. `apply_rules_to_uncategorized()` matches keywords against transaction descriptions/merchants.
- `database.py` - SQLite engine and session factory. DB path: `sqlite:///../finance.db` (relative to backend/)
- `services/import_service.py` - `BankCSVImporter`: parses Boursorama CSVs (semicolon-separated, UTF-8 BOM), auto-categorizes via 3-tier priority: user rules > Boursorama category mapping > keyword matching. Deduplicates via MD5 `import_id`.
- `category.json` - Category seed data with structure: `CatégoriesPrincipales > ParentCategory > SubCategory > [names]`

### Frontend
- `app.py` - Streamlit entrypoint with sidebar navigation between pages
- `pages/analyse.py` - Expense analysis page: date range picker, revenue/expense summary, 3-level collapsible accordion (parent > sub > transactions), inline recategorization dialog with optional rule creation
- `pages/import_csv.py` - CSV upload page with preview and import stats display

### Key Patterns
- Transaction deduplication uses MD5 hash of `dateOp + amount + label`
- Categories are a 3-level tree: `parent_category` > `sub_category` > `name`
- Internal transfers (Boursorama's "Mouvements internes débiteurs/créditeurs") are filtered out of analysis views
- `init_data.py` handles both initial setup and manual SQLite migrations (adding columns)

## Language

The codebase, comments, and UI are in **French**. Keep this convention when adding code or user-facing strings.
