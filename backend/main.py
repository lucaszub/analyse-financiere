# backend/main.py
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import tempfile
import os
from typing import List, Optional

from .database import get_db, init_db
from .schemas import TransactionResponse, AccountResponse, CategoryResponse, ImportStats
from .crud import get_transactions, get_accounts, get_categories
from .services.import_service import BankCSVImporter

app = FastAPI(
    title="Finance Manager API",
    description="API pour gérer tes finances personnelles",
    version="1.0.0"
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

@app.get("/accounts", response_model=List[AccountResponse])
def list_accounts(db: Session = Depends(get_db)):
    """Liste tous les comptes"""
    return get_accounts(db)

@app.get("/categories", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """Liste toutes les catégories"""
    return get_categories(db)

@app.get("/transactions", response_model=List[TransactionResponse])
def list_transactions(
    skip: int = 0,
    limit: int = 100,
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Liste les transactions avec pagination"""
    return get_transactions(db, skip=skip, limit=limit, account_id=account_id)

@app.post("/upload")
async def upload_csv(
    file: UploadFile,
    account_id: int = 1,
    db: Session = Depends(get_db)
):
    """Upload et importe un CSV bancaire"""
    
    # Vérifier que le compte existe
    accounts = get_accounts(db)
    if not any(acc.id == account_id for acc in accounts):
        raise HTTPException(status_code=404, detail=f"Compte {account_id} introuvable")
    
    # Vérifier l'extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Le fichier doit être un CSV")
    
    try:
        content = await file.read()
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        importer = BankCSVImporter(db, account_id)
        stats = importer.import_csv(temp_file_path, "boursorama")
        
        os.unlink(temp_file_path)
        
        return stats
        
    except Exception as e:
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")