# backend/crud.py
from sqlalchemy.orm import Session, joinedload
from .models import Transaction, Account, Category, CategorizationRule
from .schemas import TransactionCreate, CategorizationRuleCreate
from typing import List, Optional
from datetime import datetime


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
    account_id: Optional[int] = None,
) -> List[Transaction]:
    """Récupère les transactions avec filtres optionnels"""
    query = db.query(Transaction).options(joinedload(Transaction.category))
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()


def get_transactions_by_date_range(
    db: Session,
    start: datetime,
    end: datetime,
    account_id: Optional[int] = None,
) -> List[Transaction]:
    """Récupère les transactions par plage de dates avec eager loading de category"""
    query = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.date >= start, Transaction.date <= end)
    )
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    return query.order_by(Transaction.date.desc()).all()


def update_transaction_category(db: Session, txn_id: int, category_id: int) -> Transaction:
    """Re-catégorise une transaction"""
    txn = db.query(Transaction).options(joinedload(Transaction.category)).filter(Transaction.id == txn_id).first()
    if not txn:
        return None
    txn.category_id = category_id
    db.commit()
    db.refresh(txn)
    return txn


def get_accounts(db: Session) -> List[Account]:
    """Récupère tous les comptes actifs"""
    return db.query(Account).filter(Account.is_active == True).all()


def get_categories(db: Session) -> List[Category]:
    """Récupère toutes les catégories"""
    return db.query(Category).all()


def create_category(db: Session, name: str, parent_category: str, sub_category: str) -> Category:
    """Crée une nouvelle catégorie"""
    cat = Category(name=name, parent_category=parent_category, sub_category=sub_category)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def find_category_by_keyword(db: Session, keyword: str) -> Optional[Category]:
    """Trouve une catégorie par mot-clé dans le nom"""
    keyword = keyword.lower()
    categories = db.query(Category).all()
    for cat in categories:
        if keyword in cat.name.lower():
            return cat
    return None


def transaction_exists(db: Session, import_id: str) -> bool:
    """Vérifie si une transaction existe déjà"""
    return db.query(Transaction).filter(Transaction.import_id == import_id).first() is not None


# --- Categorization Rules ---

def get_categorization_rules(db: Session, active_only: bool = True) -> List[CategorizationRule]:
    """Liste les règles de catégorisation"""
    query = db.query(CategorizationRule)
    if active_only:
        query = query.filter(CategorizationRule.is_active == True)
    return query.all()


def create_categorization_rule(db: Session, rule: CategorizationRuleCreate) -> CategorizationRule:
    """Crée une règle de catégorisation"""
    db_rule = CategorizationRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


def apply_rules_to_uncategorized(db: Session) -> int:
    """Applique les règles actives aux transactions sans catégorie. Retourne le nombre de transactions mises à jour."""
    rules = get_categorization_rules(db, active_only=True)
    uncategorized = db.query(Transaction).filter(Transaction.category_id == None).all()
    count = 0
    for txn in uncategorized:
        for rule in rules:
            field_value = ""
            if rule.match_field == "merchant" and txn.merchant:
                field_value = txn.merchant.lower()
            elif txn.description:
                field_value = txn.description.lower()

            if rule.keyword.lower() in field_value:
                txn.category_id = rule.category_id
                count += 1
                break
    db.commit()
    return count
