"""Tests de déduplication des imports CSV."""

import os
import tempfile

import pandas as pd
import pytest

from backend.models import Transaction
from backend.services.import_service import BankCSVImporter


def _write_csv(rows: list[dict], path: str) -> None:
    """Écrit un CSV Boursorama minimal."""
    df = pd.DataFrame(rows)
    df.to_csv(path, sep=";", index=False, encoding="utf-8-sig")


def _make_row(
    date: str = "2025-06-15",
    amount: str = "-50,00",
    label: str = "CARREFOUR MARKET",
    category_parent: str = "Alimentation",
    supplier: str = "Carrefour",
) -> dict:
    return {
        "dateOp": date,
        "dateVal": date,
        "label": label,
        "category": "",
        "categoryParent": category_parent,
        "supplierFound": supplier,
        "amount": amount,
    }


class TestGenerateImportId:
    """Tests unitaires de generate_import_id / _normalize_base_key."""

    def test_same_row_same_hash(self, db):
        importer = BankCSVImporter(db, account_id=1)
        row = pd.Series({"dateOp": "2025-06-15", "amount": -50.0, "label": "CARREFOUR"})
        key = importer._normalize_base_key(row)
        h1 = importer.generate_import_id(key, 0)
        h2 = importer.generate_import_id(key, 0)
        assert h1 == h2

    def test_case_insensitive(self, db):
        """'CARREFOUR' et 'carrefour' doivent donner le même hash."""
        importer = BankCSVImporter(db, account_id=1)
        row_upper = pd.Series({"dateOp": "2025-06-15", "amount": -50.0, "label": "CARREFOUR MARKET"})
        row_lower = pd.Series({"dateOp": "2025-06-15", "amount": -50.0, "label": "carrefour market"})
        key_upper = importer._normalize_base_key(row_upper)
        key_lower = importer._normalize_base_key(row_lower)
        assert importer.generate_import_id(key_upper, 0) == importer.generate_import_id(key_lower, 0)

    def test_whitespace_normalization(self, db):
        """Espaces multiples ou tabs ne changent pas le hash."""
        importer = BankCSVImporter(db, account_id=1)
        row_normal = pd.Series({"dateOp": "2025-06-15", "amount": -50.0, "label": "CARREFOUR MARKET"})
        row_spaces = pd.Series({"dateOp": "2025-06-15", "amount": -50.0, "label": "  CARREFOUR   MARKET  "})
        key1 = importer._normalize_base_key(row_normal)
        key2 = importer._normalize_base_key(row_spaces)
        assert importer.generate_import_id(key1, 0) == importer.generate_import_id(key2, 0)

    def test_different_account_different_hash(self, db):
        """La même transaction sur 2 comptes différents = 2 hash différents."""
        row = pd.Series({"dateOp": "2025-06-15", "amount": -50.0, "label": "CARREFOUR"})
        importer1 = BankCSVImporter(db, account_id=1)
        importer2 = BankCSVImporter(db, account_id=2)
        key1 = importer1._normalize_base_key(row)
        key2 = importer2._normalize_base_key(row)
        assert importer1.generate_import_id(key1, 0) != importer2.generate_import_id(key2, 0)

    def test_occurrence_differentiates(self, db):
        """Occurrence 0 et 1 du même base_key donnent des hash différents."""
        importer = BankCSVImporter(db, account_id=1)
        row = pd.Series({"dateOp": "2025-06-15", "amount": -50.0, "label": "CARREFOUR"})
        key = importer._normalize_base_key(row)
        assert importer.generate_import_id(key, 0) != importer.generate_import_id(key, 1)


class TestImportCSVDeduplication:
    """Tests d'intégration de la déduplication lors de l'import."""

    def test_import_then_reimport_same_csv(self, db):
        """Importer 2 fois le même CSV ne crée pas de doublons."""
        rows = [
            _make_row(date="2025-06-15", amount="-50,00", label="CARREFOUR"),
            _make_row(date="2025-06-16", amount="-30,00", label="BOULANGERIE"),
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as f:
            _write_csv(rows, f.name)
            path = f.name

        try:
            importer = BankCSVImporter(db, account_id=1)
            stats1 = importer.import_csv(path)
            assert stats1.imported == 2
            assert stats1.duplicates == 0

            stats2 = importer.import_csv(path)
            assert stats2.imported == 0
            assert stats2.duplicates == 2

            total = db.query(Transaction).count()
            assert total == 2
        finally:
            os.unlink(path)

    def test_overlapping_csv_ranges(self, db):
        """CSV-A (jan-fev) + CSV-B (fev-mar) : les transactions de février ne sont importées qu'une fois."""
        csv_a_rows = [
            _make_row(date="2025-01-15", amount="-50,00", label="JANVIER"),
            _make_row(date="2025-02-10", amount="-80,00", label="FEVRIER OVERLAP"),
        ]
        csv_b_rows = [
            _make_row(date="2025-02-10", amount="-80,00", label="FEVRIER OVERLAP"),
            _make_row(date="2025-03-05", amount="-25,00", label="MARS"),
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as fa:
            _write_csv(csv_a_rows, fa.name)
            path_a = fa.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as fb:
            _write_csv(csv_b_rows, fb.name)
            path_b = fb.name

        try:
            importer = BankCSVImporter(db, account_id=1)
            stats_a = importer.import_csv(path_a)
            assert stats_a.imported == 2

            stats_b = importer.import_csv(path_b)
            assert stats_b.imported == 1  # seul MARS est nouveau
            assert stats_b.duplicates == 1  # FEVRIER OVERLAP déjà en base

            total = db.query(Transaction).count()
            assert total == 3
        finally:
            os.unlink(path_a)
            os.unlink(path_b)

    def test_true_duplicates_same_day(self, db):
        """2 transactions identiques le même jour (2 cafés) doivent toutes être importées."""
        rows = [
            _make_row(date="2025-06-15", amount="-4,50", label="CAFE DU COIN"),
            _make_row(date="2025-06-15", amount="-4,50", label="CAFE DU COIN"),
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as f:
            _write_csv(rows, f.name)
            path = f.name

        try:
            importer = BankCSVImporter(db, account_id=1)
            stats = importer.import_csv(path)
            assert stats.imported == 2
            assert stats.duplicates == 0

            total = db.query(Transaction).count()
            assert total == 2
        finally:
            os.unlink(path)

    def test_true_duplicates_reimport(self, db):
        """Réimporter un CSV contenant 2 transactions identiques ne crée pas de doublons."""
        rows = [
            _make_row(date="2025-06-15", amount="-4,50", label="CAFE DU COIN"),
            _make_row(date="2025-06-15", amount="-4,50", label="CAFE DU COIN"),
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as f:
            _write_csv(rows, f.name)
            path = f.name

        try:
            importer = BankCSVImporter(db, account_id=1)
            stats1 = importer.import_csv(path)
            assert stats1.imported == 2

            stats2 = importer.import_csv(path)
            assert stats2.imported == 0
            assert stats2.duplicates == 2

            total = db.query(Transaction).count()
            assert total == 2
        finally:
            os.unlink(path)

    def test_different_accounts_not_deduplicated(self, db):
        """La même transaction importée sur 2 comptes différents = 2 entrées."""
        from backend.models import Account
        account2 = Account(id=2, name="Livret A", account_type="savings")
        db.add(account2)
        db.commit()

        rows = [_make_row(date="2025-06-15", amount="-50,00", label="VIREMENT")]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as f:
            _write_csv(rows, f.name)
            path = f.name

        try:
            importer1 = BankCSVImporter(db, account_id=1)
            stats1 = importer1.import_csv(path)
            assert stats1.imported == 1

            importer2 = BankCSVImporter(db, account_id=2)
            stats2 = importer2.import_csv(path)
            assert stats2.imported == 1

            total = db.query(Transaction).count()
            assert total == 2
        finally:
            os.unlink(path)

    def test_case_difference_deduplicated(self, db):
        """'CARREFOUR' dans CSV-A et 'carrefour' dans CSV-B = doublon détecté."""
        rows_a = [_make_row(date="2025-06-15", amount="-50,00", label="CARREFOUR MARKET")]
        rows_b = [_make_row(date="2025-06-15", amount="-50,00", label="carrefour market")]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as fa:
            _write_csv(rows_a, fa.name)
            path_a = fa.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as fb:
            _write_csv(rows_b, fb.name)
            path_b = fb.name

        try:
            importer = BankCSVImporter(db, account_id=1)
            stats_a = importer.import_csv(path_a)
            assert stats_a.imported == 1

            stats_b = importer.import_csv(path_b)
            assert stats_b.imported == 0
            assert stats_b.duplicates == 1
        finally:
            os.unlink(path_a)
            os.unlink(path_b)
