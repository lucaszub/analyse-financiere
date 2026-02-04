# streamlit_app/app.py
import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Finance Manager", layout="wide")

st.title("💰 Gestionnaire de Finances Personnelles")

# Sidebar pour la navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["Import CSV", "Transactions", "Statistiques"]
)

# ==================== PAGE: IMPORT CSV ====================
if page == "Import CSV":
    st.header("📤 Importer des transactions")
    
    # Récupérer les comptes disponibles
    try:
        response = requests.get(f"{API_URL}/accounts")
        accounts = response.json()
        
        if not accounts:
            st.warning("Aucun compte trouvé. Créez d'abord un compte.")
        else:
            # Sélection du compte
            account_options = {f"{acc['name']} ({acc['account_type']})": acc['id'] for acc in accounts}
            selected_account = st.selectbox("Compte", list(account_options.keys()))
            account_id = account_options[selected_account]
            
            # Sélection du type de banque
            bank_type = st.selectbox(
                "Format du fichier",
                ["generic", "boursouma"],
                help="Choisir le format selon ta banque"
            )
            
            # Upload du fichier
            uploaded_file = st.file_uploader(
                "Choisis ton fichier CSV",
                type=['csv'],
                help="Exporte ton relevé bancaire au format CSV"
            )
            
            if uploaded_file is not None:
                # Aperçu du fichier
                st.subheader("Aperçu du fichier")
                df_preview = pd.read_csv(uploaded_file, nrows=5)
                st.dataframe(df_preview)
                
                # Reset le pointeur du fichier
                uploaded_file.seek(0)
                
                # Bouton d'import
                if st.button("🚀 Importer les transactions", type="primary"):
                    with st.spinner("Import en cours..."):
                        try:
                            # Envoyer le fichier à l'API
                            files = {"file": (uploaded_file.name, uploaded_file, "text/csv")}
                            data = {
                                "account_id": account_id,
                                "bank_type": bank_type
                            }
                            
                            response = requests.post(
                                f"{API_URL}/import/upload",
                                files=files,
                                data=data
                            )
                            
                            if response.status_code == 200:
                                stats = response.json()
                                
                                # Afficher les résultats
                                st.success("✅ Import terminé !")
                                
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("Total lignes", stats['total_rows'])
                                col2.metric("Importées", stats['imported'], delta=stats['imported'])
                                col3.metric("Doublons", stats['duplicates'])
                                col4.metric("Erreurs", stats['errors'])
                                
                                if stats['errors'] > 0 and stats['error_details']:
                                    with st.expander("Voir les erreurs"):
                                        for error in stats['error_details']:
                                            st.error(error)
                            else:
                                st.error(f"Erreur: {response.json()['detail']}")
                                
                        except Exception as e:
                            st.error(f"Erreur lors de l'import: {str(e)}")
    
    except Exception as e:
        st.error(f"Impossible de se connecter à l'API: {str(e)}")
        st.info("Assure-toi que l'API FastAPI est lancée sur http://localhost:8000")

# ==================== PAGE: TRANSACTIONS ====================
elif page == "Transactions":
    st.header("📊 Liste des transactions")
    
    try:
        # Récupérer les transactions
        response = requests.get(f"{API_URL}/transactions?limit=100")
        transactions = response.json()
        
        if transactions:
            # Convertir en DataFrame pour affichage
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['date']).dt.date
            
            # Afficher
            st.dataframe(
                df[['date', 'description', 'amount', 'transaction_type', 'merchant']],
                use_container_width=True
            )
            
            st.info(f"Total: {len(transactions)} transactions")
        else:
            st.info("Aucune transaction trouvée. Commence par importer un fichier CSV.")
    
    except Exception as e:
        st.error(f"Erreur: {str(e)}")

# ==================== PAGE: STATISTIQUES ====================
elif page == "Statistiques":
    st.header("📈 Statistiques")
    st.info("À venir : graphiques des dépenses par catégorie, évolution temporelle, etc.")