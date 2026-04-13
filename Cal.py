import streamlit as st
import pandas as pd
from streamlit_calendar import calendar

st.set_page_config(layout="wide") # Mode large pour mieux voir le calendrier
st.title("🏡 Gestion de la Maison Familiale")
today = pd.Timestamp.today().date()
# --- SIMULATION DE BASE DE DONNÉES ---
if 'reservations' not in st.session_state:
    # On ajoute une colonne 'Personnes' et 'Couleur'
    st.session_state.reservations = pd.DataFrame(columns=["Membre", "Début", "Fin", "Personnes", "Couleur"])

# --- FORMULAIRE D'INSCRIPTION ---
with st.sidebar:
    st.header("📝 Réserver un séjour")
    nom = st.text_input("Nom de la famille / Personne")
    nb_pers = st.number_input("Nombre de personnes", min_value=1, max_value=15, value=2)
    dates = st.date_input("Dates du séjour", value=[today,today].date(), num_months=2)
    couleur = st.color_picker("Choisissez une couleur pour le calendrier", "#3D91FF")
    
    if st.button("Ajouter au calendrier"):
        if len(dates) == 2 and nom:
            nouvelle_resa = {
                "Membre": nom, 
                "Début": dates[0], 
                "Fin": dates[1], 
                "Personnes": nb_pers,
                "Couleur": couleur
            }
            st.session_state.reservations = pd.concat([
                st.session_state.reservations, 
                pd.DataFrame([nouvelle_resa])
            ], ignore_index=True)
            st.success(f"Réservation pour {nom} ajoutée !")
        else:
            st.error("Veuillez remplir tous les champs.")

# --- PRÉPARATION DES ÉVÉNEMENTS POUR LE CALENDRIER ---
calendar_events = []
for _, row in st.session_state.reservations.iterrows():
    calendar_events.append({
        "title": f"👥 {row['Membre']} ({row['Personnes']} pers.)",
        "start": row["Début"].isoformat(),
        "end": row["Fin"].isoformat(),
        "backgroundColor": row["Couleur"],
        "borderColor": row["Couleur"],
        "allDay": True
    })

# --- AFFICHAGE ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📅 Planning Occupation")
    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "editable": False,
        "selectable": True,
    }
    calendar(events=calendar_events, options=calendar_options)

with col2:
    st.subheader("📊 Résumé")
    if not st.session_state.reservations.empty:
        # Affichage du nombre total de personnes actuellement prévues
        st.write(f"Total réservations : {len(st.session_state.reservations)}")
        st.dataframe(st.session_state.reservations[["Membre", "Personnes"]], hide_index=True)
    else:
        st.info("Aucune donnée.")
