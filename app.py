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
import os

# ==========================
# CONFIG PAGE
# ==========================
st.set_page_config(
    page_title="Vérification des statuts",
    page_icon="🎓",
    layout="wide"
)

# ==========================
# STYLE GLOBAL PRO
# ==========================
st.markdown("""
<style>

html, body, [class*="css"] {
    background:#071a2b;
    font-family: Arial, Helvetica, sans-serif;
    color:white;
}

/* pleine largeur */
.main .block-container{
    max-width:100%;
    padding-top:0.5rem;
    padding-bottom:0rem;
}

/* TITRE */
.main-title{
    text-align:center;
    font-size:38px;
    font-weight:900;
    letter-spacing:1px;
    margin-bottom:5px;
}

/* infos petites */
.small-top{
    text-align:center;
    font-size:12px;
    opacity:0.8;
}

/* zone centrale */
.live-zone{
    display:flex;
    align-items:center;
    justify-content:center;
    height:78vh;
}

/* image large */
[data-testid="stImage"] img{
    border-radius:10px;
}

/* metrics */
[data-testid="stMetricValue"]{
    font-size:28px;
    font-weight:800;
}

</style>
""", unsafe_allow_html=True)

# ==========================
# CHARGEMENT FICHIER
# ==========================
try:
    if not os.path.exists("ABS_GENERAL.xlsx"):
        st.error("❌ Fichier ABS_GENERAL.xlsx introuvable.")
        st.stop()

    df = pd.read_excel("ABS_GENERAL.xlsx", engine="openpyxl")

except Exception as e:
    st.error(f"Erreur chargement : {e}")
    st.stop()

if "MATRICULE" not in df.columns:
    st.error("❌ Colonne MATRICULE absente.")
    st.stop()

# ==========================
# HEADER
# ==========================
st.markdown("""
<div class="main-title">
🎓 SYSTÈME DE VÉRIFICATION DES STATUTS À L'INSCRIPTION<br>
AFFECTÉ(E) - NON AFFECTÉ(E) 2025-2026
</div>
""", unsafe_allow_html=True)

st.markdown(
    f"<div class='small-top'>✅ {len(df)} lignes chargées automatiquement</div>",
    unsafe_allow_html=True
)

# ==========================
# SELECTION INTERVALLE
# ==========================
colA, colB, colC = st.columns([1,1,1])

with colB:
    start_row = st.number_input(
        "Ligne début",
        min_value=1,
        max_value=len(df),
        value=1
    )

    end_row = st.number_input(
        "Ligne fin",
        min_value=1,
        max_value=len(df),
        value=min(50, len(df))
    )

if start_row > end_row:
    st.error("Intervalle invalide.")
    st.stop()

subset = df.iloc[start_row-1:end_row]
matricules = subset["MATRICULE"].astype(str).tolist()

st.markdown("---")

# ==========================
# CONFIG CHROME
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
# BOUTON LANCEMENT
# ==========================
if st.button("🚀 Lancer la vérification"):

    matricules = df["MATRICULE"].astype(str).tolist()[:limite]

    col_page, col_progress = st.columns([2, 1])

    page_container = col_page.empty()
    progress_container = col_progress.container()

    progress_bar = progress_container.progress(0)
    status_text = progress_container.empty()

    # Stats temps réel
    stat_affecte = progress_container.empty()
    stat_non_affecte = progress_container.empty()
    stat_introuvable = progress_container.empty()
    stat_erreur = progress_container.empty()

    resultats = []

    driver = None

    try:
        driver = get_chrome_driver()

        count_affecte = 0
        count_non_affecte = 0
        count_introuvable = 0
        count_erreur = 0

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

            time.sleep(2)

            # 🔥 LIVE BROWSER EFFECT (Screenshot fluide)
            png = driver.get_screenshot_as_png()
            page_container.image(png, use_container_width=True)

            page_text = driver.page_source.lower()

            if "non affecte" in page_text:
                statut = "NON_AFFECTE"
                count_non_affecte += 1
            elif "affecte" in page_text:
                statut = "AFFECTE"
                count_affecte += 1
            elif "introuvable" in page_text:
                statut = "INTROUVABLE"
                count_introuvable += 1
            else:
                statut = "ERREUR"
                count_erreur += 1

            resultats.append({
                "matricule": m,
                "statut": statut,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # 📊 Stats temps réel
            stat_affecte.metric("✅ Affectés", count_affecte)
            stat_non_affecte.metric("❌ Non Affectés", count_non_affecte)
            stat_introuvable.metric("❓ Introuvables", count_introuvable)
            stat_erreur.metric("🔥 Erreurs", count_erreur)

            progress_bar.progress((i + 1) / len(matricules))

            # 🧠 optimisation RAM (important Render free)
            driver.delete_all_cookies()

            if i < len(matricules) - 1:
                time.sleep(1)

        progress_container.success("✅ Vérification terminée")

        df_resultats = pd.DataFrame(resultats)
        st.dataframe(df_resultats, use_container_width=True)

    except Exception as e:
        st.error(f"Erreur : {e}")

    finally:
        if driver:
            driver.quit()








