# init_data.py (à la racine du projet analyse-financiere/)
import json
import sqlite3

from backend.database import SessionLocal, init_db, engine
from backend.models import Category, Account


def migrate_add_columns():
    """Ajoute les nouvelles colonnes si elles n'existent pas (migration manuelle pour SQLite)"""
    # Utiliser le même chemin de DB que SQLAlchemy
    db_path = str(engine.url.database)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Vérifier si category_parent_csv existe dans transactions
    cursor.execute("PRAGMA table_info(transactions)")
    columns = [col[1] for col in cursor.fetchall()]

    if "category_parent_csv" not in columns:
        cursor.execute("ALTER TABLE transactions ADD COLUMN category_parent_csv TEXT")
        print("  ✓ Colonne category_parent_csv ajoutée à transactions")
    else:
        print("  ✓ Colonne category_parent_csv déjà présente")

    conn.commit()
    conn.close()


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

    # Créer les tables (y compris categorization_rules)
    print("\n1. Création des tables...")
    init_db()

    # Migration : ajouter les nouvelles colonnes
    print("\n2. Migration des colonnes...")
    migrate_add_columns()

    # Importer les catégories
    print("\n3. Import des catégories...")
    populate_categories()

    # Créer les comptes
    print("\n4. Création des comptes...")
    create_default_accounts()

    print("\n" + "=" * 50)
    print("Base de données prête à l'emploi !")
    print("=" * 50)
