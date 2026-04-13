import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_calendar import calendar

st.set_page_config(layout="wide")
st.title("🏡 Gestion de la Maison Familiale")

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

# ------------------ LECTURE DES DONNÉES ------------------

@st.cache_data(ttl=5)
def load_data():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

df = load_data()

# ------------------ FORMULAIRE ------------------

today = pd.Timestamp.today().date()

with st.sidebar:
    st.header("📝 Réserver un séjour")
    
    nom = st.text_input("Nom")
    nb_pers = st.number_input("Nombre de personnes", 1, 15, 2)
    
    dates = st.date_input(
        "Dates du séjour",
        value=(today, today),
        min_value=today,
        max_value=today + pd.Timedelta(days=365)
    )
    
    couleur = st.color_picker("Couleur", "#3D91FF")

    if st.button("Ajouter"):
        if len(dates) == 2 and nom:
            
            # 🔥 Vérification des conflits
            conflit = False
            for _, row in df.iterrows():
                debut_exist = pd.to_datetime(row["Début"]).date()
                fin_exist = pd.to_datetime(row["Fin"]).date()

                if not (dates[1] < debut_exist or dates[0] > fin_exist):
                    conflit = True
                    break

           
            else:
                sheet.append_row([
                    nom,
                    str(dates[0]),
                    str(dates[1]),
                    nb_pers,
                    couleur
                ])
                st.success("✅ Réservation ajoutée !")
                st.cache_data.clear()

        else:
            st.error("Veuillez remplir tous les champs")



# ------------------ CALENDRIER ------------------

calendar_events = []

if not df.empty:
    for _, row in df.iterrows():
        calendar_events.append({
            "title": f"{row['Membre']} ({row['Personnes']} pers.)",
            "start": pd.to_datetime(row["Début"]).date().isoformat(),
            "end": (pd.to_datetime(row["Fin"]).date() + pd.Timedelta(days=1)).isoformat(),
            "backgroundColor": row["Couleur"],
            "borderColor": row["Couleur"],
            "textColor": "#FFFFFF",
            "allDay": True
        })

col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📅 Planning")
    
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth"
        },
        "initialView": "dayGridMonth",
    }

    calendar(events=calendar_events, options=calendar_options)

with col2:
    st.subheader("📊 Résumé")

    if not df.empty:
        st.write(f"Total réservations : {len(df)}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucune réservation")

st.markdown("---")
st.subheader("✏️ Modifier / Supprimer")

if not df.empty:
    options = df.apply(lambda row: f"{row['Membre']} ({row['Début']} → {row['Fin']})", axis=1)
    selected = st.selectbox("Choisir une réservation", options)

    index = options[options == selected].index[0]

    if st.button("❌ Supprimer"):
        sheet.delete_rows(index + 2)  # +2 car header + index 0
        st.success("Supprimé !")
        st.cache_data.clear()

    if st.button("✏️ Modifier"):
        st.session_state.edit_index = index

if "edit_index" in st.session_state:
    i = st.session_state.edit_index
    row = df.iloc[i]

    st.sidebar.markdown("### ✏️ Édition")

    new_nom = st.sidebar.text_input("Nom", row["Membre"])
    new_nb = st.sidebar.number_input("Personnes", 1, 15, int(row["Personnes"]))

    new_dates = st.sidebar.date_input(
        "Dates",
        value=(
            pd.to_datetime(row["Début"]).date(),
            pd.to_datetime(row["Fin"]).date()
        )
    )

    if st.sidebar.button("💾 Enregistrer"):
        sheet.delete_rows(i + 2)
        sheet.insert_row([
            new_nom,
            str(new_dates[0]),
            str(new_dates[1]),
            new_nb,
            row["Couleur"]
        ], i + 2)

        st.success("Modifié !")
        del st.session_state.edit_index
        st.cache_data.clear()
