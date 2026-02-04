# pages/analyse.py
import streamlit as st
import requests
import pandas as pd
from datetime import date, datetime
from collections import defaultdict

API_URL = "http://localhost:8000"

INTERNAL_TRANSFER_PARENTS = {
    "Mouvements internes débiteurs",
    "Mouvements internes créditeurs",
}


def _fetch_transactions(start_date: date, end_date: date):
    """Récupère les transactions depuis l'API."""
    resp = requests.get(
        f"{API_URL}/transactions/range",
        params={"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
    )
    if resp.status_code == 200:
        return resp.json()
    return []


def _fetch_categories():
    """Récupère toutes les catégories."""
    resp = requests.get(f"{API_URL}/categories")
    if resp.status_code == 200:
        return resp.json()
    return []


def _build_tree(transactions):
    """Construit l'arbre catégorie parent > sous-catégorie > transactions."""
    tree = defaultdict(lambda: {"total": 0.0, "subcategories": defaultdict(lambda: {"total": 0.0, "transactions": []})})

    for txn in transactions:
        parent = txn.get("parent_category") or "Non catégorisé"
        sub = txn.get("sub_category") or "Non catégorisé"
        amount = txn["amount"]

        tree[parent]["total"] += amount
        tree[parent]["subcategories"][sub]["total"] += amount
        tree[parent]["subcategories"][sub]["transactions"].append(txn)

    # Trier par total décroissant
    sorted_tree = dict(sorted(tree.items(), key=lambda x: x[1]["total"], reverse=True))
    return sorted_tree


def _format_amount(amount: float) -> str:
    """Formate un montant en euros."""
    return f"{amount:,.2f} €".replace(",", " ").replace(".", ",").replace(" ", " ")


@st.dialog("Re-catégoriser la transaction")
def _recategorize_dialog(txn, categories):
    """Dialog pour re-catégoriser une transaction."""
    st.markdown(f"**{txn['description']}**")
    st.markdown(f"Montant : {_format_amount(txn['amount'])} | Date : {txn['date'][:10]}")

    # Construire les options de catégorie
    cat_options = {}
    for cat in sorted(categories, key=lambda c: f"{c.get('parent_category', '')} > {c.get('sub_category', '')} > {c['name']}"):
        label = f"{cat.get('parent_category', '?')} > {cat.get('sub_category', '?')} > {cat['name']}"
        cat_options[label] = cat["id"]

    cat_labels = list(cat_options.keys())

    # Pré-sélectionner la catégorie actuelle
    current_idx = 0
    if txn.get("category_id"):
        for i, (label, cid) in enumerate(cat_options.items()):
            if cid == txn["category_id"]:
                current_idx = i
                break

    selected_label = st.selectbox("Catégorie", cat_labels, index=current_idx)
    selected_cat_id = cat_options[selected_label]

    # Option créer une règle
    create_rule = st.checkbox("Créer une règle pour les futures transactions similaires")
    rule_keyword = ""
    rule_match_field = "description"
    if create_rule:
        # Extraction intelligente du keyword : prendre les premiers mots significatifs
        default_kw = txn.get("description", "")
        # Retirer les préfixes courants type "CARTE xx/xx"
        parts = default_kw.split()
        if len(parts) > 2 and parts[0].upper() in ("CARTE", "VIR", "PRLV"):
            default_kw = " ".join(parts[2:])
        rule_keyword = st.text_input("Mot-clé à matcher", value=default_kw[:50])
        rule_match_field = st.selectbox("Champ à matcher", ["description", "merchant"])

    # Section créer une nouvelle catégorie
    with st.expander("Créer une nouvelle catégorie"):
        new_parent = st.text_input("Catégorie parente (ex: BesoinsEssentiels)")
        new_sub = st.text_input("Sous-catégorie (ex: Alimentation)")
        new_name = st.text_input("Nom de la catégorie (ex: Boulangerie)")
        if st.button("Créer la catégorie"):
            if new_parent and new_sub and new_name:
                resp = requests.post(
                    f"{API_URL}/categories",
                    json={"name": new_name, "parent_category": new_parent, "sub_category": new_sub},
                )
                if resp.status_code == 200:
                    st.success(f"Catégorie '{new_name}' créée !")
                    st.rerun()
                else:
                    st.error("Erreur lors de la création.")
            else:
                st.warning("Remplis tous les champs.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Valider", type="primary", use_container_width=True):
            # Sauvegarder la re-catégorisation
            resp = requests.patch(
                f"{API_URL}/transactions/{txn['id']}/category",
                json={"category_id": selected_cat_id},
            )
            if resp.status_code == 200:
                # Créer la règle si demandé
                if create_rule and rule_keyword.strip():
                    requests.post(
                        f"{API_URL}/rules",
                        json={
                            "keyword": rule_keyword.strip(),
                            "category_id": selected_cat_id,
                            "match_field": rule_match_field,
                        },
                    )
                st.rerun()
            else:
                st.error("Erreur lors de la sauvegarde.")
    with col2:
        if st.button("Annuler", use_container_width=True):
            st.rerun()


def render():
    st.header("Analyse des dépenses")

    # --- Date range picker ---
    today = date.today()
    first_of_month = today.replace(day=1)

    col_start, col_end = st.columns(2)
    with col_start:
        start_date = st.date_input("Du", value=first_of_month)
    with col_end:
        end_date = st.date_input("Au", value=today)

    if start_date > end_date:
        st.error("La date de début doit être avant la date de fin.")
        return

    # --- Charger les données ---
    try:
        all_transactions = _fetch_transactions(start_date, end_date)
    except requests.ConnectionError:
        st.error("Impossible de se connecter à l'API. Vérifie que le backend est lancé.")
        return

    if not all_transactions:
        st.info("Aucune transaction sur cette période.")
        return

    # --- Charger les catégories (pour le dialog) ---
    categories = _fetch_categories()

    # --- Filtrer les virements internes ---
    transactions = [
        t for t in all_transactions
        if t.get("category_parent_csv") not in INTERNAL_TRANSFER_PARENTS
    ]

    # --- Résumé Revenus / Dépenses ---
    revenus = sum(t["amount"] for t in transactions if t["transaction_type"] == "credit")
    depenses = sum(t["amount"] for t in transactions if t["transaction_type"] == "debit")
    difference = revenus - depenses

    col_r, col_d, col_diff = st.columns(3)
    col_r.metric("Revenus", _format_amount(revenus))
    col_d.metric("Dépenses", _format_amount(depenses))
    diff_label = f"+{_format_amount(difference)}" if difference >= 0 else f"-{_format_amount(abs(difference))}"
    col_diff.metric("Différence", diff_label)

    st.divider()

    # --- Séparer dépenses et revenus pour l'accordion ---
    debit_txns = [t for t in transactions if t["transaction_type"] == "debit"]
    credit_txns = [t for t in transactions if t["transaction_type"] == "credit"]

    # --- Accordion dépenses ---
    st.subheader("Dépenses par catégorie")
    _render_accordion(debit_txns, categories, prefix="deb")

    st.divider()

    # --- Accordion revenus ---
    st.subheader("Revenus par catégorie")
    _render_accordion(credit_txns, categories, prefix="cred")


def _render_accordion(transactions, categories, prefix=""):
    """Affiche un accordion 3 niveaux pour un ensemble de transactions."""
    tree = _build_tree(transactions)

    if not tree:
        st.info("Aucune transaction.")
        return

    for parent_name, parent_data in tree.items():
        parent_key = f"expand_L1_{prefix}_{parent_name}"
        is_expanded = st.session_state.get(parent_key, False)

        indicator = "▼" if is_expanded else "▶"
        if st.button(
            f"{indicator}  {parent_name}  —  {_format_amount(parent_data['total'])}",
            key=f"btn_L1_{prefix}_{parent_name}",
            use_container_width=True,
        ):
            st.session_state[parent_key] = not is_expanded
            st.rerun()

        if is_expanded:
            sorted_subs = sorted(
                parent_data["subcategories"].items(),
                key=lambda x: x[1]["total"],
                reverse=True,
            )
            for sub_name, sub_data in sorted_subs:
                sub_key = f"expand_L2_{prefix}_{parent_name}_{sub_name}"
                is_sub_expanded = st.session_state.get(sub_key, False)

                sub_indicator = "▼" if is_sub_expanded else "▶"
                col_sub, _ = st.columns([11, 1])
                with col_sub:
                    if st.button(
                        f"    {sub_indicator}  {sub_name}  —  {_format_amount(sub_data['total'])}",
                        key=f"btn_L2_{prefix}_{parent_name}_{sub_name}",
                        use_container_width=True,
                    ):
                        st.session_state[sub_key] = not is_sub_expanded
                        st.rerun()

                if is_sub_expanded:
                    # Niveau 3 : transactions individuelles
                    for txn in sorted(sub_data["transactions"], key=lambda t: t["date"]):
                        txn_date = txn["date"][:10]
                        desc = txn.get("description", "")[:50]
                        amount_str = _format_amount(txn["amount"])

                        col_date, col_desc, col_amt, col_btn = st.columns([2, 6, 2, 2])
                        with col_date:
                            st.text(txn_date)
                        with col_desc:
                            st.text(desc)
                        with col_amt:
                            st.text(amount_str)
                        with col_btn:
                            if st.button("Recat", key=f"recat_{prefix}_{txn['id']}"):
                                _recategorize_dialog(txn, categories)
