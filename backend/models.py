# models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class TransactionType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # "Boursorama", "Livret A", "PEA"
    account_type = Column(String)  # "checking", "savings", "investment"
    balance = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    
    transactions = relationship("Transaction", back_populates="account")


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    parent_category = Column(String)  # "BesoinsEssentiels", "Transport"
    sub_category = Column(String)     # "Logement", "Auto"
    
    transactions = relationship("Transaction", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    date = Column(DateTime, nullable=False)
    
    merchant = Column(String)  # Nom du commerçant
    notes = Column(String)

    # Catégorie parent du CSV Boursorama (ex: "Mouvements internes débiteurs")
    category_parent_csv = Column(String, nullable=True)

    # Pour éviter les doublons lors de l'import CSV
    import_id = Column(String, unique=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    match_field = Column(String, default="description")  # "description" ou "merchant"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category")