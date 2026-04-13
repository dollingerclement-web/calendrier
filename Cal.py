import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_calendar import calendar

st.set_page_config(layout="wide")
st.title("🏡 Planning de la chirouze")
st.info("Avant toute réservation merci d'envoyer une demande sur le groupe whats'app : priorité à la famille et aux anciens ;)")

# ------------------ CONNEXION GOOGLE SHEETS ------------------

@st.cache_resource
def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["CHIROUZE"], scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("Reservations maison").sheet1
    return sheet

sheet = connect_sheet()

# ------------------ CHARGEMENT DONNÉES ------------------

@st.cache_data(ttl=5)
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()

today = pd.Timestamp.today().date()

# ------------------ FORMULAIRE PRINCIPAL ------------------

st.subheader("📝 Nouvelle réservation")

col1, col2, col3,col4 = st.columns(4)

with col1:
    nom = st.text_input("Nom")

with col2:
    nb_ad = st.number_input("Adultes actifs", 1, 15, 2)
    
with col3:
    nb_en = st.number_input("Enfants", 1, 15, 2)

nb_pers=nb_ad+nb_en

with col4:
    couleur = st.color_picker("Couleur", "#3D91FF")

dates = st.date_input( "Dates du séjour", value=(today, today))

if len(dates) == 2:
    st.write("📅 Période choisie :", dates[0].strftime("%d/%m/%Y"), "→",dates[1].strftime("%d/%m/%Y"))


# ------------------ AJOUT ------------------

if st.button("➕ Ajouter réservation"):

    if len(dates) == 2 and nom:

        sheet.append_row([nom, str(dates[0]),str(dates[1]),nb_pers,nb_ad,nb_en,couleur])

        st.success("✅ Réservation ajoutée !")
        st.cache_data.clear()
        st.rerun()

    else:
        st.error("Veuillez remplir tous les champs")

# ------------------ ÉDITION / SUPPRESSION ------------------

st.markdown("---")
st.subheader("✏️ Gérer les réservations")

if not df.empty:

    options = df.apply(
        lambda row: f"{row['Membre']} ({pd.to_datetime(row['Début']).strftime('%d/%m/%Y')} → {pd.to_datetime(row['Fin']).strftime('%d/%m/%Y')})",
        axis=1
    )

    selected = st.selectbox("Réservation", options)
    index = options[options == selected].index[0]

    colA, colB = st.columns(2)

    with colA:
        if st.button("❌ Supprimer"):
            sheet.delete_rows(index + 2)
            st.success("Supprimé")
            st.cache_data.clear()


# ------------------ CALENDRIER ------------------

st.markdown("---")
st.subheader("📅 Planning")

calendar_events = []

if not df.empty:
    for _, row in df.iterrows():

        calendar_events.append({
            "title": f"{row['Membre']} ({row['Personnes']} pers.)",
            "start": pd.to_datetime(row["Début"]).date().isoformat(),
            "end": (pd.to_datetime(row["Fin"]).date() + pd.Timedelta(days=1)).isoformat(),
            "backgroundColor": row["Couleur"],
            "borderColor": row["Couleur"],
            "textColor": "#000000",
            "allDay": True
        })

calendar_options = {
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth"
    },
    "initialView": "dayGridMonth",
    "eventDisplay": "block",
    "eventOverlap": True
}

calendar(events=calendar_events, options=calendar_options)

# ------------------ FORMAT FR ------------------

st.markdown("---")
st.subheader("📊 Tableau")

if not df.empty:
    df_display = df.copy()

    df_display["Début"] = pd.to_datetime(df_display["Début"]).dt.strftime("%d/%m/%Y")
    df_display["Fin"] = pd.to_datetime(df_display["Fin"]).dt.strftime("%d/%m/%Y")

    st.dataframe(df_display, use_container_width=True)
else:
    st.info("Aucune réservation")
