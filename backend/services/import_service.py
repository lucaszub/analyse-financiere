# backend/services/import_service.py
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib

from ..crud import create_transaction, transaction_exists, find_category_by_keyword
from ..schemas import TransactionCreate, ImportStats
from ..models import TransactionType

class BankCSVImporter:
    """Service pour importer des CSV bancaires"""
    
    def __init__(self, db: Session, account_id: int):
        self.db = db
        self.account_id = account_id
    
    def generate_import_id(self, row: pd.Series) -> str:
        """Génère un ID unique pour éviter les doublons"""
        unique_string = f"{row['dateOp']}_{row['amount']}_{row['label']}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def detect_transaction_type(self, amount: float) -> TransactionType:
        """Détecte si c'est un débit ou crédit"""
        return TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT
    
    def auto_categorize(self, description: str, category: str = None) -> int | None:
        """Essaye de catégoriser automatiquement"""
        if not description:
            return None
        
        boursorama_mapping = {
            'alimentation': 'Épicerie',
            'carburant': 'Carburant',
            'vêtements': 'Vêtements',
            'hébergement': 'Hôtel',
            'restaurant': 'Restaurant',
            'virements': 'Virement interne',
        }
        
        if category:
            category_lower = category.lower()
            for key, cat_name in boursorama_mapping.items():
                if key in category_lower:
                    found_cat = find_category_by_keyword(self.db, cat_name)
                    if found_cat:
                        return found_cat.id
        
        keywords_mapping = {
            'carrefour': 'Épicerie',
            'leclerc': 'Épicerie',
            'auchan': 'Épicerie',
            'super u': 'Épicerie',
            'intermarche': 'Épicerie',
            'uber': 'VTC',
            'sncf': 'Train',
            'netflix': 'Streaming',
            'spotify': 'Streaming',
            'edf': 'Électricité',
            'bouygues': 'Internet',
            'orange': 'Téléphone',
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
        # Format: dateOp;dateVal;label;category;categoryParent;supplierFound;amount;comment;accountNum;accountLabel;accountbalance
        df = pd.read_csv(
            file_path,
            sep=';',
            encoding='utf-8',
            quotechar='"'
        )
        
        # Nettoyer les guillemets dans les colonnes
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip('"')
        
        # Convertir amount en float (remplacer virgule par point et gérer les espaces)
        if 'amount' in df.columns:
            df['amount'] = df['amount'].astype(str).str.replace(',', '.').str.replace(' ', '').astype(float)
        
        # Parser les dates
        if 'dateOp' in df.columns:
            df['dateOp'] = pd.to_datetime(df['dateOp'], format='%Y-%m-%d')
        
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
            error_details=[]
        )
        
        for idx, row in df.iterrows():
            try:
                # Vérifier les données essentielles
                if pd.isna(row.get('amount')) or pd.isna(row.get('dateOp')):
                    stats.errors += 1
                    stats.error_details.append(f"Ligne {idx}: données manquantes")
                    continue
                
                # Générer import_id
                import_id = self.generate_import_id(row)
                
                # Vérifier doublons
                if transaction_exists(self.db, import_id):
                    stats.duplicates += 1
                    continue
                
                # Préparer les données
                merchant = row.get('supplierFound', '').strip() if pd.notna(row.get('supplierFound')) else None
                description = row.get('label', '').strip() if pd.notna(row.get('label')) else ""
                
                # Créer la transaction
                transaction = TransactionCreate(
                    account_id=self.account_id,
                    transaction_type=self.detect_transaction_type(row['amount']),
                    amount=abs(row['amount']),
                    description=description,
                    date=row['dateOp'],
                    merchant=merchant,
                    category_id=self.auto_categorize(description, row.get('category')),
                    import_id=import_id
                )
                
                create_transaction(self.db, transaction)
                stats.imported += 1
                
            except Exception as e:
                stats.errors += 1
                stats.error_details.append(f"Ligne {idx}: {str(e)}")
        
        return stats