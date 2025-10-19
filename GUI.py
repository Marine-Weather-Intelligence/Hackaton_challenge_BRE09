import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import time 

# Importations nécessaires pour l'affichage du résultat
import plotly.graph_objects as go
import plotly.express as px
import os
import xml.etree.ElementTree as ET

# ---------------- CONFIG & SETUP ----------------

st.set_page_config(layout="wide", page_title="OdysSea - Planificateur")

# --- Définition des zones disponibles ---
zones_disponibles = {
    "Département": [
        "Morbihan", "Finistère", "Côtes d'Armor", "Ille-et-Vilenne",
        "Guadeloupe", "Martinique", "Guyane", "La Réunion", "Mayotte"
    ],
    "Région": ["Bretagne", "Nouvelle-Aquitaine", "Provence-Alpes-Côte d'Azur"],
    "Pays": ["France", "Espagne", "Italie"]
}

# --- DONNÉES DE ROUTES FICTIVES POUR LA DÉMO (INTÉGRATION) ---
morbihan_routes_detaillees = {
    'MyTrip': [
        [47.4905, -3.0988, '2025-10-21T10:00', 'D', 'P'], #Port Haliguen
        [47.4756, -3.0677, '2025-10-21T10:15', 'I'],
        [47.4696, -3.0552, '2025-10-21T10:15', 'I'],
        [47.4454, -3.0522, '2025-10-21T10:30', 'I'],
        [47.4212, -3.051, '2025-10-21T10:45', 'I'],
        [47.3971, -3.0491, '2025-10-21T11:00', 'I'],
        [47.3729, -3.0469, '2025-10-21T11:15', 'I'],
        [47.3487, -3.0452, '2025-10-21T11:30', 'I'],
        [47.3247, -3.0429, '2025-10-21T11:45', 'I'],
        [47.307297, -3.054521, '2025-10-21T11:50', 'I'],
        [47.3045, -3.0587, '2025-10-21T12:00', 'I'],
        [47.30466667, -3.06166667, '2025-10-21T12:07', 'A', 'A'], #Port An Dro - Belle ile
        [47.30466667, -3.06166667, '2025-10-22T10:00', 'D', 'A'], #Port An Dro - Belle ile
        [47.3028, -3.06, '2025-10-22T10:00', 'I'],
        [47.3145, -3.02, '2025-10-22T10:15', 'I'],
        [47.3278, -2.99, '2025-10-22T10:30', 'I'],
        [47.3401, -2.95, '2025-10-22T10:45', 'I'],
        [47.3433, -2.92, '2025-10-22T11:00', 'I'],
        [47.349169, -2.891802, '2025-10-22T11:05', 'I'],
        [47.3458, -2.88, '2025-10-22T11:15', 'I'],
        [47.3438, -2.8753, '2025-10-22T11:17', 'A', 'P'], #Port d'Hoedic
        [47.3438, -2.8753, '2025-10-24T10:00', 'D', 'P'], #Port d'Hoedic
        [47.3451, -2.8747, '2025-10-24T10:00', 'I'],
        [47.3588, -2.8978, '2025-10-24T10:15', 'I'],
        [47.3726, -2.9217, '2025-10-24T10:30', 'I'],
        [47.3840, -2.9447, '2025-10-24T10:45', 'I'],
        [47.385, -2.945333333, '2025-10-24 10:47', 'A', 'A'],#Rade De Houat - Houat
        [47.385, -2.945333333, '2025-10-25T10:00', 'I','A'],#Rade De Houat - Houat
        [47.370637, -2.945898, '2025-10-25T10:10', 'I'],
        [47.3693, -2.9667, '2025-10-25T10:15', 'I'],
        [47.3846, -2.9859, '2025-10-25T10:30', 'I'],
        [47.394234, -3.010287, '2025-10-25T10:35', 'I'],
        [47.4018, -3.0042, '2025-10-25T10:45', 'I'],
        [47.416903, -2.992817, '2025-10-25T10:50', 'I'],
        [47.4363, -3.0409, '2025-10-25T11:15', 'I'],
        [47.4535, -3.0592, '2025-10-25T11:30', 'I'],
        [47.4707, -3.0776, '2025-10-25T11:45', 'I'],
        [47.4879, -3.0960, '2025-10-25T12:00', 'I'],
        [47.4905, -3.0988, '2025-10-21T12:02', 'D', 'P'], #Port Haliguen
    ],
}

# --- FONCTIONS PLOTLY POUR L'AFFICHAGE DU RÉSULTAT ---
def add_danger_zones_from_gpx(fig):
    gpx_folder = 'GPX_Warnings-20251018T185509Z-1-001' 
    if not os.path.isdir(gpx_folder):
        st.info("ℹ️ Le dossier de zones de danger (GPX) n'a pas été trouvé. Seules les routes sont affichées.", icon="⚠️")
        return

    all_polygons_lats, all_polygons_lons, all_polygons_descs = [], [], []
    for filename in os.listdir(gpx_folder):
        if not filename.endswith('.gpx'):
            continue
        
        full_path = os.path.join(gpx_folder, filename)
        try:
            ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
            tree = ET.parse(full_path)
            root = tree.getroot()

            for track in root.findall('gpx:trk', ns):
                points = track.findall('.//gpx:trkpt', ns)
                poly_lats = [float(p.get('lat')) for p in points]
                poly_lons = [float(p.get('lon')) for p in points]

                desc_element = track.find('gpx:desc', ns)
                description = desc_element.text.strip() if desc_element is not None else "Danger non spécifié"

                if poly_lats and (poly_lats[0] != poly_lats[-1] or poly_lons[0] != poly_lons[-1]):
                    poly_lats.append(poly_lats[0])
                    poly_lons.append(poly_lons[0])

                if poly_lats:
                    all_polygons_lats.extend(poly_lats + [None])
                    all_polygons_lons.extend(poly_lons + [None])
                    all_polygons_descs.extend([description] * len(poly_lats) + [None])
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier {filename}: {e}")
    
    if all_polygons_lats:
        fig.add_trace(go.Scattermap(
            mode="lines",
            lat=all_polygons_lats,
            lon=all_polygons_lons,
            fill="toself",
            fillcolor="rgba(255, 0, 0, 0.3)",
            line=dict(width=0),
            name="Zones de danger",
            customdata=all_polygons_descs,
            hovertemplate="<b>DANGER</b><br>%{customdata}<extra></extra>"
        ))

def display_routes_avec_traces_separees(routes_dict):
    fig = go.Figure()
    colors = px.colors.qualitative.Plotly

    rows = []
    for i, (route_id, coords) in enumerate(routes_dict.items()):
        for c in coords:
            lat, lon, time, typ = c[:4]
            cat = c[4] if len(c) == 5 else ""
            rows.append({
                "Lat": lat, "Lon": lon, "Time": time, "Type": typ,
                "Categorie": cat, "Route_ID": route_id,
                "Route_Color": colors[i % len(colors)]
            })
    df = pd.DataFrame(rows)

    if df.empty:
        fig.add_annotation(text="Aucune donnée de route à afficher.", showarrow=False, xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    for route_id in df["Route_ID"].unique():
        route_df = df[df["Route_ID"] == route_id]
        fig.add_trace(go.Scattermap(
            mode="lines",
            lat=route_df["Lat"], lon=route_df["Lon"],
            line=dict(width=2, color=route_df["Route_Color"].iloc[0]),
            showlegend=False
        ))

    category_map = {"P": "Port", "A": "Ancre", "B": "Bouée"}
    color_map = {"P": "orange", "A": "red", "B": "green"}

    for cat, label in category_map.items():
        df_cat = df[df["Categorie"] == cat]
        if not df_cat.empty:
            fig.add_trace(go.Scattermap(
                mode="markers",
                lat=df_cat["Lat"], lon=df_cat["Lon"],
                marker=dict(symbol="circle", size=9, color=color_map[cat], allowoverlap=True),
                name=label,
                customdata=df_cat[["Route_ID", "Type", "Time"]],
                hovertemplate="<b>Route %{customdata[0]}</b><br>Type: %{customdata[1]}<br>Heure: %{customdata[2]|%H:%M}<extra></extra>"
            ))

    add_danger_zones_from_gpx(fig)

    fig.update_layout(
        map_style="open-street-map",
        map_zoom=9,
        map_center=dict(lat=df["Lat"].mean(), lon=df["Lon"].mean()),
        title="Itinéraires, Points d'Intérêt et Zones de Danger",
        margin=dict(r=0, t=40, l=0, b=0),
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        map_layers=[{
            "sourcetype": "raster",
            "source": ["https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png"],
            "below": "traces",
            "opacity": 0.8
        }],
        height=300 
    )
    
    return fig

# ---------------- SESSION STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "accueil"
if "calculate_plan" not in st.session_state:
    st.session_state.calculate_plan = False
if "geo_type" not in st.session_state:
    st.session_state.geo_type = "Département" 
if "region" not in st.session_state:
    st.session_state.region = None
# Initialisation des ancrages sélectionnés à une liste vide
if "selected_anchors" not in st.session_state:
    st.session_state.selected_anchors = []

# --- Fonction de transition avec chargement ---
def start_planning(selected_type, selected_region):
    with st.spinner(f"Préparation de la zone **{selected_region}**. Veuillez patienter..."):
        time.sleep(2) 
        st.session_state.geo_type = selected_type
        st.session_state.region = selected_region
        st.session_state.page = "preparation"
        
        # Réinitialiser la liste d'ancrages lors du changement de zone/démarrage
        st.session_state.selected_anchors = []
        if 'multiselect_anchors' in st.session_state:
             st.session_state.multiselect_anchors = []
        
        st.rerun() 
        
# Fonction de callback pour le calcul
def trigger_calculation():
    # 1. Simuler un temps de calcul AVANT de changer l'état
    with st.spinner("Calcul des routes optimales en cours... ⏳"):
        time.sleep(3) 
    # 2. Mettre à jour l'état
    st.session_state.calculate_plan = True
    st.session_state.page = "resultat"
    
# ===============================================
# ---------------- PAGE ACCUEIL ----------------
# ===============================================
if st.session_state.page == "accueil":
    
    st.markdown("""
        <style>
        .main-title {font-size: 3.5em; margin: 0; line-height: 1; padding-top: 10px;}
        .subtitle-text {font-size: 1.2em; color: #aaa; margin-top: -10px;}
        [data-testid="stVerticalBlock"] > div > [data-testid="stVerticalBlock"] {padding-top: 0px;}
        </style>
        """, unsafe_allow_html=True)
        
    col_logo, col_text, col_spacer = st.columns([2, 4, 10], gap="medium") 

    with col_logo:
        try:
            # Logo plus grand ici (200px)
            st.image("logo.png", width=1000) 
        except FileNotFoundError:
            st.markdown("<span style='font-size: 70px;'>⚓</span>", unsafe_allow_html=True) 

    with col_text:
        st.markdown('<h1 class="main-title">OdysSea</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle-text">Planificateur de navigation</p>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    st.subheader("Choisir votre zone de navigation 🗺️")

    col_geo, col_zone = st.columns([1, 2])

    geo_type_options = [""] + list(zones_disponibles.keys())
    type_aire = col_geo.selectbox(
        "Type d'aire géographique", 
        geo_type_options, 
        index=0, 
        key="accueil_type_aire"
    )

    liste_zones = [""]
    if type_aire:
        liste_zones.extend(zones_disponibles.get(type_aire, []))
    
    region = col_zone.selectbox(
        f"Sélectionnez une zone ({type_aire})" if type_aire else "Sélectionnez une zone", 
        liste_zones,
        index=0, 
        key="accueil_region",
        disabled=not type_aire
    )
    
    st.session_state.region = region 
    
    disabled_button = not (type_aire and region)

    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Commencer la planification 🚢", width='stretch', disabled=disabled_button):
        start_planning(type_aire, region)
        
# ===============================================
# ---------------- PAGE PREPARATION ----------------
# ===============================================
elif st.session_state.page == "preparation":
    st.title(f"Préparation du trajet - {st.session_state.region}")

    # --- Chargement / Données fictives ---
    COLUMN_TYPE = 'types'
    fictional_data = {
        "name": ["Port A", "Port B", "Port C", "Port D", "Port E", "Port F"],
        "lat": [47.5, 48.0, 47.6, 47.7, 47.8, 47.9],
        "lon": [-3.0, -4.0, -3.2, -3.5, -3.8, -3.3],
        "seabed": ["sable", "rochers", "sable;rochers", "sable", "rochers", "vases"],
        COLUMN_TYPE: ["Port de Plaisance", "Mouillage Organisé", "Port de Plaisance", "Mouillage Organisé", "Ancrage Sauvage", "Port de Plaisance"], 
        "services": ["eau;wifi", "douches;carburant", "eau;carburant", "wifi;electricité", "eau;douches", "wifi;eau"],
        "wind_sectors": ["N;NE", "SO;O", "N;SO", "O;SO", "NE;E", "E;SE"]
    }
    
    if st.session_state.region == "Morbihan":
        try:
            df = pd.read_csv("ports_morbihan.csv") 
            if COLUMN_TYPE not in df.columns:
                df[COLUMN_TYPE] = 'Port Inconnu' 
        except FileNotFoundError:
            df = pd.DataFrame(fictional_data)
    else:
        df = pd.DataFrame(fictional_data)

    df['lat'] = df['lat'].astype(float)
    df['lon'] = df['lon'].astype(float)

    list_columns = ["seabed","services","wind_sectors"]
    for col in list_columns:
        df[col] = df[col].fillna("").apply(lambda x:[v.strip() for v in x.replace(";",",").split(",") if v.strip()])

    all_types = sorted(df[COLUMN_TYPE].unique().tolist())
    all_seabeds = sorted(list(set(item for sublist in df['seabed'] for item in sublist)))


    # --- Affichage de la zone grisée et désactivée ---
    st.subheader("Choix de la zone") 
    
    col_geo_prep, col_zone_prep = st.columns([1, 2])
    
    geo_type_options_prep = list(zones_disponibles.keys())
    if st.session_state.geo_type in geo_type_options_prep:
        geo_type_index = geo_type_options_prep.index(st.session_state.geo_type)
    else: 
        geo_type_options_prep.insert(0, "")
        geo_type_index = 0
    
    col_geo_prep.selectbox("Type d'aire géographique", geo_type_options_prep, index=geo_type_index, disabled=True, key="prep_geo_type")
    
    liste_zones_prep = zones_disponibles.get(st.session_state.geo_type, [])
    if st.session_state.region in liste_zones_prep:
        zone_index = liste_zones_prep.index(st.session_state.region)
    else: 
        liste_zones_prep.insert(0, st.session_state.region if st.session_state.region else "")
        zone_index = 0
    
    col_zone_prep.selectbox(f"Zone: {st.session_state.geo_type}", liste_zones_prep, index=zone_index, disabled=True, key="prep_zone")
    st.markdown("---")
    # ---------------------------------------------


    # Onglets préparation
    prep_tabs = st.tabs(["Port & dates", "Ancrages", "Contraintes de navigation", "Contraintes quotidiennes"])

    # -------- Onglet Port & dates (Départ = Arrivée) --------
    with prep_tabs[0]:
        
        col_controls, col_map = st.columns([1, 1], gap="large") 

        with col_controls:
            st.subheader("Port de départ (et d'arrivée)")
            point_depart = st.selectbox("Port de départ", df['name'], key="port_depart_prep")
            point_arrivee = point_depart 

            st.markdown("#### Planification du temps total")
            
            col_dep_date, col_dep_time = st.columns(2)
            
            current_date = datetime.today().date()
            default_hour_8am = datetime.strptime("08:00", "%H:%M").time()

            with col_dep_date:
                date_depart = st.date_input("Date départ", min_value=current_date, value=current_date, key="date_depart")
            
            if date_depart == current_date:
                default_time_depart = max(datetime.now().time(), default_hour_8am)
            else:
                default_time_depart = default_hour_8am

            with col_dep_time:
                heure_depart = st.time_input("Heure départ", value=default_time_depart, key="heure_depart")
            
            dt_depart = datetime.combine(date_depart, heure_depart)
            
            st.markdown("---")

            choix_jours_ou_date = st.radio(
                "Mode de planification :", 
                ["Nombre de jours sur l’eau", "Date/heure de retour maximum"],
                horizontal=True,
                key="choix_jours_ou_date"
            )

            dt_arrivee = dt_depart 
            
            if choix_jours_ou_date == "Nombre de jours sur l’eau":
                col_arr1, col_arr2 = st.columns(2)
                with col_arr1:
                    heure_arrivee_max = st.time_input("Heure d'arrivée maximum du retour", value=datetime.strptime("17:00", "%H:%M").time(), key="heure_arrivee_mode1")
                with col_arr2:
                    nb_jours = st.number_input("Nombre de jours sur l’eau", min_value=1, value=2, key="nb_jours")
                    
                dt_arrivee = dt_depart + timedelta(days=nb_jours)
                dt_arrivee = dt_arrivee.replace(hour=heure_arrivee_max.hour, minute=heure_arrivee_max.minute)
                
                st.info(f"Retour Maximum estimé : **{dt_arrivee.strftime('%Y-%m-%d')}** à **{dt_arrivee.strftime('%H:%M')}**")
                    
            else: 
                col_arr1, col_arr2 = st.columns(2)
                with col_arr1:
                    date_arrivee = st.date_input("Date d'arrivée maximum", value=(dt_depart.date() + timedelta(days=1)), key="date_arrivee_prep")
                with col_arr2:
                    heure_arrivee = st.time_input("Heure d'arrivée maximum", value=(dt_depart + timedelta(hours=1)).time(), key="heure_arrivee_prep")
                
                dt_arrivee = datetime.combine(date_arrivee, heure_arrivee)

        
        with col_map:
            st.subheader("Carte des ports (Départ/Arrivée)")
            map_center = df[df['name']==point_depart][['lat','lon']].values[0] if not df[df['name']==point_depart].empty else [47.5, -3.0]
            m = folium.Map(location=map_center, zoom_start=10)
            for _, row in df.iterrows():
                color = 'green' if row['name']==point_depart else 'blue'
                folium.Marker([row['lat'], row['lon']], popup=row['name'], icon=folium.Icon(color=color)).add_to(m)
            st_folium(m, height=450, width=None, key="map_ports_prep") 


    # -------- Onglets Ancrages, Contraintes de navigation, Contraintes quotidiennes --------
    
    with prep_tabs[1]:
        st.subheader("Filtrage et sélection des étapes (Ports et Ancrages)")
        
        point_depart = st.session_state.get('port_depart_prep', df['name'].iloc[0] if not df.empty else None)
        
        st.markdown("##### Critères de recherche")
        col_filtre_type, col_filtre_seabed = st.columns(2)

        with col_filtre_type:
            selected_type = col_filtre_type.selectbox("Type d'Ancrage :", options=["Tous"] + all_types, key="filter_type_single")
        
        with col_filtre_seabed:
            selected_seabeds = st.multiselect("Type de fond (seabed) :", options=all_seabeds, default=all_seabeds, key="filter_seabeds")

        df_anchors = df[df['name'] != point_depart].copy()
        if selected_type != "Tous":
            df_anchors = df_anchors[df_anchors[COLUMN_TYPE] == selected_type]
        if selected_seabeds:
            df_anchors = df_anchors[df_anchors['seabed'].apply(lambda x: any(s in x for s in selected_seabeds))]
        available_anchors = df_anchors['name'].tolist()

        st.markdown("---")
        st.markdown("##### Ports disponibles pour le mouillage")
        
        def select_all_anchors():
            st.session_state.multiselect_anchors = available_anchors[:]
        def clear_all_anchors():
            st.session_state.multiselect_anchors = []

        col_select_all, col_clear_all = st.columns(2)
        with col_select_all:
            st.button("Sélectionner tout ✅", on_click=select_all_anchors, width='stretch')
        with col_clear_all:
            st.button("Désélectionner tout ❌", on_click=clear_all_anchors, width='stretch')

        if not available_anchors:
            st.info("Aucun port ne correspond à vos critères de filtres.")
            st.session_state.selected_anchors = []
        else:
            
            if "multiselect_anchors" not in st.session_state:
                current_selection = []
            else:
                current_selection = [a for a in st.session_state.multiselect_anchors if a in available_anchors]
            
            st.session_state.selected_anchors = st.multiselect(
                f"Ports et ancrages intermédiaires à considérer ({len(available_anchors)} trouvés) :",
                options=available_anchors,
                key="multiselect_anchors" 
            )

        st.markdown("---")
        st.subheader("Visualisation des étapes")
        
        map_center = df[['lat','lon']].mean().tolist() if not df.empty else [47.5, -3.0]
        m_anchors = folium.Map(location=map_center, zoom_start=9)

        for _, row in df.iterrows():
            if row['name'] == point_depart:
                color = 'blue'
                icon_type = 'flag'
            elif row['name'] in st.session_state.selected_anchors:
                color = 'green'
                icon_type = 'anchor'
            elif row['name'] in available_anchors:
                color = 'lightblue'
                icon_type = 'info-sign'
            else:
                color = 'gray'
                icon_type = 'remove'

            folium.Marker(
                [row['lat'], row['lon']], 
                popup=f"**{row['name']}**<br>Type: {row[COLUMN_TYPE]}<br>Fond: {', '.join(row['seabed'])}", 
                icon=folium.Icon(color=color, icon=icon_type)
            ).add_to(m_anchors)

        st_folium(m_anchors, height=450, width=None, key="map_anchors")


    with prep_tabs[2]:
        st.subheader("Contraintes météorologiques et nautiques")
        st.markdown("##### Limites Météo")
        col_vent, col_vague = st.columns(2)
        
        with col_vent:
            st.slider("Vitesse de Vent Maximum (Noeuds)", 0, 50, 30, key="max_vent")
        with col_vague:
            st.slider("Hauteur de Vague Maximale (Mètres)", 0.0, 5.0, 2.0, 0.1, key="max_vague")

        st.markdown("---")
        st.markdown("##### Performance du Bateau")

        col_angle_remontee, col_angle_descente = st.columns(2)
        
        with col_angle_remontee:
            st.slider("Angle de Remontée au vent (°)", 30, 90, 45, key="angle_min")
            st.caption("Angle minimum entre le vent et la route (cap) pour la remontée au vent.")
        
        with col_angle_descente:
            st.slider("Angle de Descente au vent (°)", 90, 180, 160, key="angle_max")
            st.caption("Angle maximum entre le vent et la route (cap) en descente sous le vent.")

    with prep_tabs[3]:
        st.subheader("Contraintes de temps et de rythme quotidien")

        st.markdown("##### Horaires d'opération quotidiens")
        col_daily_dep, col_daily_arr = st.columns(2)

        with col_daily_dep:
            st.time_input("Heure de départ quotidienne maximale", 
                          value=datetime.strptime("09:00", "%H:%M").time(),
                          key="max_daily_departure_time")

        with col_daily_arr:
            st.time_input("Heure d'arrivée quotidienne maximale", 
                          value=datetime.strptime("16:00", "%H:%M").time(), 
                          key="max_daily_arrival_time")

        st.markdown("---")
        st.markdown("##### Rythme de l'itinéraire")

        col_freq_unit, col_freq_n = st.columns([2, 1])

        with col_freq_unit:
            frequency_unit = st.selectbox(
                "Fréquence de changement de destination :", 
                ["Jour", "Semaine"],
                key="frequency_unit"
            )
        
        with col_freq_n:
            st.number_input(
                f"Tous les N ({frequency_unit}s)", 
                min_value=1, 
                value=1, 
                key="frequency_n"
            )

        st.caption("Détermine la fréquence à laquelle le planificateur doit trouver une nouvelle étape éloignée de la destination précédente.")


    # -------- Bouton Calculer --------
    st.markdown("---")
    if st.button("Calculer ma route 🧭", width='stretch', on_click=trigger_calculation):
        st.rerun() 

# ===============================================
# ---------------- PAGE RESULTAT ----------------
# ===============================================
elif st.session_state.page == "resultat":
    st.title(f"Résultat du plan de route - {st.session_state.region}")
    
    st.markdown("""
        <style>
        /* 1. Espaceur pour le centrage vertical (hauteur définie par l'utilisateur: 50px) */
        .spacer-200 {
            height: 50px; 
        }
        
        /* 2. Augmentation de la taille de la police pour le corps et l'en-tête du DataFrame */
        .stDataFrame > div:first-child > div:first-child .st-ag-row,
        .stDataFrame > div:first-child > div:first-child .st-ag-header-cell {
            font-size: 2.0em !important; 
            line-height: 2.5; 
        }
        
        /* 3. Police plus petite pour le libellé de warning */
        .small-warning-text {
             font-size: 0.7em;
        }
        </style>
        """, unsafe_allow_html=True)

    col_fiche, col_carte = st.columns([1, 1], gap="large") 

    # --- COLONNE FICHE DE ROUTE ---
    with col_fiche:
        st.subheader("Fiche de route détaillée 📝")
        st.write("Voici la feuille de route optimisée :")
        
        route_data = {
            "Jour": ["Jour 1", "Jour 2", "Jour 3", "Jour 4", "Jour 5"],
            "Trajet": ["Port Haliguen - Port An dro", "Port An dro - Port d'Hoedic", "Port d'Hoedic", "Port d'Hoedic - Houat Grande Plage", "Houat Grande Plage - Port Haliguen"],
            "Départ": ["21/10 - 10h", "22/10 - 10h", "—", "24/10 - 10h", "25/10 - 10h"],
            "Info": ["", "", "⚠️", "", ""], 
            "Temps de Nav.": ["5h", "4h30", "--", "4h", "6h"],
            "Type d'étape": ["Ancre", "Port", "Port", "Ancre", "Ancre"],
            "Avertissement": ["", "", "Météo trop mauvaise pour naviguer. Recommandation: rester au port.", "", ""] 
        }
        route_bilan = pd.DataFrame(route_data)
        
        st.markdown("<div class='spacer-200'></div>", unsafe_allow_html=True)

        st.dataframe(
            route_bilan,
            hide_index=True,
            width='stretch', # Utilisation de 'stretch'
            column_config={
                "Avertissement": None, 
                "Info": st.column_config.TextColumn(
                    "Info",
                    help="Avertissements météo ou événements.",
                    width="small"
                ),
                "Temps de Nav.": st.column_config.TextColumn(width="small"),
                "Type d'étape": st.column_config.TextColumn(width="small"),
            },
        )
        
        st.markdown(f"""
             <p class='small-warning-text'>
             *⚠️ Jour 3: Météo trop mauvaise pour naviguer.*
             </p>
        """, unsafe_allow_html=True)


    # --- COLONNE CARTE ---
    with col_carte:
        st.subheader("Carte de l'itinéraire et zones de danger 🗺️")
        st.write("Visualisation interactive de la route optimisée, incluant les zones de danger relevées.")
        
        try:
            fig = display_routes_avec_traces_separees(morbihan_routes_detaillees)
            st.plotly_chart(
            fig, 
            # Correction: 'width' est déprécié. Utiliser use_container_width=True
            use_container_width=True, 
            # Toutes les options Plotly spécifiques sont dans 'config'
            config={'displayModeBar': True} 
        )
        except Exception as e:
            st.error(f"Impossible d'afficher la carte : {e}")



    st.markdown("---")
    if st.button("Retour à la planification", key="back_to_prep"):
        st.session_state.page = "preparation"
        st.rerun()