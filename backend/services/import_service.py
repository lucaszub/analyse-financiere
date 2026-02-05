# backend/services/import_service.py
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib

from ..crud import (
    create_transaction,
    transaction_exists,
    find_category_by_keyword,
    get_categorization_rules,
)
from ..schemas import TransactionCreate, ImportStats
from ..models import TransactionType


class BankCSVImporter:
    """Service pour importer des CSV bancaires"""

    def __init__(self, db: Session, account_id: int):
        self.db = db
        self.account_id = account_id

    def _normalize_base_key(self, row: pd.Series) -> str:
        """Construit la clé de base normalisée pour le hashing."""
        label = str(row.get("label", "")).strip().lower()
        label = " ".join(label.split())  # espaces multiples → un seul
        date_str = str(row["dateOp"]).split(" ")[0] if pd.notna(row.get("dateOp")) else ""
        amount_str = f"{float(row['amount']):.2f}"
        return f"{self.account_id}_{date_str}_{amount_str}_{label}"

    def generate_import_id(self, base_key: str, occurrence: int = 0) -> str:
        """Génère un ID unique pour éviter les doublons.

        Le hash inclut : account_id, date, montant normalisé, label normalisé,
        et un compteur d'occurrence pour distinguer les transactions identiques
        le même jour (ex: 2 cafés au même endroit).
        """
        unique_string = f"{base_key}_{occurrence}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def detect_transaction_type(self, amount: float) -> TransactionType:
        """Détecte si c'est un débit ou crédit"""
        return TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT

    def _apply_user_rules(self, description: str, merchant: str | None) -> int | None:
        """Applique les règles utilisateur (priorité sur le mapping hardcodé)"""
        rules = get_categorization_rules(self.db, active_only=True)
        for rule in rules:
            field_value = ""
            if rule.match_field == "merchant" and merchant:
                field_value = merchant.lower()
            elif description:
                field_value = description.lower()

            if rule.keyword.lower() in field_value:
                return rule.category_id
        return None

    def auto_categorize(self, description: str, merchant: str | None = None, category: str | None = None) -> int | None:
        """Essaye de catégoriser automatiquement. Priorité : règles utilisateur > mapping Boursorama > keywords"""
        if not description:
            return None

        # 1. Règles utilisateur (priorité)
        rule_result = self._apply_user_rules(description, merchant)
        if rule_result is not None:
            return rule_result

        # 2. Mapping catégories Boursorama
        boursorama_mapping = {
            "alimentation": "Épicerie",
            "carburant": "Carburant",
            "vêtements": "Vêtements",
            "hébergement": "Hôtel",
            "restaurant": "Restaurant",
            "virements": "Virement interne",
        }

        if category:
            category_lower = category.lower()
            for key, cat_name in boursorama_mapping.items():
                if key in category_lower:
                    found_cat = find_category_by_keyword(self.db, cat_name)
                    if found_cat:
                        return found_cat.id

        # 3. Keywords dans la description
        keywords_mapping = {
            "carrefour": "Épicerie",
            "leclerc": "Épicerie",
            "auchan": "Épicerie",
            "super u": "Épicerie",
            "intermarche": "Épicerie",
            "uber": "VTC",
            "sncf": "Train",
            "netflix": "Streaming",
            "spotify": "Streaming",
            "edf": "Électricité",
            "bouygues": "Internet",
            "orange": "Téléphone",
        }

        description_lower = description.lower()
        for keyword, category_name in keywords_mapping.items():
            if keyword in description_lower:
                found_cat = find_category_by_keyword(self.db, category_name)
                if found_cat:
                    return found_cat.id

        return None

    def parse_boursorama_csv(self, file_path: str) -> pd.DataFrame:
        """Parse un CSV Boursorama"""
        df = pd.read_csv(
            file_path,
            sep=";",
            encoding="utf-8-sig",  # Gère le BOM des CSV Boursorama
            quotechar='"',
        )

        # Nettoyer les guillemets dans les colonnes
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].str.strip('"')

        # Convertir amount en float (virgule → point, espaces normaux et insécables)
        if "amount" in df.columns:
            df["amount"] = (
                df["amount"]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace("\xa0", "", regex=False)
                .astype(float)
            )

        # Parser les dates
        if "dateOp" in df.columns:
            df["dateOp"] = pd.to_datetime(df["dateOp"], format="%Y-%m-%d")

        return df

    def import_csv(self, file_path: str, bank_type: str = "boursorama") -> ImportStats:
        """Importe un fichier CSV dans la base"""

        if bank_type == "boursorama":
            df = self.parse_boursorama_csv(file_path)
        else:
            raise ValueError(f"Type de banque '{bank_type}' non supporté")

        stats = ImportStats(
            total_rows=len(df),
            imported=0,
            duplicates=0,
            errors=0,
            error_details=[],
        )

        occurrence_tracker: dict[str, int] = {}

        for idx, row in df.iterrows():
            try:
                if pd.isna(row.get("amount")) or pd.isna(row.get("dateOp")):
                    stats.errors += 1
                    stats.error_details.append(f"Ligne {idx}: données manquantes")
                    continue

                base_key = self._normalize_base_key(row)
                occurrence = occurrence_tracker.get(base_key, 0)
                occurrence_tracker[base_key] = occurrence + 1

                import_id = self.generate_import_id(base_key, occurrence)

                if transaction_exists(self.db, import_id):
                    stats.duplicates += 1
                    continue

                merchant = (
                    row.get("supplierFound", "").strip()
                    if pd.notna(row.get("supplierFound"))
                    else None
                )
                description = (
                    row.get("label", "").strip() if pd.notna(row.get("label")) else ""
                )
                category_parent_csv = (
                    row.get("categoryParent", "").strip()
                    if pd.notna(row.get("categoryParent"))
                    else None
                )

                category_raw = row.get("category") if pd.notna(row.get("category")) else None

                transaction = TransactionCreate(
                    account_id=self.account_id,
                    transaction_type=self.detect_transaction_type(row["amount"]),
                    amount=abs(row["amount"]),
                    description=description,
                    date=row["dateOp"],
                    merchant=merchant,
                    category_id=self.auto_categorize(description, merchant, category_raw),
                    category_parent_csv=category_parent_csv,
                    import_id=import_id,
                )

                create_transaction(self.db, transaction)
                stats.imported += 1

            except Exception as e:
                stats.errors += 1
                stats.error_details.append(f"Ligne {idx}: {str(e)}")

        return stats
