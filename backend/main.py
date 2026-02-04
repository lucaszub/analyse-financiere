# backend/main.py
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import tempfile
import os
from typing import List, Optional
from datetime import date, datetime

from .database import get_db, init_db
from .schemas import (
    TransactionResponse,
    TransactionUpdate,
    AccountResponse,
    CategoryCreate,
    CategoryResponse,
    CategorizationRuleCreate,
    CategorizationRuleResponse,
    ImportStats,
)
from .crud import (
    get_transactions,
    get_transactions_by_date_range,
    update_transaction_category,
    get_accounts,
    get_categories,
    create_category,
    get_categorization_rules,
    create_categorization_rule,
    apply_rules_to_uncategorized,
)
from .services.import_service import BankCSVImporter

app = FastAPI(
    title="Finance Manager API",
    description="API pour gérer tes finances personnelles",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {"message": "Finance Manager API", "status": "running"}


# --- Accounts ---

@app.get("/accounts", response_model=List[AccountResponse])
def list_accounts(db: Session = Depends(get_db)):
    """Liste tous les comptes"""
    return get_accounts(db)


# --- Categories ---

@app.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """Liste toutes les catégories"""
    return get_categories(db)


@app.post("/categories", response_model=CategoryResponse)
def create_new_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle catégorie"""
    return create_category(db, payload.name, payload.parent_category, payload.sub_category)


# --- Transactions ---

@app.get("/transactions", response_model=List[TransactionResponse])
def list_transactions(
    skip: int = 0,
    limit: int = 100,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Liste les transactions avec pagination"""
    txns = get_transactions(db, skip=skip, limit=limit, account_id=account_id)
    return _enrich_transactions(txns)


@app.get("/transactions/range", response_model=List[TransactionResponse])
def list_transactions_by_range(
    start_date: date,
    end_date: date,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Transactions par plage de dates"""
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    txns = get_transactions_by_date_range(db, start_dt, end_dt, account_id)
    return _enrich_transactions(txns)


@app.patch("/transactions/{txn_id}/category", response_model=TransactionResponse)
def recategorize_transaction(txn_id: int, payload: TransactionUpdate, db: Session = Depends(get_db)):
    """Re-catégorise une transaction"""
    txn = update_transaction_category(db, txn_id, payload.category_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    return _enrich_transactions([txn])[0]


# --- Categorization Rules ---

@app.get("/rules", response_model=List[CategorizationRuleResponse])
def list_rules(db: Session = Depends(get_db)):
    """Lister les règles de catégorisation"""
    return get_categorization_rules(db)


@app.post("/rules", response_model=CategorizationRuleResponse)
def create_rule(payload: CategorizationRuleCreate, db: Session = Depends(get_db)):
    """Créer une règle de catégorisation"""
    return create_categorization_rule(db, payload)


@app.post("/rules/apply")
def apply_rules(db: Session = Depends(get_db)):
    """Appliquer les règles aux transactions non catégorisées"""
    count = apply_rules_to_uncategorized(db)
    return {"updated": count}


# --- Import ---

@app.post("/upload")
async def upload_csv(
    file: UploadFile,
    account_id: int = 1,
    db: Session = Depends(get_db),
):
    """Upload et importe un CSV bancaire"""

    accounts = get_accounts(db)
    if not any(acc.id == account_id for acc in accounts):
        raise HTTPException(status_code=404, detail=f"Compte {account_id} introuvable")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un CSV")

    try:
        content = await file.read()

        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".csv") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        importer = BankCSVImporter(db, account_id)
        stats = importer.import_csv(temp_file_path, "boursorama")

        os.unlink(temp_file_path)

        return stats

    except Exception as e:
        if "temp_file_path" in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


# --- Helpers ---

def _enrich_transactions(txns) -> List[dict]:
    """Ajoute les infos de catégorie aux transactions pour la réponse."""
    results = []
    for txn in txns:
        d = {
            "id": txn.id,
            "account_id": txn.account_id,
            "category_id": txn.category_id,
            "transaction_type": txn.transaction_type,
            "amount": txn.amount,
            "description": txn.description,
            "date": txn.date,
            "merchant": txn.merchant,
            "notes": txn.notes,
            "category_parent_csv": txn.category_parent_csv,
            "import_id": getattr(txn, "import_id", None),
            "created_at": txn.created_at,
            "category_name": txn.category.name if txn.category else None,
            "parent_category": txn.category.parent_category if txn.category else None,
            "sub_category": txn.category.sub_category if txn.category else None,
        }
        results.append(d)
    return results
