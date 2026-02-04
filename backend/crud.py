# backend/crud.py
from sqlalchemy.orm import Session
from .models import Transaction, Account, Category
from .schemas import TransactionCreate
from typing import List, Optional

def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
    """Crée une transaction"""
    db_transaction = Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    account_id: Optional[int] = None
) -> List[Transaction]:
    """Récupère les transactions avec filtres optionnels"""
    query = db.query(Transaction)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()

def get_accounts(db: Session) -> List[Account]:
    """Récupère tous les comptes actifs"""
    return db.query(Account).filter(Account.is_active == True).all()

def get_categories(db: Session) -> List[Category]:
    """Récupère toutes les catégories"""
    return db.query(Category).all()

def find_category_by_keyword(db: Session, keyword: str) -> Optional[Category]:
    """Trouve une catégorie par mot-clé dans la description"""
    keyword = keyword.lower()
    categories = db.query(Category).all()
    
    for cat in categories:
        if keyword in cat.name.lower():
            return cat
    return None

def transaction_exists(db: Session, import_id: str) -> bool:
    """Vérifie si une transaction existe déjà"""
    return db.query(Transaction).filter(Transaction.import_id == import_id).first() is not None