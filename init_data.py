# init_data.py (à la racine du projet analyse-financiere/)
import json
import sys
from pathlib import Path

# Ajouter le dossier backend au path
sys.path.append(str(Path(__file__).parent / "backend"))

from database import SessionLocal, init_db
from models import Category, Account

def populate_categories(json_file="backend/category.json"):
    """Importe les catégories depuis ton JSON"""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    db = SessionLocal()
    
    try:
        count = 0
        for parent_name, parent_content in data["CatégoriesPrincipales"].items():
            for sub_name, items in parent_content.items():
                for item in items:
                    # Vérifier si la catégorie existe déjà
                    existing = db.query(Category).filter_by(name=item).first()
                    if not existing:
                        category = Category(
                            name=item,
                            parent_category=parent_name,
                            sub_category=sub_name
                        )
                        db.add(category)
                        count += 1
        
        db.commit()
        print(f"✓ {count} nouvelles catégories importées")
        print(f"✓ Total: {db.query(Category).count()} catégories en base")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Erreur lors de l'import des catégories: {e}")
        raise
    finally:
        db.close()

def create_default_accounts():
    """Crée tes comptes de base"""
    db = SessionLocal()
    
    default_accounts = [
        {"name": "BoursoBank", "account_type": "checking", "balance": 0},
        {"name": "Livret A", "account_type": "savings", "balance": 0},
        {"name": "PEA", "account_type": "investment", "balance": 0},
    ]
    
    try:
        count = 0
        for acc_data in default_accounts:
            existing = db.query(Account).filter_by(name=acc_data["name"]).first()
            if not existing:
                account = Account(**acc_data)
                db.add(account)
                count += 1
        
        db.commit()
        print(f"✓ {count} nouveaux comptes créés")
        print(f"✓ Total: {db.query(Account).count()} comptes en base")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Erreur lors de la création des comptes: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Initialisation de la base de données")
    print("=" * 50)
    
    # Créer les tables
    print("\n1. Création des tables...")
    init_db()
    
    # Importer les catégories
    print("\n2. Import des catégories...")
    populate_categories()
    
    # Créer les comptes
    print("\n3. Création des comptes...")
    create_default_accounts()
    
    print("\n" + "=" * 50)
    print("✅ Base de données prête à l'emploi !")
    print("=" * 50)
