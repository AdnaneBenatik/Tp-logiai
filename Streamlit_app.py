import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="LogiAI | Prédiction de retard", page_icon="🚚", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1050px; padding-top: 2rem;}
.hero {padding: 1.5rem 1.8rem; border-radius: 16px; background: linear-gradient(110deg,#123a62,#1976a3); color:white; margin-bottom:1.4rem;}
.hero h1 {color:white; margin:0; font-size:2.2rem;}
.hero p {margin:.5rem 0 0; color:#e5f3fa;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🚚 LogiAI</h1><p>Anticipez les retards de livraison grâce au Machine Learning.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Connexion à l’API")
    api_url = st.text_input("Adresse FastAPI", value=API_URL).rstrip("/")
    if st.button("Vérifier la connexion", use_container_width=True):
        try:
            response = requests.get(f"{api_url}/health", timeout=5)
            response.raise_for_status()
            info = response.json()
            if info.get("model_loaded") is False:
                st.warning("API accessible, mais modèle non chargé. Lancez l'entraînement.")
            else:
                st.success("API accessible !")
            st.json(info)
        except requests.RequestException as exc:
            st.error(f"Connexion impossible : {exc}")
    st.caption("Démarrez FastAPI avant d'utiliser cette interface.")

st.subheader("📦 Informations sur la livraison")
with st.form("prediction_form"):
    col1, col2 = st.columns(2, gap="large")
    with col1:
        distance_km = st.number_input("Distance (km)", min_value=1.0, max_value=1000.0, value=120.0, step=1.0)
        poids_kg = st.number_input("Poids (kg)", min_value=0.1, max_value=5000.0, value=500.0, step=1.0)
        heure_depart = st.slider("Heure de départ", min_value=0, max_value=23, value=8, format="%d h")
        type_vehicule = st.selectbox("Type de véhicule", ["moto", "fourgon", "camion"], index=2)
    with col2:
        pluie_mm = st.number_input("Pluie (mm)", min_value=0.0, max_value=100.0, value=15.0, step=0.5)
        trafic_index = st.slider("Indice de trafic (0 = fluide, 10 = saturé)", min_value=0.0, max_value=10.0, value=7.0, step=0.5)
        nb_arrets = st.number_input("Nombre d'arrêts", min_value=0, max_value=30, value=5, step=1)
    submitted = st.form_submit_button("🔎 Prédire le risque de retard", type="primary", use_container_width=True)

if submitted:
    payload = {
        "distance_km": distance_km,
        "poids_kg": poids_kg,
        "heure_depart": heure_depart,
        "pluie_mm": pluie_mm,
        "trafic_index": trafic_index,
        "nb_arrets": nb_arrets,
        "type_vehicule": type_vehicule,
    }
    try:
        with st.spinner("Analyse de la livraison en cours..."):
            response = requests.post(f"{api_url}/v1/predict", json=payload, timeout=20)
        if response.status_code == 422:
            st.error("Certaines données ne sont pas acceptées par l'API.")
            st.json(response.json())
        elif response.status_code == 503:
            st.error("Le modèle n'est pas chargé. Exécutez `python -m logiai.train`, puis redémarrez FastAPI.")
        else:
            response.raise_for_status()
            result = response.json()
            probability = float(result["probabilite_retard"])
            threshold = float(result.get("seuil", 0.4))
            alert = bool(result.get("alerte", probability >= threshold))
            st.divider()
            st.subheader("📊 Résultat de la prédiction")
            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("Probabilité de retard", f"{probability:.1%}")
            metric2.metric("Seuil d'alerte", f"{threshold:.0%}")
            metric3.metric("Version du modèle", str(result.get("model_version", "Non précisée")))
            st.progress(min(max(probability, 0.0), 1.0))
            if alert:
                st.error("⚠️ Risque de retard élevé : cette livraison dépasse le seuil d'alerte.")
            else:
                st.success("✅ Risque de retard limité : cette livraison reste sous le seuil d'alerte.")
            with st.expander("Voir la réponse JSON de l'API"):
                st.json(result)
    except requests.ConnectionError:
        st.error("Impossible de joindre FastAPI. Vérifiez que le serveur est lancé sur le port 8000.")
    except requests.Timeout:
        st.error("L'API met trop de temps à répondre. Réessayez.")
    except (requests.RequestException, ValueError, KeyError) as exc:
        st.error(f"Erreur pendant la prédiction : {exc}")

st.caption("LogiAI • Interface Streamlit connectée à FastAPI")
