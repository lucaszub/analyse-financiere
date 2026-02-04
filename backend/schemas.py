# backend/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .models import TransactionType


class TransactionBase(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    transaction_type: TransactionType
    amount: float
    description: Optional[str] = None
    date: datetime
    merchant: Optional[str] = None
    notes: Optional[str] = None
    category_parent_csv: Optional[str] = None


class TransactionCreate(TransactionBase):
    import_id: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime
    category_name: Optional[str] = None
    parent_category: Optional[str] = None
    sub_category: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionUpdate(BaseModel):
    category_id: int


class AccountResponse(BaseModel):
    id: int
    name: str
    account_type: Optional[str]
    balance: float
    is_active: bool

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    parent_category: str
    sub_category: str


class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_category: Optional[str]
    sub_category: Optional[str]

    class Config:
        from_attributes = True


class CategorizationRuleCreate(BaseModel):
    keyword: str
    category_id: int
    match_field: str = "description"


class CategorizationRuleResponse(BaseModel):
    id: int
    keyword: str
    category_id: int
    match_field: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ImportStats(BaseModel):
    total_rows: int
    imported: int
    duplicates: int
    errors: int
    error_details: list[str] = []
