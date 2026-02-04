# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal finance manager for tracking and categorizing bank transactions. Built with a **FastAPI backend** (SQLAlchemy + SQLite) and a **React frontend** (Vite + TypeScript + Tailwind CSS). Currently supports Boursorama/BoursoBank CSV imports only.

## Commands

```bash
# Activate virtualenv (backend)
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Initialize database (creates tables, seeds categories from category.json, creates default accounts)
python init_data.py

# Start FastAPI backend (port 8000)
uvicorn backend.main:app --reload

# Install frontend dependencies (first time only)
cd frontend && npm install

# Start React frontend (port 5173, separate terminal)
cd frontend && npm run dev
```

Both the backend (port 8000) and the React dev server (port 5173) must run simultaneously. The Vite dev server proxies `/api/*` requests to the backend at `http://localhost:8000`.

## Architecture

**Two-process architecture**: React frontend communicates with FastAPI backend via HTTP REST calls through a Vite proxy. They share the same SQLite database (`finance.db` at project root).

### Backend (`backend/`)
- `main.py` - FastAPI app with all endpoints. Uses `_enrich_transactions()` helper to flatten category relationship data into response dicts.
- `models.py` - SQLAlchemy models: `Account`, `Category` (3-level hierarchy: parent > sub > name), `Transaction`, `CategorizationRule`
- `schemas.py` - Pydantic schemas for request/response validation
- `crud.py` - Database operations. `apply_rules_to_uncategorized()` matches keywords against transaction descriptions/merchants.
- `database.py` - SQLite engine and session factory. DB path: `sqlite:///../finance.db` (relative to backend/)
- `services/import_service.py` - `BankCSVImporter`: parses Boursorama CSVs (semicolon-separated, UTF-8 BOM), auto-categorizes via 3-tier priority: user rules > Boursorama category mapping > keyword matching. Deduplicates via MD5 `import_id`.
- `category.json` - Category seed data with structure: `CatégoriesPrincipales > ParentCategory > SubCategory > [names]`

### Frontend (`frontend/`)
- **Stack**: Vite + React 19 + TypeScript + Tailwind CSS v4 + Recharts + React Router
- **Dark theme** inspired by Finary (background `#0a0a0a`, accent doré `#c8a254`)
- `src/api/client.ts` - Axios instance wrapping all backend API calls (proxied via `/api`)
- `src/types/index.ts` - TypeScript interfaces mirroring Pydantic schemas
- `src/components/Layout.tsx` + `Sidebar.tsx` - App shell with sidebar navigation
- `src/pages/Budget.tsx` - Main dashboard: date range picker, summary cards, cashflow bar chart, distribution donut, 3-level category accordion, recategorization modal
- `src/pages/Import.tsx` - CSV upload with drag & drop, preview table, import stats, rule re-application

### Key Patterns
- Transaction deduplication uses MD5 hash of `dateOp + amount + label`
- Categories are a 3-level tree: `parent_category` > `sub_category` > `name`
- Internal transfers (Boursorama's "Mouvements internes débiteurs/créditeurs") are filtered out of analysis views
- `init_data.py` handles both initial setup and manual SQLite migrations (adding columns)
- Vite proxy: `/api/*` → `http://localhost:8000/*` (strips `/api` prefix)

## Language

The codebase, comments, and UI are in **French**. Keep this convention when adding code or user-facing strings.
