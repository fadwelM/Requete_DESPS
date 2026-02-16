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

st.set_page_config(page_title="Vérification Inscription", page_icon="🎓", layout="wide")

st.title("🎓 Système de Vérification Inscription")
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
# FONCTION DE VERIFICATION
# ==========================
def verifier_matricule(driver, matricule):

    try:
        driver.get("https://agfne.sigfne.net/vas/interface-edition-documents-sigfne/")
        wait = WebDriverWait(driver, 15)

        champ = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )

        champ.clear()
        champ.send_keys(str(matricule))
        champ.send_keys(Keys.RETURN)

        time.sleep(3)

        page_text = driver.page_source.lower()

        if "non affecte" in page_text:
            statut = "NON_AFFECTE"
        elif "affecte" in page_text:
            statut = "AFFECTE"
        elif "introuvable" in page_text or "non trouvé" in page_text:
            statut = "INTROUVABLE"
        else:
            statut = "INDETERMINE"

        return {
            "statut": statut,
            "matricule": matricule,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {
            "statut": "ERREUR",
            "matricule": matricule,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "erreur": str(e)[:100]
        }


# ==========================
# INTERFACE STREAMLIT
# ==========================

# Sélecteur du nombre de lignes à traiter
limite = st.number_input(
    "Nombre de matricules à traiter",
    min_value=1,
    max_value=2000,
    value=10
)

# Charger automatiquement le fichier du repository
try:
    if not os.path.exists("ABS_GENERAL.xlsx"):
        st.error("❌ Le fichier ABS_GENERAL.xlsx est introuvable dans le repository.")
        st.stop()

    df = pd.read_excel("ABS_GENERAL.xlsx", engine="openpyxl")

except Exception as e:
    st.error(f"Erreur chargement fichier : {e}")
    st.stop()


# Vérifier colonne
if "MATRICULE" not in df.columns:
    st.error("❌ Colonne 'MATRICULE' introuvable.")
    st.stop()

st.success(f"✅ {len(df)} lignes chargées automatiquement")

# Bouton lancement
# Bouton lancement
if st.button("🚀 Lancer la vérification"):

    matricules = df["MATRICULE"].astype(str).tolist()[:limite]

    # Layout 2/3 - 1/3
    col_page, col_progress = st.columns([2, 1])

    # Screenshot live
    png = driver.get_screenshot_as_png()
    page_container.image(png, use_container_width=True)
    progress_container = col_progress.container()

    resultats = []
    driver = None

    try:
        driver = get_chrome_driver()

        progress_bar = progress_container.progress(0)
        status_text = progress_container.empty()

        for i, m in enumerate(matricules):

            status_text.markdown(f"### 🔄 Traitement {i+1}/{len(matricules)}")
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

            # 🔥 Affichage LIVE de la page dans les 2/3 écran
            page_html = driver.page_source
            page_container.components.v1.html(
                page_html,
                height=800,
                scrolling=True
            )

            page_text = page_html.lower()

            if "non affecte" in page_text:
                statut = "NON_AFFECTE"
            elif "affecte" in page_text:
                statut = "AFFECTE"
            elif "introuvable" in page_text:
                statut = "INTROUVABLE"
            else:
                statut = "INDETERMINE"

            resultats.append({
                "matricule": m,
                "statut": statut,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            progress_bar.progress((i + 1) / len(matricules))

            if i < len(matricules) - 1:
                time.sleep(random.uniform(2, 4))

        progress_container.success("✅ Vérification terminée")

        df_resultats = pd.DataFrame(resultats)
        st.dataframe(df_resultats, use_container_width=True)

    except Exception as e:
        st.error(f"Erreur : {e}")

    finally:
        if driver:
            driver.quit()



