# app.py - Routeur principal Streamlit
import streamlit as st

st.set_page_config(page_title="Finance Manager", layout="wide")

from pages import analyse, import_csv

page = st.sidebar.radio(
    "Navigation",
    ["Analyse des dépenses", "Import CSV"],
)

if page == "Analyse des dépenses":
    analyse.render()
elif page == "Import CSV":
    import_csv.render()
