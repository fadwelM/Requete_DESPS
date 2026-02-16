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
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

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

        # Attendre le champ matricule
        champ = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )

        champ.clear()
        champ.send_keys(str(matricule))
        champ.send_keys(Keys.RETURN)

        # Attendre que la page affiche un résultat
        wait.until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)

        page_text = driver.page_source.lower()

        # Analyse statut
        if "non affecte" in page_text:
            statut = "NON_AFFECTE"
            details = "Candidat non affecté"
        elif "affecte" in page_text:
            statut = "AFFECTE"
            details = "Candidat affecté"
        elif "introuvable" in page_text or "non trouvé" in page_text:
            statut = "INTROUVABLE"
            details = "Matricule non trouvé"
        else:
            statut = "INDETERMINE"
            details = "Résultat non identifié"

        return {
            "statut": statut,
            "niveau": "NON_DEFINI",
            "details": details,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return {
            "statut": "ERREUR",
            "niveau": "NON_DEFINI",
            "details": str(e)[:100],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# ==========================
# INTERFACE STREAMLIT
# ==========================
df = pd.read_excel("ABS_GENERAL.xlsx", engine="openpyxl")

    if "MATRICULE" not in df.columns:
        st.error("❌ Colonne 'MATRICULE' introuvable.")
    else:

        st.success(f"✅ {len(df)} lignes chargées")

        if st.button("🚀 Lancer la vérification"):

            matricules = df["MATRICULE"].astype(str).tolist()[:limite]

            progress = st.progress(0)
            status = st.empty()

            resultats = []

            driver = None

            try:
                driver = get_chrome_driver()

                for i, m in enumerate(matricules):

                    status.text(f"Traitement {i+1}/{len(matricules)} : {m}")

                    resultat = verifier_matricule(driver, m)
                    resultat["matricule"] = m
                    resultats.append(resultat)

                    progress.progress((i + 1) / len(matricules))

                    if i < len(matricules) - 1:
                        time.sleep(random.uniform(2, 4))

                st.success("✅ Terminé")

                df_resultats = pd.DataFrame(resultats)

                st.dataframe(df_resultats, use_container_width=True)

                csv = df_resultats.to_csv(index=False)

                st.download_button(
                    "📥 Télécharger CSV",
                    csv,
                    file_name=f"resultats_bepc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"Erreur : {e}")

            finally:
                if driver:
                    driver.quit()

else:
    st.info("👆 Chargez un fichier Excel pour commencer.")

