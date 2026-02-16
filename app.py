import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time
import random
import os
import streamlit.components.v1 as components

# ==========================
# CONFIG PAGE
# ==========================
st.set_page_config(
    page_title="Vérification des statuts à l'inscription AFFECTÉ(E) - NON AFFECTÉ(E)",
    page_icon="🎓",
    layout="wide"
)

# ==========================
# CHARGEMENT FICHIER (AVANT UTILISATION)
# ==========================
try:
    if not os.path.exists("ABS_GENERAL.xlsx"):
        st.error("❌ Le fichier ABS_GENERAL.xlsx est introuvable dans le repository.")
        st.stop()

    df = pd.read_excel("ABS_GENERAL.xlsx", engine="openpyxl")

except Exception as e:
    st.error(f"Erreur chargement fichier : {e}")
    st.stop()

if "MATRICULE" not in df.columns:
    st.error("❌ Colonne 'MATRICULE' introuvable.")
    st.stop()

# ==========================
# TITRE
# ==========================
st.title("🎓 Système de Vérification des statuts à l'inscription AFFECTÉ(E) - NON AFFECTÉ(E) 2025-2026")

# ==========================
# STYLE GLOBAL
# ==========================
st.markdown("""
<style>

html, body, [class*="css"]  {
    background-color: #0b1c2d !important;
    font-family: Arial, Helvetica, sans-serif;
    color: white;
}

h1 {
    text-align: center;
    font-weight: 900;
    color: white;
}

.small-top {
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    opacity: 0.8;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

</style>
""", unsafe_allow_html=True)

# ==========================
# HEADER
# ==========================
st.markdown(
    "<h1>🎓 SYSTÈME DE VÉRIFICATION DES STATUTS À L'INSCRIPTION AFFECTÉ(E) - NON AFFECTÉ(E) 2025-2026</h1>",
    unsafe_allow_html=True
)

top_info = st.container()

with top_info:
    col1, col2, col3 = st.columns([1,1,1])

    with col2:
        limite = st.number_input(
            "Nombre de matricules à traiter",
            min_value=1,
            max_value=2000,
            value=10
        )

    st.markdown(
        f"<div class='small-top'>✅ {len(df)} lignes chargées automatiquement</div>",
        unsafe_allow_html=True
    )

st.markdown("---")

# ==========================
# CONFIGURATION CHROME
# ==========================
def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service("/usr/local/bin/chromedriver")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver


# ==========================
# INTERFACE
# ==========================
st.success(f"✅ {len(df)} lignes chargées automatiquement")

if st.button("🚀 Lancer la vérification"):

    matricules = df["MATRICULE"].astype(str).tolist()[:limite]

    col_center = st.container()

    with col_center:
        col_live, col_stats = st.columns([3,1])

        page_container = col_live.empty()
        progress_container = col_stats.container()

    resultats = []
    driver = None

    try:
        driver = get_chrome_driver()

        progress_bar = progress_container.progress(0)
        status_text = progress_container.empty()
        stats_box = progress_container.empty()

        total_aff = 0
        total_non = 0
        total_intr = 0

        for i, m in enumerate(matricules):

            status_text.markdown(f"### 🔄 {i+1}/{len(matricules)}")
            status_text.write(f"Matricule : **{m}**")

            driver.get("https://agfne.sigfne.net/vas/interface-edition-documents-sigfne/")
            wait = WebDriverWait(driver, 15)

            champ = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )

            champ.clear()
            champ.send_keys(str(m))
            champ.send_keys(Keys.RETURN)

            time.sleep(3)

            page_html = driver.page_source

            # LIVE VIEW
            with page_container:
                components.html(
                    page_html,
                    height=700,
                    scrolling=True
                )

            page_text = page_html.lower()

            if "non affecte" in page_text:
                statut = "NON_AFFECTE"
                total_non += 1
            elif "affecte" in page_text:
                statut = "AFFECTE"
                total_aff += 1
            elif "introuvable" in page_text:
                statut = "INTROUVABLE"
                total_intr += 1
            else:
                statut = "INDETERMINE"

            resultats.append({
                "matricule": m,
                "statut": statut,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            progress_bar.progress((i + 1) / len(matricules))

            stats_box.markdown(f"""
            ### 📊 STATISTIQUES
            ✅ AFFECTÉ : {total_aff}  
            ❌ NON AFFECTÉ : {total_non}  
            ⚠️ INTROUVABLE : {total_intr}
            """)

            if i < len(matricules) - 1:
                time.sleep(random.uniform(2, 4))

        progress_container.success("✅ TERMINÉ")

        df_resultats = pd.DataFrame(resultats)
        st.dataframe(df_resultats, use_container_width=True)

    finally:
        if driver:
            driver.quit()


