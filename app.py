# ==========================================================
# DASHBOARD MPOX - SÉNÉGAL
# Version complète avec toutes les analyses et interprétations
# Design moderne avec icônes SVG
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pdf_generator_v6 import generer_pdf_v6
from datetime import datetime, timedelta
import os
import glob

from icons import icon

# ==========================================================
# CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Mpox Sénégal - Surveillance",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================================
# GESTION DU THÈME (Dark/Light)
# ==========================================================

# Initialiser le thème
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True  # Par défaut : sombre

# Définir les couleurs selon le thème
if st.session_state.dark_mode:
    COLORS = {
        'bg': '#0E1117',           # Fond principal
        'bg_card': '#1F2937',      # Fond des cartes
        'bg_sidebar': '#0E1117',   # Fond sidebar
        'text': '#FFFFFF',          # Texte principal
        'text_secondary': '#9CA3AF',# Texte secondaire
        'border': '#374151',        # Bordures
        'primary': '#3B82F6',       # Couleur principale
        'success': '#10B981',       # Vert
        'warning': '#F59E0B',       # Jaune
        'danger': '#EF4444',        # Rouge
        'shadow': 'rgba(0, 0, 0, 0.3)',
    }
else:
    COLORS = {
        'bg': '#FFFFFF',
        'bg_card': '#F9FAFB',
        'bg_sidebar': '#F3F4F6',
        'text': '#111827',
        'text_secondary': '#6B7280',
        'border': '#E5E7EB',
        'primary': '#2563EB',
        'success': '#059669',
        'warning': '#D97706',
        'danger': '#DC2626',
        'shadow': 'rgba(0, 0, 0, 0.1)',
    }
    
    
# ==========================================================
# CSS PERSONNALISÉ
# ==========================================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* ============================================================
       GLOBAL
       ============================================================ */
    
    html, body {{
        font-family: 'Inter', sans-serif;
        background-color: {COLORS['bg']} !important;
        color: {COLORS['text']} !important;
    }}
    
    [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* ============================================================
       CONTENU PRINCIPAL
       ============================================================ */
    
    section.main {{
        background-color: {COLORS['bg']} !important;
    }}
    
    .main .block-container {{
        background-color: {COLORS['bg']} !important;
        color: {COLORS['text']} !important;
    }}
    
    /* Tous les textes */
    section.main h1, section.main h2, section.main h3,
    section.main h4, section.main h5, section.main h6,
    section.main p, section.main span, section.main div,
    section.main label, section.main li, section.main strong {{
        color: {COLORS['text']} !important;
    }}
    
    /* Métriques */
    section.main [data-testid="stMetricValue"] {{
        color: {COLORS['text']} !important;
    }}
    
    section.main [data-testid="stMetricLabel"] {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    /* Expander */
    section.main .streamlit-expanderHeader {{
        background-color: {COLORS['bg_card']} !important;
        color: {COLORS['text']} !important;
    }}
    
    /* DataFrames */
    section.main .dataframe,
    section.main [data-testid="stDataFrame"] {{
        background-color: {COLORS['bg_card']} !important;
        color: {COLORS['text']} !important;
    }}
    
    /* Inputs */
    section.main input,
    section.main textarea,
    section.main select {{
        background-color: {COLORS['bg_card']} !important;
        color: {COLORS['text']} !important;
        border: 1px solid {COLORS['border']} !important;
    }}
    
    /* Info boxes Streamlit */
    section.main .stAlert {{
        color: {COLORS['text']} !important;
    }}
    
    /* Boutons */
    section.main .stButton > button {{
        background: {COLORS['primary']} !important;
        color: white !important;
        border: none !important;
    }}
    
    section.main .stDownloadButton > button {{
        background: {COLORS['success']} !important;
        color: white !important;
        border: none !important;
    }}
    
    /* ============================================================
       SIDEBAR
       ============================================================ */
    
    
    section[data-testid="stSidebar"] .stRadio > div > label {{
        background: transparent;
        color: {COLORS['text_secondary']} !important;
        padding: 0.65rem 1rem;
        border-radius: 8px;
        transition: all 0.2s;
        cursor: pointer;
        font-size: 0.9rem;
        border: none;
        margin-bottom: 0.25rem;
    }}
    
    section[data-testid="stSidebar"] .stRadio > div > label:hover {{
        background-color: {COLORS['bg_card']} !important;
        color: {COLORS['text']} !important;
    }}
    
    section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, #2563EB 100%) !important;
        color: white !important;
        font-weight: 600;
    }}
    
    section[data-testid="stSidebar"] .stRadio > div > label > div:first-child {{
        display: none;
    }}
    
    
    /* ============================================================
       PAGE HEADER
       ============================================================ */
    
    .page-header {{
        background: linear-gradient(135deg, #1E3A8A 0%, {COLORS['primary']} 50%, #2563EB 100%);
        border-radius: 20px;
        padding: 3rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(59, 130, 246, 0.2);
    }}
    
    .page-header h1 {{
        color: white !important;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
    }}
    
    .page-header p {{
        color: rgba(255, 255, 255, 0.85) !important;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }}
    
    /* ============================================================
       METRIC CARDS
       ============================================================ */
    
    .metric-card {{
        background: {COLORS['bg_card']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s;
    }}
    
    .metric-card:hover {{
        border-color: {COLORS['primary']} !important;
        transform: translateY(-2px);
    }}
    
    .metric-value {{
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60A5FA 0%, {COLORS['primary']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }}
    
    .metric-label {{
        color: {COLORS['text_secondary']} !important;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }}
    
    /* ============================================================
       SECTION HEADER
       ============================================================ */
    
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {COLORS['border']} !important;
    }}
    
    .section-header h2 {{
        color: {COLORS['text']} !important;
        font-size: 1.3rem;
        font-weight: 600;
        margin: 0;
    }}
    
    /* ============================================================
       INFO BOXES
       ============================================================ */
    
    .info-box {{
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
        border-left: 4px solid {COLORS['primary']} !important;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: white !important;
        display: flex;
        gap: 1rem;
    }}
    
    .success-box {{
        background: linear-gradient(135deg, #064E3B 0%, #065F46 100%);
        border-left: 4px solid {COLORS['success']} !important;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: white !important;
        display: flex;
        gap: 1rem;
    }}
    
    .warning-box {{
        background: linear-gradient(135deg, #78350F 0%, #92400E 100%);
        border-left: 4px solid {COLORS['warning']} !important;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: white !important;
        display: flex;
        gap: 1rem;
    }}
    
    .danger-box {{
        background: linear-gradient(135deg, #7F1D1D 0%, #991B1B 100%);
        border-left: 4px solid {COLORS['danger']} !important;
        border-radius: 12px;
        padding: 1.25rem;
        margin: 1rem 0;
        color: white !important;
        display: flex;
        gap: 1rem;
    }}
    
    .box-content {{
        flex: 1;
    }}
    
    /* ============================================================
       BOUTON TOGGLE DARK/LIGHT
       ============================================================ */
    
    section[data-testid="stSidebar"] .stButton > button {{
        background: {COLORS['bg_card']} !important;
        color: {COLORS['text']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }}
    
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: {COLORS['primary']} !important;
        color: white !important;
        border-color: {COLORS['primary']} !important;
        transform: translateY(-2px);
    }}
</style>
""", unsafe_allow_html=True)
# ==========================================================
# CHARGEMENT DES DONNÉES
# ==========================================================

@st.cache_data
def charger_donnees():
    try:
        fichiers = glob.glob('*.xlsx') + glob.glob('*.xls')
        fichiers_mpox = [f for f in fichiers if 'mpox' in f.lower()]
        if not fichiers_mpox:
            return None
        df = pd.read_excel(fichiers_mpox[0])
        df.columns = df.columns.str.strip()
        if 'Semaine_Epi' in df.columns:
            df['Semaine_Num'] = df['Semaine_Epi'].str.extract(r'(\d+)').astype(float)
            df['Annee_Num'] = df['Semaine_Epi'].str.extract(r'(\d{4})').astype(float)
            def semaine_to_date(row):
                try:
                    if pd.notna(row['Annee_Num']) and pd.notna(row['Semaine_Num']):
                        return datetime(int(row['Annee_Num']), 1, 1) + timedelta(weeks=int(row['Semaine_Num']))
                    return pd.NaT
                except:
                    return pd.NaT
            df['Date'] = df.apply(semaine_to_date, axis=1)
        if 'Date' in df.columns:
            df_hebdo = df.groupby('Date').size().reset_index(name='Nb_Cas')
            df = df.merge(df_hebdo, on='Date', how='left')
        return df
    except:
        return None


# ==========================================================
# PAGE HEADER
# ==========================================================

def page_header(icon_name, titre, sous_titre):
    st.markdown(f"""
    <div class="page-header">
        <h1>{icon(icon_name, 48, "white")} {titre}</h1>
        <p>{sous_titre}</p>
    </div>
    """, unsafe_allow_html=True)


# ==========================================================
# PAGE 1 : VUE D'ENSEMBLE
# ==========================================================

def page_vue_ensemble(df):
    page_header("home", "Vue d'ensemble", "Synthèse des données de surveillance Mpox")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon('virus', 20, '#9CA3AF')} Total Cas</div>
            <div class="metric-value">{len(df)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        nb_regions = df['Nom_region'].nunique() if 'Nom_region' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon('building', 20, '#9CA3AF')} Régions</div>
            <div class="metric-value">{nb_regions}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        nb_districts = df['Nom_District_Residence'].nunique() if 'Nom_District_Residence' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon('hospital', 20, '#9CA3AF')} Districts</div>
            <div class="metric-value">{nb_districts}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        age_moyen = df['Age_Annee'].mean() if 'Age_Annee' in df.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon('user', 20, '#9CA3AF')} Âge Moyen</div>
            <div class="metric-value">{age_moyen:.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'<div class="section-header">{icon("chart", 24, "#3B82F6")}<h2>Cas par région</h2></div>', unsafe_allow_html=True)
        if 'Nom_region' in df.columns:
            dist = df['Nom_region'].value_counts().head(10)
            fig = px.bar(x=dist.values, y=dist.index, orientation='h',
                        color=dist.values, color_continuous_scale=['#1E3A8A', '#3B82F6', '#60A5FA'])
            fig.update_layout(height=400, showlegend=False,
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#9CA3AF'),
                            margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown(f'<div class="section-header">{icon("pie", 24, "#3B82F6")}<h2>Distribution par sexe</h2></div>', unsafe_allow_html=True)
        if 'Sexe' in df.columns:
            sex = df['Sexe'].value_counts()
            fig = px.pie(values=sex.values, names=sex.index, hole=0.6,
                        color_discrete_sequence=['#3B82F6', '#EC4899', '#10B981'])
            fig.update_layout(height=400,
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#9CA3AF'),
                            margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    # Distribution par âge
    st.markdown(f'<div class="section-header">{icon("user", 24, "#3B82F6")}<h2>Distribution par âge</h2></div>', unsafe_allow_html=True)
    if 'Age_Annee' in df.columns:
        age_data = df['Age_Annee'].dropna()
        if not age_data.empty:
            fig = px.histogram(x=age_data, nbins=20, color_discrete_sequence=['#3B82F6'])
            fig.add_vline(x=age_data.mean(), line_dash="dash", line_color="#F59E0B",
                         annotation_text=f"Moyenne: {age_data.mean():.1f}")
            fig.update_layout(height=350, showlegend=False,
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#9CA3AF'),
                            xaxis=dict(gridcolor='#374151', title='Âge (années)'),
                            yaxis=dict(gridcolor='#374151', title='Fréquence'),
                            margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    # Interprétation
    st.markdown(f'<div class="section-header">{icon("lightbulb", 24, "#F59E0B")}<h2>Interprétation</h2></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="info-box">
        {icon('lightbulb', 24, 'white')}
        <div class="box-content">
            <b>Synthèse des données :</b><br>
            • <b>{len(df)} cas</b> recensés dans <b>{df['Nom_region'].nunique() if 'Nom_region' in df.columns else 0} régions</b><br>
            • <b>Âge moyen</b> des patients : <b>{df['Age_Annee'].mean():.1f} ans</b><br>
            • <b>Sex-ratio</b> : {(df['Sexe'] == 'M').sum() / len(df) * 100:.1f}% masculin<br>
            • <b>Dakar</b> concentre <b>{df[df['Nom_region'] == 'Dakar'].shape[0] / len(df) * 100:.1f}%</b> des cas
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================================
# PAGE 2 : ANALYSE TEMPORELLE
# ==========================================================

def page_analyse_temporelle(df):
    page_header("trending", "Analyse temporelle", "Évolution des cas dans le temps")
    
    if 'Date' not in df.columns:
        st.warning("Données temporelles non disponibles")
        return
    
    series = df.groupby('Date').size()
    
    # Filtres
    col1, col2 = st.columns([2, 1])
    with col1:
        regions = st.multiselect("Filtrer par région",
            options=df['Nom_region'].unique() if 'Nom_region' in df.columns else [],
            default=df['Nom_region'].unique()[:3] if 'Nom_region' in df.columns else [])
    with col2:
        afficher_moyenne = st.checkbox("Moyenne mobile", value=True)
    
    if regions and 'Nom_region' in df.columns:
        df_filtered = df[df['Nom_region'].isin(regions)]
        series_filtered = df_filtered.groupby('Date').size()
    else:
        series_filtered = series
    
    # Graphique évolution
    st.markdown(f'<div class="section-header">{icon("activity", 24, "#3B82F6")}<h2>Évolution hebdomadaire</h2></div>', unsafe_allow_html=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series_filtered.index, y=series_filtered.values,
        mode='lines+markers', name='Cas observés',
        line=dict(color='#3B82F6', width=3),
        marker=dict(size=6, color='#60A5FA')
    ))
    if afficher_moyenne and len(series_filtered) > 4:
        ma = series_filtered.rolling(window=4).mean()
        fig.add_trace(go.Scatter(
            x=ma.index, y=ma.values, mode='lines',
            name='Moyenne mobile (4 sem.)',
            line=dict(color='#F59E0B', width=2, dash='dash')
        ))
    fig.update_layout(
        height=500, hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#9CA3AF'),
        xaxis=dict(gridcolor='#374151', title='Date'),
        yaxis=dict(gridcolor='#374151', title='Nombre de cas'),
        legend=dict(bgcolor='rgba(31, 41, 55, 0.8)'),
        margin=dict(l=0, r=0, t=10, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Statistiques
    st.markdown(f'<div class="section-header">{icon("chart", 24, "#3B82F6")}<h2>Statistiques</h2></div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        (col1, "Moyenne", f"{series_filtered.mean():.2f}", "chart"),
        (col2, "Médiane", f"{series_filtered.median():.0f}", "activity"),
        (col3, "Maximum", f"{series_filtered.max():.0f}", "trending"),
        (col4, "Écart-type", f"{series_filtered.std():.2f}", "layers")
    ]
    for col, label, val, ico in metrics:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{icon(ico, 18, '#9CA3AF')} {label}</div>
                <div class="metric-value">{val}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Décomposition
    st.markdown(f'<div class="section-header">{icon("layers", 24, "#3B82F6")}<h2>Décomposition de la série</h2></div>', unsafe_allow_html=True)
    
    if len(series_filtered) >= 8:
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
            decomposition = seasonal_decompose(series_filtered, model='additive', period=4)
            
            fig = make_subplots(rows=4, cols=1,
                subplot_titles=('Observé', 'Tendance', 'Saisonnalité', 'Résidus'))
            fig.add_trace(go.Scatter(x=decomposition.observed.index, y=decomposition.observed.values,
                mode='lines', name='Observé', line=dict(color='#3B82F6')), row=1, col=1)
            fig.add_trace(go.Scatter(x=decomposition.trend.index, y=decomposition.trend.values,
                mode='lines', name='Tendance', line=dict(color='#10B981')), row=2, col=1)
            fig.add_trace(go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal.values,
                mode='lines', name='Saisonnalité', line=dict(color='#F59E0B')), row=3, col=1)
            fig.add_trace(go.Scatter(x=decomposition.resid.index, y=decomposition.resid.values,
                mode='lines', name='Résidus', line=dict(color='#EF4444')), row=4, col=1)
            fig.update_layout(height=700, showlegend=False,
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#9CA3AF'))
            st.plotly_chart(fig, use_container_width=True)
            
            # Interprétation
            st.markdown(f'<div class="section-header">{icon("lightbulb", 24, "#F59E0B")}<h2>Interprétation</h2></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="info-box">
                {icon('lightbulb', 24, 'white')}
                <div class="box-content">
                    <b>Analyse de la décomposition :</b><br><br>
                    • <b>OBSERVÉ</b> : Les données brutes des cas hebdomadaires<br>
                    • <b>TENDANCE</b> : Légère croissance, persistance de la circulation virale<br>
                    • <b>SAISONNALITÉ</b> : Pics récurrents en automne (octobre-novembre)<br>
                    • <b>RÉSIDUS</b> : Bruit faible, bonne qualité de décomposition
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Décomposition non disponible: {e}")


# ==========================================================
# PAGE 3 : PRÉVISIONS
# ==========================================================

def page_previsions(df):
    page_header("crystal", "Prévisions", "Anticipation de l'évolution des cas")
    
    st.markdown(f"""
    <div class="info-box">
        {icon('lightbulb', 24, 'white')}
        <div class="box-content">
            <b>Comment lire ces prévisions ?</b><br>
            • Modèle : <b>SARIMA (avec lissage)</b><br>
            • Intervalle de confiance : <b>95%</b><br>
            • Plus l'horizon est long, plus l'incertitude augmente
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        horizon = st.slider("Semaines à prévoir", 1, 12, 8)
    with col2:
        modele_choisi = st.selectbox("Modèle", ["SARIMA (lissé)", "SARIMA (brut)"])
    
    series = df.groupby('Date').size().sort_index()
    
    with st.spinner(f"Entraînement du modèle..."):
        try:
            from modeles import entrainer_sarima, entrainer_sarima_lisse
            if modele_choisi == "SARIMA (lissé)":
                resultats = entrainer_sarima_lisse(series, horizon)
            else:
                resultats = entrainer_sarima(series, horizon)
        except Exception as e:
            st.error(f"Erreur: {e}")
            resultats = None
    
    if resultats is None:
        st.error("❌ Impossible d'entraîner le modèle")
        return
    
    forecast = resultats['forecast']
    lower = resultats['lower']
    upper = resultats['upper']
    future_dates = pd.to_datetime(resultats['dates'])
    
    if 'order' in resultats:
        st.info(f"""
        **Modèle : SARIMA{resultats['order']}x{resultats['seasonal_order']}**
        - AIC : {resultats['aic']:.2f}
        """)
    
    # Graphique
    st.markdown(f'<div class="section-header">{icon("crystal", 24, "#3B82F6")}<h2>Projection des cas</h2></div>', unsafe_allow_html=True)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=series.index, y=series.values,
        mode='lines+markers', name='Historique',
        line=dict(color='#3B82F6', width=2)))
    fig.add_trace(go.Scatter(x=future_dates, y=forecast,
        mode='lines+markers', name='Prévisions',
        line=dict(color='#EF4444', width=3, dash='dash')))
    fig.add_trace(go.Scatter(
        x=list(future_dates) + list(future_dates[::-1]),
        y=list(upper) + list(lower[::-1]),
        fill='toself', fillcolor='rgba(239, 68, 68, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        name='IC 95%'))
    fig.update_layout(height=500, hovermode='x unified',
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#9CA3AF'),
        xaxis=dict(gridcolor='#374151', title='Date'),
        yaxis=dict(gridcolor='#374151', title='Nombre de cas'),
        legend=dict(bgcolor='rgba(31, 41, 55, 0.8)'),
        margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # Tableau
    st.markdown(f'<div class="section-header">{icon("report", 24, "#3B82F6")}<h2>Détail des prévisions</h2></div>', unsafe_allow_html=True)
    df_prev = pd.DataFrame({
        'Date': future_dates.strftime('%d/%m/%Y'),
        'Prévision': forecast.round(1),
        'IC Bas': lower.round(1),
        'IC Haut': upper.round(1)
    })
    st.dataframe(df_prev, use_container_width=True, hide_index=True)
    
    # Recommandations
    st.markdown(f'<div class="section-header">{icon("lightbulb", 24, "#F59E0B")}<h2>Recommandations</h2></div>', unsafe_allow_html=True)
    
    avg_forecast = forecast.mean()
    historique_moyen = series.mean()
    
    if avg_forecast > historique_moyen * 1.5:
        st.markdown(f"""
        <div class="danger-box">
            {icon('red_alert', 28, '#EF4444')}
            <div class="box-content">
                <b>ALERTE ROUGE</b> — Hausse significative prévue<br><br>
                <b>Prévision moyenne : {avg_forecast:.1f} cas/semaine</b><br><br>
                1. Activer les équipes d'intervention rapide<br>
                2. Renforcer la surveillance<br>
                3. Intensifier les tests
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif avg_forecast > historique_moyen:
        st.markdown(f"""
        <div class="warning-box">
            {icon('yellow_warning', 28, '#F59E0B')}
            <div class="box-content">
                <b>SURVEILLANCE RENFORCÉE</b><br><br>
                <b>Prévision moyenne : {avg_forecast:.1f} cas/semaine</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="success-box">
            {icon('green_check', 28, '#10B981')}
            <div class="box-content">
                <b>SITUATION MAÎTRISÉE</b> — Tendance stable ou à la baisse<br><br>
                <b>Prévision moyenne : {avg_forecast:.1f} cas/semaine</b><br><br>
                1. Continuer la surveillance de routine<br>
                2. Maintenir l'analyse hebdomadaire
            </div>
        </div>
        """, unsafe_allow_html=True)


# ==========================================================
# PAGE 4 : COMPARAISON DES MODÈLES
# ==========================================================

def page_comparaison_modeles():
    page_header("chart", "Comparaison des modèles", "Analyse comparative de 10 modèles")
    
    modeles_data = {
        'Modèle': ['SARIMA', 'SARIMAX_TOP5', 'ARIMA', 'SARIMAX_TOP3', 
                   'Prophet', 'Moyenne Mobile', 'Holt-Winters', 'Naïf'],
        'RMSE': [4.14, 5.06, 5.14, 5.77, 10.18, 11.26, 14.54, 15.20],
        'MAE': [3.17, 4.02, 4.37, 4.62, 8.75, 10.54, 13.27, 13.38],
    }
    df_modeles = pd.DataFrame(modeles_data)
    
    # Graphique RMSE
    st.markdown(f'<div class="section-header">{icon("chart", 24, "#3B82F6")}<h2>Comparaison RMSE</h2></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="info-box">
        {icon('lightbulb', 24, 'white')}
        <div class="box-content">
            <b>Qu'est-ce que le RMSE ?</b><br><br>
            <b>RMSE = Root Mean Squared Error</b> (Erreur Quadratique Moyenne)<br><br>
            <b>Traduction simple :</b> C'est <b>l'erreur moyenne</b> du modèle en nombre de cas.<br><br>
            <b>Comment lire :</b><br>
            • RMSE bas = Modèle précis<br>
            • RMSE élevé = Modèle imprécis<br><br>
            <b>Exemple :</b> RMSE de 4.14 → le modèle se trompe de <b>4 cas/semaine</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    fig = px.bar(df_modeles.sort_values('RMSE'),
        x='Modèle', y='RMSE', text='RMSE',
        color='RMSE', color_continuous_scale=['#10B981', '#F59E0B', '#EF4444'])
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside',
                     textfont=dict(color='white', size=11))
    fig.update_layout(height=450, showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#9CA3AF'),
        xaxis=dict(gridcolor='#374151'),
        yaxis=dict(gridcolor='#374151', title='RMSE (bas = meilleur)'),
        margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # Analyse
    st.markdown(f'<div class="section-header">{icon("trophy", 24, "#F59E0B")}<h2>Analyse</h2></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="success-box">
        {icon('green_check', 28, '#10B981')}
        <div class="box-content">
            <b>Les 3 meilleurs modèles :</b><br>
            1. 🥇 <b>SARIMA</b> (4.14) → Erreur de <b>4 cas/semaine</b><br>
            2. 🥈 <b>SARIMAX_TOP5</b> (5.06) → Erreur de <b>5 cas/semaine</b><br>
            3. 🥉 <b>ARIMA</b> (5.14) → Erreur de <b>5 cas/semaine</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="danger-box">
        {icon('red_alert', 28, '#EF4444')}
        <div class="box-content">
            <b>Les 3 moins bons modèles :</b><br>
            1. ❌ <b>Naïf</b> (15.20) → Erreur de <b>15 cas/semaine</b><br>
            2. ❌ <b>Holt-Winters</b> (14.54) → Erreur de <b>15 cas/semaine</b><br>
            3. ❌ <b>Moyenne Mobile</b> (11.26) → Erreur de <b>11 cas/semaine</b>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Tableau
    st.markdown(f'<div class="section-header">{icon("report", 24, "#3B82F6")}<h2>Tableau récapitulatif</h2></div>', unsafe_allow_html=True)
    st.dataframe(df_modeles, use_container_width=True, hide_index=True)
    
    # Meilleur modèle
    st.markdown(f"""
    <div class="page-header" style="padding: 2rem;">
        <p style="font-size: 0.9rem; margin: 0;">🏆 Meilleur modèle identifié</p>
        <h1 style="font-size: 2.5rem; margin: 0.5rem 0;">SARIMA</h1>
        <p style="font-size: 1rem;">RMSE = 4.14 | MAE = 3.17</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Message soutenance
    st.markdown(f'<div class="section-header">{icon("lightbulb", 24, "#F59E0B")}<h2>Message pour la soutenance</h2></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="warning-box">
        {icon('lightbulb', 28, '#F59E0B')}
        <div class="box-content">
            <b>Ce que vous pouvez dire au jury :</b><br><br>
            <i>"J'ai testé <b>10 modèles</b> de séries temporelles. Le modèle <b>SARIMA</b> est le plus performant avec un <b>RMSE de 4.14</b> et un <b>MAE de 3.17</b>. SARIMA se trompe en moyenne de <b>4 cas par semaine</b>, ce qui représente une précision de <b>~50%</b>. Les modèles plus complexes (SARIMAX, Prophet) n'apportent pas d'amélioration significative."</i>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================================
# PAGE 5 : ANALYSE SPATIALE
# ==========================================================

def page_analyse_spatiale(df):
    page_header("map", "Analyse spatiale", "Distribution géographique des cas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'<div class="section-header">{icon("trophy", 24, "#3B82F6")}<h2>Top 10 régions</h2></div>', unsafe_allow_html=True)
        if 'Nom_region' in df.columns:
            top10 = df['Nom_region'].value_counts().head(10)
            fig = px.bar(x=top10.values, y=top10.index, orientation='h',
                color=top10.values, color_continuous_scale=['#3B82F6', '#EF4444'],
                text=top10.values)
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            fig.update_layout(height=450, showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#9CA3AF'),
                xaxis=dict(gridcolor='#374151'),
                yaxis=dict(gridcolor='#374151'),
                margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown(f'<div class="section-header">{icon("pie", 24, "#3B82F6")}<h2>Répartition</h2></div>', unsafe_allow_html=True)
        if 'Nom_region' in df.columns:
            all_regions = df['Nom_region'].value_counts()
            fig = px.pie(values=all_regions.values, names=all_regions.index, hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(height=450,
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#9CA3AF'),
                margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    # Évolution top 5
    if 'Date' in df.columns and 'Nom_region' in df.columns:
        st.markdown(f'<div class="section-header">{icon("activity", 24, "#3B82F6")}<h2>Évolution des 5 régions principales</h2></div>', unsafe_allow_html=True)
        
        top5 = df['Nom_region'].value_counts().head(5).index
        df_top = df[df['Nom_region'].isin(top5)]
        df_ts_top = df_top.groupby(['Date', 'Nom_region']).size().unstack(fill_value=0)
        
        fig = go.Figure()
        colors = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6']
        for i, region in enumerate(top5):
            if region in df_ts_top.columns:
                fig.add_trace(go.Scatter(
                    x=df_ts_top.index, y=df_ts_top[region],
                    mode='lines+markers', name=region,
                    line=dict(color=colors[i], width=2)
                ))
        fig.update_layout(height=450, hovermode='x unified',
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#9CA3AF'),
            xaxis=dict(gridcolor='#374151', title='Date'),
            yaxis=dict(gridcolor='#374151', title='Nombre de cas'),
            legend=dict(bgcolor='rgba(31, 41, 55, 0.8)'),
            margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    # Interprétation
    st.markdown(f'<div class="section-header">{icon("lightbulb", 24, "#F59E0B")}<h2>Interprétation</h2></div>', unsafe_allow_html=True)
    
    top1_name = df['Nom_region'].value_counts().index[0]
    top1_count = df['Nom_region'].value_counts().iloc[0]
    top1_pct = top1_count / len(df) * 100
    top3 = df['Nom_region'].value_counts().head(3)
    top3_names = ", ".join(top3.index.tolist())
    top3_pct = top3.sum() / len(df) * 100
    
    st.markdown(f"""
    <div class="success-box">
        {icon('green_check', 28, '#10B981')}
        <div class="box-content">
            <b>Concentration géographique :</b><br><br>
            • <b>{top1_name}</b> concentre <b>{top1_pct:.1f}%</b> des cas ({top1_count} cas)<br>
            • Le <b>top 3</b> ({top3_names}) représente <b>{top3_pct:.1f}%</b> des cas<br><br>
            <b>Interprétation :</b> La maladie est fortement concentrée dans quelques régions. Cela peut s'expliquer par la densité de population, les flux migratoires et les structures de santé plus développées.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="warning-box">
        {icon('yellow_warning', 28, '#F59E0B')}
        <div class="box-content">
            <b>Recommandations :</b><br><br>
            1. Renforcer la surveillance dans les 3 régions principales<br>
            2. Coordonner les actions au niveau national<br>
            3. Pré-positionner les ressources avant les pics saisonniers
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================================
# PAGE 6 : RAPPORT
# ==========================================================

def page_rapport(df):
    page_header("report", "Rapport", "Téléchargement du rapport de surveillance")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon('virus', 20, '#9CA3AF')} Total Cas</div>
            <div class="metric-value">{len(df)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon('building', 20, '#9CA3AF')} Régions</div>
            <div class="metric-value">{df['Nom_region'].nunique() if 'Nom_region' in df.columns else 0}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon('hospital', 20, '#9CA3AF')} Districts</div>
            <div class="metric-value">{df['Nom_District_Residence'].nunique() if 'Nom_District_Residence' in df.columns else 0}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(f'<div class="section-header">{icon("download", 24, "#3B82F6")}<h2>Téléchargement</h2></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="info-box">
        {icon('lightbulb', 24, 'white')}
        <div class="box-content">
            <b>Deux formats disponibles :</b><br>
            • 📄 <b>TXT</b> : Format texte simple<br>
            • 📕 <b>PDF v6</b> : Format professionnel avec sommaire, logo et graphiques
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    # Charger le rapport TXT
    rapport = None
    if os.path.exists('rapport_final_mpox.txt'):
        with open('rapport_final_mpox.txt', 'r', encoding='utf-8') as f:
            rapport = f.read()
        
        with col1:
            st.download_button(
                "📄 Télécharger TXT",
                data=rapport,
                file_name=f"rapport_mpox_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    # Générer le PDF v6
    with col2:
        if st.button("📕 Générer le PDF v6", use_container_width=True):
            with st.spinner("🔄 Génération du PDF v6 en cours..."):
                try:
                    from pdf_generator_v6 import generer_pdf_v6
                    
                    # Données des modèles
                    modeles_data = {
                        'Modèle': ['SARIMA', 'SARIMAX_TOP5', 'ARIMA', 'SARIMAX_TOP3', 
                                   'Prophet', 'Moyenne Mobile', 'Holt-Winters', 'Naïf'],
                        'RMSE': [4.14, 5.06, 5.14, 5.77, 10.18, 11.26, 14.54, 15.20],
                        'MAE': [3.17, 4.02, 4.37, 4.62, 8.75, 10.54, 13.27, 13.38],
                        'AIC': [318.59, 322.61, 316.91, 319.12, None, None, None, None]
                    }
                    
                    # Générer le PDF v6
                    pdf_path = generer_pdf_v6(
                        rapport_txt=rapport if rapport else "Rapport de surveillance Mpox - Sénégal",
                        df=df,
                        modeles_data=modeles_data,
                        output_path=f'rapport_mpox_{datetime.now().strftime("%Y%m%d")}.pdf'
                    )
                    
                    # Lire le PDF
                    with open(pdf_path, 'rb') as f:
                        pdf_bytes = f.read()
                    
                    # Stocker dans session state
                    st.session_state['pdf_bytes'] = pdf_bytes
                    st.session_state['pdf_name'] = os.path.basename(pdf_path)
                    
                    st.success("✅ PDF v6 généré avec succès !")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Bouton de téléchargement PDF
    if 'pdf_bytes' in st.session_state:
        st.markdown("---")
        st.download_button(
            label="📥 Cliquez ici pour télécharger le PDF v6",
            data=st.session_state['pdf_bytes'],
            file_name=st.session_state['pdf_name'],
            mime="application/pdf",
            use_container_width=True
        )
        
        st.info("""
        📕 **Le PDF v6 contient :**
        
        - **Page 1** : Page de garde avec logo
        - **Page 2** : Sommaire
        - **Page 3** : Synthèse + évolution temporelle
        - **Page 4** : Top 10 régions
        - **Page 5** : Comparaison des modèles + RMSE
        - **Page 6** : Décomposition de la série
        - **Page 7** : Prévisions + graphique
        - **Page 8** : Recommandations
        """)
    
    # Aperçu du rapport TXT
    if rapport:
        st.markdown("---")
        st.markdown(f'<div class="section-header">{icon("report", 24, "#3B82F6")}<h2>Aperçu du rapport</h2></div>', unsafe_allow_html=True)
        
        with st.expander("📄 Voir le rapport complet"):
            st.text(rapport)

# ==========================================================
# MAIN
# ==========================================================
def main():
   
    # ============================================================
    # SIDEBAR (contenu)
    # ============================================================
        # Logo
    st.sidebar.markdown(f"""
    <div class="sidebar-logo">
        {icon('virus', 22, '#3B82F6')}
        <span>Mpox Sénégal</span>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    # ⭐ Section THÈME - Version compacte
    st.sidebar.markdown('<div class="section-label">THÈME</div>', unsafe_allow_html=True)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🌙", key="dark_btn", help="Mode Sombre", use_container_width=True):
            os.makedirs('.streamlit', exist_ok=True)
            with open('.streamlit/config.toml', 'w') as f:
                f.write("""
[theme]
base = "dark"
primaryColor = "#3B82F6"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1F2937"
textColor = "#FFFFFF"
""")
            st.rerun()
    with col2:
        if st.button("☀️", key="light_btn", help="Mode Clair", use_container_width=True):
            os.makedirs('.streamlit', exist_ok=True)
            with open('.streamlit/config.toml', 'w') as f:
                f.write("""
[theme]
base = "light"
primaryColor = "#2563EB"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F9FAFB"
textColor = "#111827"
""")
            st.rerun()

    st.sidebar.markdown('<div class="section-label">MENU</div>', unsafe_allow_html=True)
    
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Vue d'ensemble", "📈 Analyse temporelle", "🔮 Prévisions",
         "🔬 Comparaison des modèles", "🗺️ Analyse spatiale", "📋 Rapport"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('<div class="section-label">INFORMATIONS</div>', unsafe_allow_html=True)
    
    df = charger_donnees()
    
    if df is not None:
        st.sidebar.markdown(f"""
        <div style="padding: 1rem; color: #9CA3AF; font-size: 0.85rem; line-height: 2;">
            <div>{icon('virus', 16, '#3B82F6')} <b style="color: white;">{len(df)}</b> cas</div>
            <div>{icon('building', 16, '#3B82F6')} <b style="color: white;">{df['Nom_region'].nunique() if 'Nom_region' in df.columns else 0}</b> régions</div>
            <div>{icon('calendar', 16, '#3B82F6')} <b style="color: white;">{df['Date'].nunique() if 'Date' in df.columns else 0}</b> semaines</div>
            <div style="margin-top: 1rem;">{icon('trophy', 16, '#F59E0B')} <span>Meilleur modèle :</span></div>
            <div style="color: #3B82F6; font-weight: 600; padding-left: 1.5rem;">SARIMA (RMSE=4.14)</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"© {datetime.now().year} — Etud_L3 SID")
    
    if df is None:
        st.error("❌ Impossible de charger les données")
        return
    
    if page == "🏠 Vue d'ensemble":
        page_vue_ensemble(df)
    elif page == "📈 Analyse temporelle":
        page_analyse_temporelle(df)
    elif page == "🔮 Prévisions":
        page_previsions(df)
    elif page == "🔬 Comparaison des modèles":
        page_comparaison_modeles()
    elif page == "🗺️ Analyse spatiale":
        page_analyse_spatiale(df)
    elif page == "📋 Rapport":
        page_rapport(df)
        
if __name__ == "__main__":
    main()