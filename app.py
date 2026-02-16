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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================
# STYLE GLOBAL - BLEU NUIT
# ==========================
st.markdown("""
<style>
    /* Fond bleu nuit */
    .stApp {
        background-color: #0B1A2F;
    }
    
    html, body, [class*="css"] {
        background-color: #0B1A2F;
        color: white;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    
    /* Conteneur principal pleine largeur */
    .main .block-container {
        max-width: 100%;
        padding: 0.5rem 2rem 0rem 2rem;
        background-color: #0B1A2F;
    }
    
    /* Titre centré */
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        color: white;
        margin-top: 10px;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        letter-spacing: 1px;
        padding: 10px;
        border-bottom: 2px solid #1E3A5F;
    }
    
    /* Style des métriques */
    [data-testid="stMetric"] {
        background-color: #1E3A5F;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2C4F7C;
        margin: 5px 0;
    }
    
    [data-testid="stMetricLabel"] {
        color: #B0C4DE;
        font-size: 14px;
    }
    
    [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    /* Style des inputs */
    .stNumberInput input {
        background-color: #1E3A5F;
        color: white;
        border: 1px solid #2C4F7C;
        border-radius: 5px;
    }
    
    .stNumberInput label {
        color: #B0C4DE !important;
    }
    
    /* Style du bouton */
    .stButton button {
        background-color: #1E3A5F;
        color: white;
        border: 2px solid #2C4F7C;
        border-radius: 8px;
        padding: 10px 30px;
        font-size: 18px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        background-color: #2C4F7C;
        border-color: #3A6A9F;
    }
    
    /* Zone des captures */
    .screenshot-container {
        border: 2px solid #1E3A5F;
        border-radius: 10px;
        overflow: hidden;
        margin: 10px 0;
        background-color: #0F1F35;
    }
    
    /* Style des progressions */
    .progress-container {
        background-color: #0F1F35;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #1E3A5F;
        margin: 10px 0;
    }
    
    /* Barre de progression */
    .stProgress > div > div > div > div {
        background-color: #2E8B57 !important;
    }
    
    /* Style des dataframes */
    .dataframe-container {
        background-color: #0F1F35;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #1E3A5F;
        margin-top: 20px;
    }
    
    /* Images en plein écran */
    [data-testid="stImage"] {
        width: 100%;
        margin: 0;
        padding: 0;
    }
    
    [data-testid="stImage"] img {
        width: 100%;
        height: auto;
        border-radius: 8px;
        border: 2px solid #1E3A5F;
    }
    
    /* Texte d'information */
    .info-text {
        color: #B0C4DE;
        font-size: 14px;
        text-align: center;
        margin: 5px 0;
    }
    
    /* Ligne de séparation */
    hr {
        border-color: #1E3A5F;
        margin: 20px 0;
    }
    
    /* Messages de succès/erreur */
    .stAlert {
        background-color: #1E3A5F !important;
        color: white !important;
        border: 1px solid #2C4F7C !important;
    }
    
    /* Titre de colonnes pour l'intervalle */
    .interval-title {
        color: #B0C4DE;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 5px;
    }
    
    /* Cache les petits éléments inutiles */
    footer {display: none;}
    header {display: none;}
    
</style>
""", unsafe_allow_html=True)

# ==========================
# CHARGEMENT FICHIER
# ==========================
try:
    # Recherche du fichier avec différents formats
    fichiers_possibles = ["ABS_GENERAL.xlsx", "ABS_GENERAL.csv", "ABS_GENERAL.txt"]
    fichier_trouve = None
    
    for fichier in fichiers_possibles:
        if os.path.exists(fichier):
            fichier_trouve = fichier
            break
    
    if fichier_trouve is None:
        st.error("❌ Aucun fichier ABS_GENERAL trouvé (xlsx, csv ou txt)")
        st.stop()
    
    # Chargement selon l'extension
    if fichier_trouve.endswith('.xlsx'):
        df = pd.read_excel(fichier_trouve, engine="openpyxl")
    elif fichier_trouve.endswith('.csv'):
        df = pd.read_csv(fichier_trouve)
    else:
        df = pd.read_csv(fichier_trouve, delimiter='\t')  # Pour les txt

except Exception as e:
    st.error(f"❌ Erreur chargement : {e}")
    st.stop()

if "MATRICULE" not in df.columns:
    st.error("❌ Colonne MATRICULE absente dans le fichier.")
    st.stop()

# ==========================
# TITRE CENTRÉ
# ==========================
st.markdown("""
<div class="main-title">
    🎓 VÉRIFICATION DES STATUTS D'INSCRIPTION<br>
    <span style="font-size: 24px; color: #B0C4DE;">AFFECTÉ(E) / NON AFFECTÉ(E) 2025-2026</span>
</div>
""", unsafe_allow_html=True)

st.markdown(f"<div class='info-text'>✅ {len(df)} matricules chargés depuis {fichier_trouve}</div>", unsafe_allow_html=True)

# ==========================
# SÉLECTION DE L'INTERVALLE
# ==========================
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown('<div class="interval-title">📌 LIGNE DE DÉPART</div>', unsafe_allow_html=True)
    start_row = st.number_input(
        " ",
        min_value=1,
        max_value=len(df),
        value=1,
        key="start",
        label_visibility="collapsed"
    )

with col2:
    st.markdown('<div class="interval-title">🏁 LIGNE DE FIN</div>', unsafe_allow_html=True)
    end_row = st.number_input(
        "  ",
        min_value=start_row,
        max_value=len(df),
        value=len(df),
        key="end",
        label_visibility="collapsed"
    )

with col3:
    st.markdown('<div class="interval-title">📊 TOTAL À TRAITER</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background-color: #1E3A5F; padding: 8px; border-radius: 5px; text-align: center;">
        <span style="font-size: 24px; font-weight: 700;">{end_row - start_row + 1}</span>
        <span style="color: #B0C4DE;"> / {len(df)}</span>
    </div>
    """, unsafe_allow_html=True)

if start_row > end_row:
    st.error("❌ La ligne de fin doit être supérieure ou égale à la ligne de début.")
    st.stop()

st.markdown("---")

# ==========================
# BOUTON LANCEMENT
# ==========================
if st.button("🚀 LANCER LA VÉRIFICATION AUTOMATIQUE", use_container_width=True):
    
    # Sélection des matricules selon l'intervalle choisi
    matricules = df.iloc[start_row-1:end_row]["MATRICULE"].astype(str).tolist()
    
    # CRÉATION DES COLONNES : 2/3 GAUCHE (CAPTURES) - 1/3 DROITE (PROGRESSIONS)
    col_captures, col_progress = st.columns([2, 1])
    
    with col_captures:
        st.markdown('<div class="screenshot-container">', unsafe_allow_html=True)
        screenshot_placeholder = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_progress:
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        
        # Barre de progression
        st.markdown("### 📊 PROGRESSION")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Statistiques en temps réel
        st.markdown("### 📈 STATISTIQUES")
        col_stat1, col_stat2 = st.columns(2)
        
        with col_stat1:
            stat_affecte = st.empty()
            stat_introuvable = st.empty()
        
        with col_stat2:
            stat_non_affecte = st.empty()
            stat_erreur = st.empty()
        
        # Informations supplémentaires
        st.markdown("### ℹ️ INFOS")
        info_container = st.empty()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialisation des compteurs
    count_affecte = 0
    count_non_affecte = 0
    count_introuvable = 0
    count_erreur = 0
    resultats = []
    driver = None
    
    try:
        # Configuration Chrome optimisée
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")  # Réduit les logs
        
        service = Service("/usr/local/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)
        
        # Boucle de traitement
        for i, matricule in enumerate(matricules):
            # Mise à jour des infos
            status_text.markdown(f"""
            ### 🔄 TRAITEMENT EN COURS
            - **Matricule :** {matricule}
            - **Ligne :** {start_row + i} / {end_row}
            - **Progression :** {i+1}/{len(matricules)}
            """)
            
            # Navigation
            driver.get("https://agfne.sigfne.net/vas/interface-edition-documents-sigfne/")
            
            # Recherche
            wait = WebDriverWait(driver, 15)
            champ = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            
            champ.clear()
            champ.send_keys(str(matricule))
            champ.send_keys(Keys.RETURN)
            
            time.sleep(2)
            
            # 🖥 Capture d'écran (2/3 de l'écran)
            png = driver.get_screenshot_as_png()
            screenshot_placeholder.image(png, use_container_width=True)
            
            # Analyse du résultat
            page_text = driver.page_source.lower()
            
            if "non affecte" in page_text:
                statut = "NON AFFECTÉ"
                count_non_affecte += 1
            elif "affecte" in page_text:
                statut = "AFFECTÉ"
                count_affecte += 1
            elif "introuvable" in page_text:
                statut = "INTROUVABLE"
                count_introuvable += 1
            else:
                statut = "ERREUR"
                count_erreur += 1
            
            # Enregistrement
            resultats.append({
                "Matricule": matricule,
                "Statut": statut,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # 📊 Mise à jour stats
            stat_affecte.metric("✅ AFFECTÉS", count_affecte)
            stat_non_affecte.metric("❌ NON AFFECTÉS", count_non_affecte)
            stat_introuvable.metric("❓ INTROUVABLES", count_introuvable)
            stat_erreur.metric("⚠️ ERREURS", count_erreur)
            
            # Info supplémentaire
            info_container.info(f"💾 RAM utilisée : {i+1}/{len(matricules)} - Optimisation active")
            
            # Barre de progression
            progress_bar.progress((i + 1) / len(matricules))
            
            # 🧠 Optimisation RAM
            driver.delete_all_cookies()
            
            if i < len(matricules) - 1:
                time.sleep(1)
        
        # FIN DU TRAITEMENT
        with col_progress:
            st.success("✅ VÉRIFICATION TERMINÉE AVEC SUCCÈS")
            
            # Résumé final
            total = len(matricules)
            st.markdown(f"""
            ### 📊 RÉSUMÉ FINAL
            - ✅ Affectés : {count_affecte} ({count_affecte/total*100:.1f}%)
            - ❌ Non affectés : {count_non_affecte} ({count_non_affecte/total*100:.1f}%)
            - ❓ Introuvables : {count_introuvable} ({count_introuvable/total*100:.1f}%)
            - ⚠️ Erreurs : {count_erreur} ({count_erreur/total*100:.1f}%)
            """)
        
        # Affichage des résultats
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        st.markdown("### 📋 DÉTAIL DES RÉSULTATS")
        df_resultats = pd.DataFrame(resultats)
        st.dataframe(df_resultats, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Erreur pendant le traitement : {e}")
    
    finally:
        if driver:
            driver.quit()

else:
    # Message d'instruction
    st.markdown("""
    <div style="text-align: center; padding: 50px; background-color: #0F1F35; border-radius: 10px; border: 1px solid #1E3A5F;">
        <h2 style="color: white;">👆 CLIQUEZ SUR LE BOUTON POUR COMMENCER</h2>
        <p style="color: #B0C4DE;">La vérification commencera à la ligne <strong>{}</strong> jusqu'à la ligne <strong>{}</strong></p>
        <p style="color: #B0C4DE; font-size: 14px;">Les captures d'écran apparaîtront dans la partie gauche (2/3 de l'écran)<br>
        Les statistiques et la progression seront affichées à droite (1/3 de l'écran)</p>
    </div>
    """.format(start_row, end_row), unsafe_allow_html=True)









