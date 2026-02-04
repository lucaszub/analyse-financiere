# pages/import_csv.py
import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"


def render():
    st.header("Import CSV")

    st.markdown("Import de relevés **BoursoBank** (format Boursorama).")

    uploaded_file = st.file_uploader(
        "Choisis ton fichier CSV exporté depuis Boursorama",
        type=["csv"],
    )

    if uploaded_file is not None:
        # Aperçu avec le bon séparateur
        st.subheader("Aperçu du fichier")
        try:
            df_preview = pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig", nrows=5)
            st.dataframe(df_preview, use_container_width=True)
        except Exception as e:
            st.error(f"Impossible de lire le fichier : {e}")

        uploaded_file.seek(0)

        if st.button("Importer les transactions", type="primary"):
            with st.spinner("Import en cours..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                    # Hardcodé : account_id=1 (BoursoBank)
                    data = {"account_id": 1}

                    response = requests.post(
                        f"{API_URL}/upload",
                        files=files,
                        data=data,
                    )

                    if response.status_code == 200:
                        stats = response.json()

                        st.success("Import terminé !")

                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total lignes", stats["total_rows"])
                        col2.metric("Importées", stats["imported"])
                        col3.metric("Doublons", stats["duplicates"])
                        col4.metric("Erreurs", stats["errors"])

                        if stats["errors"] > 0 and stats.get("error_details"):
                            with st.expander("Voir les erreurs"):
                                for error in stats["error_details"]:
                                    st.error(error)
                    else:
                        detail = response.json().get("detail", "Erreur inconnue")
                        st.error(f"Erreur : {detail}")

                except requests.ConnectionError:
                    st.error("Impossible de se connecter à l'API. Vérifie que le backend est lancé.")
                except Exception as e:
                    st.error(f"Erreur lors de l'import : {e}")

    st.divider()

    # Bouton pour ré-appliquer les règles de catégorisation
    if st.button("Ré-appliquer les règles de catégorisation"):
        with st.spinner("Application des règles..."):
            try:
                resp = requests.post(f"{API_URL}/rules/apply")
                if resp.status_code == 200:
                    count = resp.json().get("updated", 0)
                    st.success(f"{count} transaction(s) re-catégorisée(s).")
                else:
                    st.error("Erreur lors de l'application des règles.")
            except requests.ConnectionError:
                st.error("Impossible de se connecter à l'API.")
