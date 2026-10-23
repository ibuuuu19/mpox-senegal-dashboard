# -*- coding: utf-8 -*-
"""
==========================================================
 DASHBOARD MPOX · SÉNÉGAL  —  Refonte « Premium »
==========================================================
 Application de surveillance pensée pour des décideurs :
 - langage simple, explications sous chaque graphique ;
 - synthèse en un coup d'œil, puis un TABLEAU DE BORD qui
   regroupe toutes les analyses réalisées dans le projet ;
 - thème clair (par défaut) ou sombre.

 Fichiers attendus à côté de ce script :
   - le fichier Excel de la base (nom contenant « mpox »)
   - modeles.py            (entrainer_sarima, entrainer_sarima_lisse)
   - pdf_generator_v6.py   (generer_pdf_v6)   [facultatif]
   - rapport_final_mpox.txt                    [facultatif]
 Le module icons.py n'est plus nécessaire : les icônes sont
 intégrées à ce fichier.

 Bibliothèques : streamlit, pandas, numpy, plotly, openpyxl,
 statsmodels (pour la décomposition de la série).
==========================================================
"""
from __future__ import annotations

import glob
import inspect
import itertools
import os
import traceback
from datetime import date, datetime
from urllib.parse import quote

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Mpox Sénégal · Surveillance",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================================
# 1. PARAMÈTRES
# ==========================================================

# False : le modèle de prévision est entraîné sur les semaines AVEC cas
#         (comportement de l'ancienne version, résultats inchangés).
# True  : il est entraîné sur la série hebdomadaire complète (semaines sans
#         cas = 0), statistiquement plus rigoureuse pour SARIMA.
PREVISION_SUR_SERIE_COMPLETE = False

# Résultats de l'étape d'évaluation des modèles (issus du projet)
MODELES_DATA = {
    "Modèle": ["SARIMA", "SARIMAX_TOP5", "ARIMA", "SARIMAX_TOP3",
               "Prophet", "Moyenne Mobile", "Holt-Winters", "Naïf"],
    "RMSE": [4.14, 5.06, 5.14, 5.77, 10.18, 11.26, 14.54, 15.20],
    "MAE": [3.17, 4.02, 4.37, 4.62, 8.75, 10.54, 13.27, 13.38],
    "AIC": [318.59, 322.61, 316.91, 319.12, None, None, None, None],
}
MODELES_EVAL = pd.DataFrame(MODELES_DATA)
MEILLEUR = MODELES_EVAL.sort_values("RMSE").iloc[0]

PAGES = [
    ("Synthèse", "home"),
    ("Tableau de bord", "dashboard"),
    ("Analyse temporelle", "trend"),
    ("Prévisions", "target"),
    ("Comparaison des modèles", "award"),
    ("Analyse spatiale", "map"),
    ("Rapport", "file"),
    ("Guide & glossaire", "help"),
]

SYMPTOMES = [
    ("Fievre", "Fièvre"),
    ("Eruption_cutaneo_muqueuse", "Éruption cutanée / muqueuse"),
    ("Asthénie_physique", "Fatigue intense"),
    ("Cephalees_intenses", "Maux de tête intenses"),
    ("Douleurs_musculaires", "Douleurs musculaires"),
    ("Adenopathies_generalisees", "Ganglions gonflés (généralisés)"),
    ("Adenopathies_localisees", "Ganglions gonflés (localisés)"),
    ("Lesion_liquide_trouble", "Lésions à liquide trouble"),
]
LESIONS = [
    ("Local_Lesion_Visage", "Visage"),
    ("Local_Lesion_Corps", "Corps"),
    ("Local_Lesion_Paume_Mains", "Paumes des mains"),
    ("Local_Lesion_Plantes_Pieds", "Plantes des pieds"),
    ("Local_Lesion_Bouche", "Bouche"),
    ("Local_Lesion_Organes_Genitaux", "Organes génitaux"),
    ("Local_Lesion_Region_Anale", "Région anale"),
]
COLONNES_TECH = ["Semaine_Num", "Annee_Num", "Date", "Nb_Cas"]

# ==========================================================
# 2. ICÔNES (SVG intégrés, style trait)
# ==========================================================

_ICONES = {
    "home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    "dashboard": '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
    "trend": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "award": '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
    "map": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "file": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "help": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "building": '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
    "calendar": '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "check": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "bulb": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>',
    "thermo": '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>',
    "bar": '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
    "pie": '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
    "layers": '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "flask": '<path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><path d="M8.5 2h7"/><path d="M7 16h10"/>',
    "virus": '<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "up": '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    "down": '<path d="m7 7 10 10"/><path d="M17 7v10H7"/>',
    "flat": '<path d="M5 12h14"/>',
    "arrow": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
}


def icone(nom: str, taille: int = 20, couleur: str = "currentColor", trait: float = 2) -> str:
    corps = _ICONES.get(nom, _ICONES["info"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{taille}" height="{taille}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{couleur}" stroke-width="{trait}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="flex:none;vertical-align:-0.2em">{corps}</svg>'
    )


def _masque_css(nom: str) -> str:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
        "stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
        f"{_ICONES[nom]}</svg>"
    )
    return 'url("data:image/svg+xml;utf8,' + quote(svg) + '")'


# ==========================================================
# 3. THÈMES (clair / sombre)
# ==========================================================

CLAIR = dict(
    bg="#F5F3EE", surface="#FFFFFF", surface2="#FBFAF6", ink="#0E1A33", muted="#5D6579",
    line="#E4E0D5", grid="#ECE8DD", navy="#0E1A33", navy2="#1C2D52", gold="#B8913B",
    goldsoft="#F6EFD9", good="#1F8A5B", goodsoft="#E3F5EC", warn="#B96F0B",
    warnsoft="#FDF1DB", bad="#C0392B", badsoft="#FBE9E6", info="#2E5FD0",
    infosoft="#E6EDFC", shadow="0 10px 30px -14px rgba(14,26,51,.22)",
    side1="#0B1530", side2="#13224A", primary="#1C3F7A", pilon="#1C2D52",
)
SOMBRE = dict(
    bg="#0A111F", surface="#121B30", surface2="#16213A", ink="#E8EDF7", muted="#9AA8C4",
    line="#263250", grid="#1E2A45", navy="#0F1D3D", navy2="#1A2B52", gold="#D6B056",
    goldsoft="#2A2314", good="#38D39F", goodsoft="#0E2B22", warn="#F2B04A",
    warnsoft="#2E2410", bad="#F47C7C", badsoft="#33171B", info="#7AA2F7",
    infosoft="#15213F", shadow="0 10px 30px -14px rgba(0,0,0,.6)",
    side1="#070C18", side2="#0D1630", primary="#6F9BF5", pilon="#2A3F6E",
)
SERIES_CLAIR = ["#1C3F7A", "#B8913B", "#1F8A5B", "#C0392B", "#6B5BD2", "#2E9CCA"]
SERIES_SOMBRE = ["#6F9BF5", "#D6B056", "#38D39F", "#F47C7C", "#A596F5", "#5FC4E8"]

SOMBRE_ACTIF = bool(st.session_state.get("mode_sombre", False))
P = SOMBRE if SOMBRE_ACTIF else CLAIR
COULEURS = SERIES_SOMBRE if SOMBRE_ACTIF else SERIES_CLAIR


def rgba(hexa: str, alpha: float) -> str:
    h = hexa.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, [class*="css"] { font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; }
.stApp { background: @@bg@@; color: @@ink@@; }
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; height: 0; }
.block-container { padding: 1.4rem 2.2rem 4rem; max-width: 1320px; }
.stApp p, .stApp li, .stApp label, .stApp span, .stApp summary { color: @@ink@@; }
.stApp a { color: @@gold@@; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { font-family: 'Fraunces', Georgia, serif; color: @@ink@@; letter-spacing: -.01em; }
[data-testid="stMarkdownContainer"] p { margin-bottom: .4rem; }
hr { border-color: @@line@@; }

/* ---------- En-tête de page ---------- */
.hero { background: radial-gradient(900px 380px at 88% -25%, #2F4A86 0%, transparent 62%), linear-gradient(160deg, @@navy@@, @@navy2@@);
  border-radius: 22px; padding: 2.1rem 2.4rem 2.2rem; margin-bottom: 1.5rem; box-shadow: @@shadow@@; }
.hero .eb { display: inline-flex; align-items: center; gap: .5rem; border: 1px solid rgba(214,176,86,.55); border-radius: 99px;
  padding: .28rem .85rem; font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; color: #E8CF8F !important; }
.hero .eb * { color: #E8CF8F !important; }
.hero .ti { font-family: 'Fraunces', Georgia, serif; font-size: clamp(1.7rem, 3.2vw, 2.55rem); line-height: 1.15; margin: .85rem 0 .5rem; color: #FFFFFF !important; font-weight: 600; }
.hero .su { color: #C9D3EA !important; font-size: 1.05rem; max-width: 780px; line-height: 1.6; }
.hero .chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.1rem; }
.hero .chip { border: 1px solid rgba(255,255,255,.2); background: rgba(255,255,255,.07); border-radius: 99px; padding: .22rem .8rem; font-size: .8rem; color: #E7ECF8 !important; }

/* ---------- Titres de section ---------- */
.sec { margin: 1.9rem 0 .9rem; }
.sec .e { color: @@gold@@ !important; font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 700; }
.sec .t { font-family: 'Fraunces', Georgia, serif; font-size: 1.55rem; color: @@ink@@ !important; margin: .15rem 0 .15rem; font-weight: 600; }
.sec .d { color: @@muted@@ !important; font-size: .95rem; max-width: 820px; line-height: 1.55; }
.ct { font-weight: 700; font-size: 1rem; color: @@ink@@ !important; margin: .6rem 0 .45rem; display: flex; align-items: center; gap: .5rem; }
.ct svg { color: @@gold@@; }
.cap { color: @@muted@@ !important; font-size: .86rem; margin: .45rem .2rem 1.1rem; line-height: 1.5; }
.cap b { color: @@ink@@ !important; }

/* ---------- Cartes d'indicateurs ---------- */
.kpi { background: @@surface@@; border: 1px solid @@line@@; border-radius: 18px; padding: 1.05rem 1.2rem; box-shadow: @@shadow@@; min-height: 132px; }
.kpi.accent { border-top: 3px solid @@gold@@; }
.kpi .l { display: flex; align-items: center; gap: .45rem; color: @@muted@@ !important; font-size: .74rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; }
.kpi .l * { color: @@gold@@ !important; }
.kpi .v { font-family: 'Fraunces', Georgia, serif; font-size: 2.15rem; line-height: 1.1; color: @@ink@@ !important; margin: .4rem 0 .15rem; font-weight: 600; }
.kpi .s { color: @@muted@@ !important; font-size: .82rem; line-height: 1.4; }

/* ---------- Bandeau de situation ---------- */
.status { display: flex; gap: 1.3rem; align-items: center; background: @@surface@@; border: 1px solid @@line@@; border-left-width: 6px; border-radius: 20px; padding: 1.3rem 1.6rem; box-shadow: @@shadow@@; margin: .2rem 0 1.2rem; }
.status .dot { width: 58px; height: 58px; border-radius: 50%; display: grid; place-items: center; flex: none; }
.status .lab { font-size: .72rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 700; color: @@muted@@ !important; }
.status .tt { font-family: 'Fraunces', Georgia, serif; font-size: 1.5rem; color: @@ink@@ !important; margin: .1rem 0 .2rem; font-weight: 600; }
.status .ds { color: @@muted@@ !important; line-height: 1.55; }
.status .ds b { color: @@ink@@ !important; }
.status.bad { border-left-color: @@bad@@; } .status.bad .dot { background: @@bad@@; }
.status.warn { border-left-color: @@warn@@; } .status.warn .dot { background: @@warn@@; }
.status.info { border-left-color: @@info@@; } .status.info .dot { background: @@info@@; }
.status.ok { border-left-color: @@good@@; } .status.ok .dot { background: @@good@@; }

/* ---------- Encadrés ---------- */
.callout { display: flex; gap: .9rem; border-radius: 16px; padding: 1.05rem 1.25rem; margin: .9rem 0; border: 1px solid transparent; border-left-width: 5px; }
.callout .tt { font-weight: 700; margin-bottom: .2rem; color: @@ink@@ !important; }
.callout .bd { line-height: 1.6; color: @@ink@@ !important; font-size: .95rem; }
.callout .bd * { color: @@ink@@ !important; }
.callout ul { margin: .3rem 0 0 1.1rem; padding: 0; }
.callout.info { background: @@infosoft@@; border-color: @@info@@; }
.callout.ok { background: @@goodsoft@@; border-color: @@good@@; }
.callout.warn { background: @@warnsoft@@; border-color: @@warn@@; }
.callout.bad { background: @@badsoft@@; border-color: @@bad@@; }
.callout.tip { background: @@goldsoft@@; border-color: @@gold@@; }

/* ---------- Cartes de lecture ---------- */
.card { background: @@surface@@; border: 1px solid @@line@@; border-radius: 18px; padding: 1.2rem 1.4rem; box-shadow: @@shadow@@; }
.card .h { font-family: 'Fraunces', Georgia, serif; font-size: 1.15rem; color: @@ink@@ !important; margin-bottom: .5rem; font-weight: 600; }
.card ul { margin: 0; padding-left: 1.15rem; }
.card li { margin: .45rem 0; line-height: 1.55; color: @@ink@@ !important; font-size: .95rem; }
.card p { color: @@muted@@ !important; font-size: .92rem; line-height: 1.55; }
.card.nav { min-height: 150px; }
.card.nav .ic { color: @@gold@@; margin-bottom: .4rem; }

/* ---------- Tableaux ---------- */
.tbl-wrap { overflow-x: auto; border: 1px solid @@line@@; border-radius: 16px; background: @@surface@@; box-shadow: @@shadow@@; margin: .4rem 0 1rem; }
table.tbl { width: 100%; border-collapse: collapse; font-size: .92rem; }
table.tbl th { background: @@navy2@@; color: #FFFFFF !important; text-align: left; padding: .75rem .95rem; font-weight: 600; white-space: nowrap; }
table.tbl td { padding: .65rem .95rem; border-top: 1px solid @@line@@; color: @@ink@@ !important; }
table.tbl tr:nth-child(even) td { background: @@surface2@@; }
table.tbl td.num, table.tbl th.num { text-align: right; font-variant-numeric: tabular-nums; }
.pill { display: inline-block; padding: .12rem .65rem; border-radius: 99px; font-size: .78rem; font-weight: 700; }
.pill.ok { background: @@goodsoft@@; color: @@good@@ !important; }
.pill.warn { background: @@warnsoft@@; color: @@warn@@ !important; }
.pill.bad { background: @@badsoft@@; color: @@bad@@ !important; }
.pill.info { background: @@infosoft@@; color: @@info@@ !important; }
.pill.gold { background: @@goldsoft@@; color: @@gold@@ !important; }

/* ---------- Glossaire ---------- */
.gl { background: @@surface@@; border: 1px solid @@line@@; border-radius: 14px; padding: .95rem 1.15rem; margin-bottom: .7rem; }
.gl .k { font-weight: 700; color: @@ink@@ !important; }
.gl .v { color: @@muted@@ !important; font-size: .92rem; line-height: 1.55; margin-top: .15rem; }

/* ---------- Graphiques ---------- */
[data-testid="stPlotlyChart"] { background: @@surface@@; border: 1px solid @@line@@; border-radius: 18px; padding: .6rem .5rem .2rem; box-shadow: @@shadow@@; }

/* ---------- Champs et boutons ---------- */
[data-testid="stWidgetLabel"] p, .stApp label p { color: @@ink@@ !important; font-weight: 600; font-size: .88rem; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div { background: @@surface@@ !important; border: 1px solid @@line@@ !important; border-radius: 12px !important; color: @@ink@@ !important; }
div[data-baseweb="select"] * { color: @@ink@@ !important; }
div[data-baseweb="select"] svg { fill: @@muted@@ !important; }
span[data-baseweb="tag"] { background: @@navy2@@ !important; border-radius: 8px !important; }
span[data-baseweb="tag"] * { color: #FFFFFF !important; }
div[data-baseweb="popover"] ul, div[data-baseweb="popover"] [role="listbox"] { background: @@surface@@ !important; }
div[data-baseweb="popover"] li, div[data-baseweb="popover"] [role="option"] { background: @@surface@@ !important; color: @@ink@@ !important; }
div[data-baseweb="popover"] li:hover, div[data-baseweb="popover"] [role="option"]:hover { background: @@goldsoft@@ !important; }
div[data-baseweb="popover"] li *, div[data-baseweb="popover"] [role="option"] * { color: @@ink@@ !important; }
[data-testid="stSlider"] [data-testid="stThumbValue"], [data-testid="stSlider"] [data-testid="stSliderThumbValue"] { color: @@ink@@ !important; font-weight: 600; }
[data-testid="stSlider"] [data-testid="stTickBarMin"], [data-testid="stSlider"] [data-testid="stTickBarMax"] { color: @@muted@@ !important; }
.stButton > button, .stDownloadButton > button { width: 100%; background: linear-gradient(135deg, @@navy2@@, @@navy@@); color: #FFFFFF !important; border: 1px solid rgba(255,255,255,.1);
  border-radius: 12px; padding: .65rem 1.1rem; font-weight: 600; box-shadow: @@shadow@@; transition: all .15s; }
.stButton > button p, .stDownloadButton > button p { color: #FFFFFF !important; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: @@gold@@; transform: translateY(-1px); color: #FFFFFF !important; }
[data-testid="stExpander"] { background: @@surface@@; border: 1px solid @@line@@ !important; border-radius: 16px; box-shadow: @@shadow@@; }
[data-testid="stExpander"] summary { font-weight: 600; background: @@surface@@ !important; border-radius: 16px; }
[data-testid="stExpander"] summary p, [data-testid="stExpander"] summary span { color: @@ink@@ !important; }
[data-testid="stExpander"] details { background: @@surface@@ !important; border-radius: 16px; }
[data-testid="stExpander"] details { border: none; }

/* ---------- Sélecteurs en « pastilles » (zone principale) ---------- */
.stApp [role="radiogroup"] { gap: .45rem; flex-wrap: wrap; }
.stApp [data-testid="stRadioOption"] { background: @@surface@@; border: 1px solid @@line@@; border-radius: 99px; padding: .42rem 1.05rem; margin: 0; cursor: pointer; transition: all .15s; display: flex; align-items: center; }
.stApp [data-testid="stRadioOption"]:hover { border-color: @@gold@@; }
.stApp [data-testid="stRadioOption"] > div > div:first-child { display: none !important; }
.stApp [data-testid="stRadioOption"] p { font-weight: 600; font-size: .9rem; margin: 0; color: @@ink@@ !important; }
.stApp [data-testid="stRadioOption"][data-selected="true"] { background: @@pilon@@; border-color: @@gold@@; }
.stApp [data-testid="stRadioOption"][data-selected="true"] p { color: #FFFFFF !important; }

/* ---------- Barre latérale ---------- */
.stApp [data-testid="stSidebar"] { background: linear-gradient(180deg, @@side1@@ 0%, @@side2@@ 100%); border-right: 1px solid rgba(255,255,255,.06); }
.stApp [data-testid="stSidebar"] * { color: #C9D3EA; }
.stApp [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p, .stApp [data-testid="stSidebar"] label p { color: #C9D3EA !important; }
.brand { display: flex; align-items: center; gap: .75rem; padding: .3rem .2rem 1.1rem; }
.brand .lg { width: 42px; height: 42px; border-radius: 13px; background: linear-gradient(135deg, #B8913B, #E8CF8F); display: grid; place-items: center; flex: none; }
.brand .lg svg { color: #0E1A33; stroke: #0E1A33; }
.brand .n { font-family: 'Fraunces', Georgia, serif; font-size: 1.2rem; color: #FFFFFF !important; line-height: 1.1; font-weight: 600; }
.brand .s { font-size: .68rem; letter-spacing: .14em; text-transform: uppercase; color: #8EA0C8 !important; margin-top: .15rem; }
.slab { font-size: .68rem; letter-spacing: .16em; text-transform: uppercase; color: #8EA0C8 !important; font-weight: 700; margin: 1.1rem 0 .45rem .2rem; }
.stApp [data-testid="stSidebar"] [role="radiogroup"] { gap: .15rem; flex-direction: column; flex-wrap: nowrap; }
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"] { width: 100%; background: transparent; border: 1px solid transparent; border-radius: 12px; padding: .62rem .85rem; }
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"]:hover { background: rgba(255,255,255,.07); border-color: transparent; }
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"] p { color: #C9D3EA !important; font-weight: 500; }
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] { background: linear-gradient(135deg, #B8913B, #D9BC6B); border-color: transparent; }
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p { color: #0E1A33 !important; font-weight: 700; }
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"]::before { content: ""; display: inline-block; width: 18px; height: 18px; margin-right: .75rem; flex: none; background-color: #C9D3EA; }
.stApp [data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"]::before { background-color: #0E1A33; }
.sbcard { background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.08); border-radius: 14px; padding: .85rem 1rem; font-size: .84rem; }
.sbcard .r { display: flex; justify-content: space-between; gap: .6rem; padding: .28rem 0; border-bottom: 1px solid rgba(255,255,255,.06); }
.sbcard .r:last-child { border-bottom: none; }
.sbcard .r span:first-child { color: #8EA0C8 !important; }
.sbcard .r span:last-child { color: #FFFFFF !important; font-weight: 600; text-align: right; }
.sbfoot { color: #7F91BA !important; font-size: .76rem; margin-top: 1.2rem; line-height: 1.5; }

@media (max-width: 768px) {
  .block-container { padding: 1rem 1rem 3rem; }
  .hero { padding: 1.4rem 1.3rem; }
  .kpi .v { font-size: 1.7rem; }
  .status { flex-direction: column; align-items: flex-start; }
}
"""


def injecter_css() -> None:
    css = CSS
    for cle, val in P.items():
        css = css.replace(f"@@{cle}@@", val)
    nav = []
    for i, (_, ic) in enumerate(PAGES, start=1):
        m = _masque_css(ic)
        nav.append(
            f'.stApp [data-testid="stSidebar"] [role="radiogroup"] > div:nth-of-type({i}) [data-testid="stRadioOption"]::before '
            f"{{ -webkit-mask: {m} center / contain no-repeat; mask: {m} center / contain no-repeat; }}"
        )
    st.markdown(f"<style>{css}\n{chr(10).join(nav)}</style>", unsafe_allow_html=True)


# ==========================================================
# 4. COMPOSANTS D'INTERFACE
# ==========================================================

_COMPTEUR = itertools.count()


def ecrire(html: str) -> None:
    """Affiche du HTML en retirant l'indentation (évite le rendu « code » de Markdown)."""
    propre = "\n".join(ligne.strip() for ligne in html.strip().splitlines() if ligne.strip())
    st.markdown(propre, unsafe_allow_html=True)


def fmt(n, d: int = 0) -> str:
    if n is None or (isinstance(n, float) and np.isnan(n)):
        return "—"
    return f"{n:,.{d}f}".replace(",", " ").replace(".", ",")


def fdate(d, court: bool = False) -> str:
    if d is None or pd.isna(d):
        return "—"
    return pd.Timestamp(d).strftime("%d/%m/%y" if court else "%d/%m/%Y")


def entete(ic: str, surtitre: str, titre: str, sous_titre: str, pastilles=None) -> None:
    chips = "".join(f'<span class="chip">{p}</span>' for p in (pastilles or []))
    bloc = f'<div class="chips">{chips}</div>' if chips else ""
    ecrire(
        f'<div class="hero"><div class="eb">{icone(ic, 15, "#E8CF8F")} {surtitre}</div>'
        f'<div class="ti">{titre}</div><div class="su">{sous_titre}</div>{bloc}</div>'
    )


def section(titre: str, description: str = "", surtitre: str = "") -> None:
    e = f'<div class="e">{surtitre}</div>' if surtitre else ""
    d = f'<div class="d">{description}</div>' if description else ""
    ecrire(f'<div class="sec">{e}<div class="t">{titre}</div>{d}</div>')


def kpi(libelle: str, valeur: str, sous: str = "", ic: str = "activity", accent: bool = False) -> str:
    cls = "kpi accent" if accent else "kpi"
    ic = ic if ic in _ICONES else "bar"
    return (
        f'<div class="{cls}"><div class="l">{icone(ic, 16)} {libelle}</div>'
        f'<div class="v">{valeur}</div><div class="s">{sous}</div></div>'
    )


def rangee_kpi(items: list[dict]) -> None:
    colonnes = st.columns(len(items))
    for col, it in zip(colonnes, items):
        with col:
            ecrire(kpi(**it))


def callout(genre: str, titre: str, corps: str) -> None:
    ic = {"info": "info", "ok": "check", "warn": "alert", "bad": "alert", "tip": "bulb"}[genre]
    col = {"info": P["info"], "ok": P["good"], "warn": P["warn"], "bad": P["bad"], "tip": P["gold"]}[genre]
    ecrire(
        f'<div class="callout {genre}"><div style="color:{col};margin-top:.1rem">{icone(ic, 22, col)}</div>'
        f'<div><div class="tt">{titre}</div><div class="bd">{corps}</div></div></div>'
    )


def carte_lecture(titre: str, points: list[str]) -> None:
    lis = "".join(f"<li>{p}</li>" for p in points)
    ecrire(f'<div class="card"><div class="h">{titre}</div><ul>{lis}</ul></div>')


def titre_graphique(texte: str, ic: str = "bar") -> None:
    ecrire(f'<div class="ct">{icone(ic, 18)} {texte}</div>')


def legende(texte: str) -> None:
    ecrire(f'<div class="cap"><b>Comment lire :</b> {texte}</div>')


def pastille(texte: str, genre: str = "info") -> str:
    return f'<span class="pill {genre}">{texte}</span>'


def table_html(entetes: list[str], lignes: list[list], num_cols=()) -> None:
    th = "".join(f'<th class="{"num" if i in num_cols else ""}">{h}</th>' for i, h in enumerate(entetes))
    tr = ""
    for ligne in lignes:
        tds = "".join(f'<td class="{"num" if i in num_cols else ""}">{c}</td>' for i, c in enumerate(ligne))
        tr += f"<tr>{tds}</tr>"
    ecrire(f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')


_PLOTLY_ACCEPTE_WIDTH = "width" in inspect.signature(st.plotly_chart).parameters


def afficher(fig) -> None:
    if fig is None:
        return
    cfg = {"displayModeBar": False, "responsive": True}
    cle = f"fig_{next(_COMPTEUR)}"
    if _PLOTLY_ACCEPTE_WIDTH:
        st.plotly_chart(fig, width="stretch", config=cfg, key=cle)
    else:
        st.plotly_chart(fig, use_container_width=True, config=cfg, key=cle)


def aller_a(page: str) -> None:
    st.session_state["nav"] = page


# ==========================================================
# 5. DONNÉES
# ==========================================================

def _lundi_iso(annee, semaine):
    """Lundi de la semaine ISO (convention des semaines épidémiologiques DHIS2)."""
    try:
        return pd.Timestamp(date.fromisocalendar(int(annee), int(semaine), 1))
    except (ValueError, TypeError, OverflowError):
        return pd.NaT


@st.cache_data(show_spinner="Chargement des données…")
def charger_donnees():
    candidats = glob.glob("*.xlsx") + glob.glob("*.xls") + glob.glob("data/*.xlsx") + glob.glob("data/*.xls")
    candidats = [f for f in candidats if "mpox" in os.path.basename(f).lower()
                 and not os.path.basename(f).startswith("~$")]
    if not candidats:
        return None, ("Aucun fichier Excel dont le nom contient « mpox » n'a été trouvé "
                      "à côté de l'application (ni dans un dossier data/).")
    try:
        df = pd.read_excel(sorted(candidats)[0])
    except Exception as e:  # noqa: BLE001
        return None, f"Le fichier de données n'a pas pu être lu : {e}"
    df.columns = df.columns.astype(str).str.strip()

    if "Semaine_Epi" in df.columns:
        nombres = df["Semaine_Epi"].astype(str).str.findall(r"\d+")
        sem = nombres.apply(lambda l: next((int(x) for x in l if len(x) <= 2), np.nan))
        ann = nombres.apply(lambda l: next((int(x) for x in l if len(x) == 4), np.nan))
        df["Semaine_Num"] = pd.to_numeric(sem, errors="coerce")
        df["Annee_Num"] = pd.to_numeric(ann, errors="coerce")
        df["Date"] = pd.to_datetime([_lundi_iso(a, s) for a, s in zip(df["Annee_Num"], df["Semaine_Num"])])
    if "Date" in df.columns:
        hebdo = df.groupby("Date").size().reset_index(name="Nb_Cas")
        df = df.merge(hebdo, on="Date", how="left")
    return df, None


def series_hebdo(df: pd.DataFrame):
    """Série observée (semaines avec au moins un cas) et série complète (semaines sans cas = 0)."""
    if "Date" not in df.columns:
        return pd.Series(dtype=int), pd.Series(dtype=int)
    d = df.dropna(subset=["Date"])
    if d.empty:
        return pd.Series(dtype=int), pd.Series(dtype=int)
    obs = d.groupby("Date").size().sort_index().astype(int)
    return obs, completer(obs)


def completer(obs: pd.Series, debut=None, fin=None) -> pd.Series:
    if obs.empty and debut is None:
        return obs
    debut = debut if debut is not None else obs.index.min()
    fin = fin if fin is not None else obs.index.max()
    idx = pd.date_range(debut, fin, freq="7D")
    return obs.reindex(idx, fill_value=0).astype(int)


def sexe_normalise(df: pd.DataFrame):
    if "Sexe" not in df.columns:
        return None
    s = df["Sexe"].astype(str).str.strip().str.lower()
    out = pd.Series(np.nan, index=df.index, dtype=object)
    out[s.str.startswith("m")] = "Masculin"
    out[s.str.startswith("f")] = "Féminin"
    return out


def statut_pcr(df: pd.DataFrame):
    if "Resultat_PCR_Mpox" not in df.columns:
        return None
    s = df["Resultat_PCR_Mpox"].astype(str).str.strip().str.lower()
    out = pd.Series("En attente / non renseigné", index=df.index, dtype=object)
    out[s.str.contains("posit", regex=False)] = "Positif"
    out[s.str.contains(r"n[ée]g", regex=True)] = "Négatif"
    return out


def tranches_age(ages: pd.Series) -> pd.Series:
    bornes = [0, 5, 15, 25, 35, 50, 200]
    noms = ["0–4 ans", "5–14 ans", "15–24 ans", "25–34 ans", "35–49 ans", "50 ans et +"]
    return pd.cut(ages, bins=bornes, labels=noms, right=False)


def tendance_recente(cpl: pd.Series):
    """Compare la moyenne des 4 dernières semaines à celle des 4 précédentes."""
    if len(cpl) < 8:
        return None
    dern, prec = float(cpl.iloc[-4:].mean()), float(cpl.iloc[-8:-4].mean())
    variation = (dern - prec) / max(prec, 1.0) * 100
    if variation >= 50:
        sens = "hausse_forte"
    elif variation >= 20:
        sens = "hausse"
    elif variation <= -20:
        sens = "baisse"
    else:
        sens = "stable"
    return dict(dern=dern, prec=prec, variation=variation, sens=sens)


def resume_serie(obs: pd.Series, cpl: pd.Series) -> dict:
    return dict(
        total=int(obs.sum()), n_obs=len(obs), n_tot=len(cpl),
        moyenne=float(obs.mean()), moyenne_cpl=float(cpl.mean()),
        mediane=float(obs.median()), ecart=float(obs.std()) if len(obs) > 1 else float("nan"),
        maxi=int(obs.max()), date_max=obs.idxmax(),
    )


def taux_oui(df: pd.DataFrame, definitions) -> pd.DataFrame:
    lignes = []
    for col, lib in definitions:
        if col not in df.columns:
            continue
        s = df[col].astype(str).str.strip().str.lower()
        oui = int(s.isin(["oui", "o", "yes", "1", "1.0", "true"]).sum())
        non = int(s.isin(["non", "n", "no", "0", "0.0", "false"]).sum())
        if oui + non > 0:
            lignes.append((lib, oui / (oui + non) * 100, oui, oui + non))
    return pd.DataFrame(lignes, columns=["lib", "pct", "oui", "n"]).sort_values("pct")


# ==========================================================
# 6. GRAPHIQUES
# ==========================================================

def _base(fig, hauteur: int = 420, legende_visible: bool = True, haut: int = 28):
    fig.update_layout(
        height=hauteur, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color=P["muted"], size=13),
        margin=dict(l=12, r=18, t=haut, b=12), colorway=COULEURS, showlegend=legende_visible,
        hoverlabel=dict(bgcolor=P["navy"], bordercolor=P["navy"],
                        font=dict(color="#FFFFFF", family="Inter, sans-serif", size=13)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", font=dict(color=P["ink"])),
    )
    axe = dict(gridcolor=P["grid"], zeroline=False, linecolor=P["line"],
               tickfont=dict(color=P["muted"]), title_font=dict(color=P["muted"]))
    fig.update_xaxes(**axe)
    fig.update_yaxes(**axe)
    return fig


def _ligne_verticale(fig, x, texte: str, couleur: str) -> None:
    fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1, xref="x", yref="paper",
                  line=dict(color=couleur, width=2, dash="dot"))
    fig.add_annotation(x=x, y=1.0, xref="x", yref="paper", text=texte, showarrow=False,
                       yanchor="bottom", font=dict(color=couleur, size=12))


def fig_evolution(s: pd.Series):
    if s.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s.index, y=s.values, name="Cas par semaine", mode="lines+markers",
        line=dict(color=P["primary"], width=2.6), marker=dict(size=6, color=P["primary"]),
        fill="tozeroy", fillcolor=rgba(P["primary"], .10),
        hovertemplate="Semaine du %{x|%d/%m/%Y}<br><b>%{y}</b> cas<extra></extra>"))
    if len(s) >= 5:
        ma = s.rolling(4, min_periods=4).mean()
        fig.add_trace(go.Scatter(
            x=ma.index, y=ma.values, name="Tendance lissée (moyenne sur 4 semaines)", mode="lines",
            line=dict(color=P["gold"], width=3, dash="dash"),
            hovertemplate="Moyenne 4 sem. : <b>%{y:.1f}</b> cas<extra></extra>"))
    pic = int(s.max())
    fig.add_annotation(x=s.idxmax(), y=pic, text=f"Pic : {pic} cas", showarrow=True, arrowhead=2,
                       arrowcolor=P["gold"], ax=0, ay=-40, bgcolor=P["navy"], bordercolor=P["gold"],
                       borderpad=4, font=dict(color="#FFFFFF", size=12))
    _base(fig, 430)
    fig.update_yaxes(title_text="Nombre de cas", rangemode="tozero")
    return fig


def fig_distribution(s: pd.Series):
    if s.empty:
        return None
    vc = s.value_counts().sort_index()
    x = [int(v) for v in vc.index]
    y = [int(v) for v in vc.values]
    couleurs = [P["muted"] if v == 0 else P["primary"] for v in x]
    fig = go.Figure(go.Bar(
        x=x, y=y, marker_color=couleurs, text=y, textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b> semaine(s) avec <b>%{x}</b> cas<extra></extra>"))
    med = float(s.median())
    _ligne_verticale(fig, med, f"Semaine typique (médiane) : {med:.0f} cas", P["gold"])
    _base(fig, 380, legende_visible=False, haut=44)
    fig.update_xaxes(title_text="Nombre de cas dans la semaine", dtick=2)
    fig.update_yaxes(title_text="Nombre de semaines", rangemode="tozero")
    return fig


def fig_regions(vc: pd.Series, top: int | None = None):
    if vc.empty:
        return None
    total = int(vc.sum())
    v = (vc.head(top) if top else vc).iloc[::-1]
    couleurs = [P["gold"] if i == len(v) - 1 else P["primary"] for i in range(len(v))]
    fig = go.Figure(go.Bar(
        y=v.index.tolist(), x=[int(n) for n in v.values], orientation="h", marker_color=couleurs,
        text=[f"{int(n)}  ·  {n / total * 100:.0f} %" for n in v.values], textposition="outside",
        cliponaxis=False, hovertemplate="<b>%{y}</b><br>%{x} cas<extra></extra>"))
    _base(fig, max(320, 34 * len(v) + 70), legende_visible=False)
    fig.update_xaxes(title_text="Nombre de cas", range=[0, float(v.max()) * 1.3])
    fig.update_yaxes(automargin=True)
    return fig


def fig_treemap(vc: pd.Series):
    if vc.empty:
        return None
    fig = go.Figure(go.Treemap(
        labels=vc.index.tolist(), parents=[""] * len(vc), values=[int(v) for v in vc.values],
        marker=dict(colors=[int(v) for v in vc.values], colorscale=[[0, "#4F6FA8"], [1, "#13224A"]],
                    line=dict(width=3, color=P["surface"])),
        texttemplate="<b>%{label}</b><br>%{value} cas<br>%{percentRoot:.0%}",
        textfont=dict(color="#FFFFFF", size=13), pathbar=dict(visible=False),
        hovertemplate="<b>%{label}</b><br>%{value} cas (%{percentRoot:.1%})<extra></extra>"))
    _base(fig, 420, legende_visible=False, haut=10)
    return fig


def fig_evolution_regions(d: pd.DataFrame, top: int = 5):
    if "Date" not in d.columns or "Nom_region" not in d.columns:
        return None
    dd = d.dropna(subset=["Date", "Nom_region"])
    if dd.empty:
        return None
    tab = dd.groupby(["Date", "Nom_region"]).size().unstack(fill_value=0)
    tab = tab.reindex(pd.date_range(tab.index.min(), tab.index.max(), freq="7D"), fill_value=0)
    ordre = tab.sum().sort_values(ascending=False).head(top).index
    fig = go.Figure()
    for i, reg in enumerate(ordre):
        fig.add_trace(go.Scatter(
            x=tab.index, y=tab[reg].values, name=str(reg), mode="lines",
            line=dict(color=COULEURS[i % len(COULEURS)], width=2.4),
            hovertemplate=f"<b>{reg}</b><br>%{{x|%d/%m/%Y}} : %{{y}} cas<extra></extra>"))
    _base(fig, 420)
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(title_text="Nombre de cas", rangemode="tozero")
    return fig


def fig_age(ages: pd.Series):
    ages = ages.dropna()
    if ages.empty:
        return None
    haut = int(np.ceil((ages.max() + 1) / 5) * 5)
    bornes = list(range(0, haut + 5, 5))
    comptes, _ = np.histogram(ages, bins=bornes)
    etiq = [f"{a}–{b - 1}" for a, b in zip(bornes[:-1], bornes[1:])]
    fig = go.Figure(go.Bar(x=etiq, y=[int(c) for c in comptes], marker_color=P["primary"],
                           hovertemplate="%{x} ans : <b>%{y}</b> cas<extra></extra>"))
    fig.add_annotation(xref="paper", yref="paper", x=1, y=1.02, xanchor="right", yanchor="bottom",
                       text=f"Âge médian : <b>{ages.median():.0f} ans</b>", showarrow=False,
                       font=dict(color=P["gold"], size=13))
    _base(fig, 380, legende_visible=False, haut=40)
    fig.update_xaxes(title_text="Âge (tranches de 5 ans)")
    fig.update_yaxes(title_text="Nombre de cas", rangemode="tozero")
    return fig


def fig_sexe(sexe: pd.Series):
    vc = sexe.dropna().value_counts()
    if vc.empty:
        return None
    coul = {"Masculin": P["primary"], "Féminin": P["gold"]}
    fig = go.Figure(go.Pie(
        labels=vc.index.tolist(), values=[int(v) for v in vc.values], hole=0.64, sort=False,
        marker=dict(colors=[coul.get(l, P["muted"]) for l in vc.index], line=dict(color=P["surface"], width=3)),
        textinfo="label+percent", textposition="outside", textfont=dict(color=P["ink"], size=13),
        hovertemplate="%{label} : <b>%{value}</b> cas (%{percent})<extra></extra>"))
    fig.add_annotation(text=f"<b>{int(vc.sum())}</b><br>cas", x=0.5, y=0.5, showarrow=False,
                       font=dict(size=18, color=P["ink"]))
    _base(fig, 380, legende_visible=False, haut=20)
    return fig


def fig_age_sexe(ages: pd.Series, sexe: pd.Series):
    t = pd.DataFrame({"tr": tranches_age(ages), "sexe": sexe}).dropna()
    if t.empty:
        return None
    tab = t.groupby(["tr", "sexe"], observed=False).size().unstack(fill_value=0)
    fig = go.Figure()
    coul = {"Masculin": P["primary"], "Féminin": P["gold"]}
    for s in tab.columns:
        fig.add_trace(go.Bar(x=tab.index.astype(str).tolist(), y=[int(v) for v in tab[s].values], name=str(s),
                             marker_color=coul.get(s, P["muted"]),
                             hovertemplate=f"{s} · %{{x}} : <b>%{{y}}</b> cas<extra></extra>"))
    _base(fig, 380)
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Nombre de cas", rangemode="tozero")
    return fig


def fig_taux(tab: pd.DataFrame):
    if tab.empty:
        return None
    fig = go.Figure(go.Bar(
        y=tab["lib"].tolist(), x=tab["pct"].tolist(), orientation="h", marker_color=P["primary"],
        text=[f"{p:.0f} %  ({o}/{n})" for p, o, n in zip(tab["pct"], tab["oui"], tab["n"])],
        textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:.1f} % des cas renseignés<extra></extra>"))
    _base(fig, max(300, 38 * len(tab) + 70), legende_visible=False)
    fig.update_xaxes(title_text="Part des cas concernés (%)", range=[0, 118])
    fig.update_yaxes(automargin=True)
    return fig


def fig_pcr(statut: pd.Series):
    vc = statut.value_counts()
    if vc.empty:
        return None
    coul = {"Positif": P["bad"], "Négatif": P["primary"], "En attente / non renseigné": P["warn"]}
    fig = go.Figure(go.Pie(
        labels=vc.index.tolist(), values=[int(v) for v in vc.values], hole=0.64, sort=False,
        marker=dict(colors=[coul.get(l, P["muted"]) for l in vc.index], line=dict(color=P["surface"], width=3)),
        textinfo="percent", textposition="outside", textfont=dict(color=P["ink"], size=13),
        hovertemplate="%{label} : <b>%{value}</b> cas (%{percent})<extra></extra>"))
    fig.add_annotation(text=f"<b>{int(vc.sum())}</b><br>cas", x=0.5, y=0.5, showarrow=False,
                       font=dict(size=18, color=P["ink"]))
    _base(fig, 380, legende_visible=True, haut=20)
    fig.update_layout(legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center", yanchor="top"))
    return fig


def decomposer(cpl: pd.Series):
    """Décomposition additive de la série complète (cycle de 4 semaines)."""
    if len(cpl) < 8:
        return None
    from statsmodels.tsa.seasonal import seasonal_decompose
    return seasonal_decompose(cpl.astype(float), model="additive", period=4)


def fig_decomposition(dec):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.07,
                        subplot_titles=("Cas observés", "Tendance de fond",
                                        "Cycle répétitif (4 semaines)", "Variations inexpliquées"))
    series = [(dec.observed, P["primary"]), (dec.trend, P["gold"]),
              (dec.seasonal, P["good"]), (dec.resid, P["bad"])]
    for i, (s, c) in enumerate(series, start=1):
        fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", line=dict(color=c, width=2.4),
                                 showlegend=False,
                                 hovertemplate="%{x|%d/%m/%Y} : <b>%{y:.1f}</b><extra></extra>"), row=i, col=1)
    _base(fig, 720, legende_visible=False, haut=40)
    fig.update_annotations(font=dict(color=P["ink"], size=13))
    return fig


def fig_prevision(hist: pd.Series, dates, prev, bas, haut):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist.values, name="Cas observés", mode="lines+markers",
        line=dict(color=P["primary"], width=2.6), marker=dict(size=5),
        hovertemplate="Semaine du %{x|%d/%m/%Y}<br><b>%{y}</b> cas<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=list(dates) + list(dates[::-1]), y=list(haut) + list(bas[::-1]), fill="toself",
        fillcolor=rgba(P["gold"], .20), line=dict(color="rgba(0,0,0,0)"),
        name="Zone d'incertitude (95 %)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=[hist.index[-1], dates[0]], y=[hist.iloc[-1], prev[0]], mode="lines", showlegend=False,
        line=dict(color=P["gold"], width=2, dash="dot"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=dates, y=prev, name="Prévision", mode="lines+markers",
        line=dict(color=P["gold"], width=3, dash="dash"), marker=dict(size=8, symbol="diamond"),
        hovertemplate="Semaine du %{x|%d/%m/%Y}<br>Prévu : <b>%{y:.1f}</b> cas<extra></extra>"))
    _ligne_verticale(fig, hist.index[-1], "Dernière semaine observée", P["muted"])
    _base(fig, 470, haut=44)
    fig.update_yaxes(title_text="Nombre de cas", rangemode="tozero")
    return fig


def fig_modeles(metrique: str):
    d = MODELES_EVAL.sort_values(metrique, ascending=False)
    mini = float(d[metrique].min())
    coul = [P["gold"] if v == mini else P["primary"] for v in d[metrique]]
    fig = go.Figure(go.Bar(
        y=d["Modèle"].tolist(), x=d[metrique].tolist(), orientation="h", marker_color=coul,
        text=[f"{v:.2f}" for v in d[metrique]], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>erreur moyenne : %{x:.2f} cas/semaine<extra></extra>"))
    _base(fig, 400, legende_visible=False)
    fig.update_xaxes(title_text="Erreur moyenne (cas par semaine) — plus petit = meilleur",
                     range=[0, float(d[metrique].max()) * 1.2])
    fig.update_yaxes(automargin=True)
    return fig


def fig_manquantes(df: pd.DataFrame):
    cols = [c for c in df.columns if c not in COLONNES_TECH]
    pct = (df[cols].isna().mean() * 100).sort_values(ascending=False)
    pct = pct[pct > 0].head(25)
    if pct.empty:
        return None
    pct = pct.iloc[::-1]
    coul = [P["bad"] if v > 80 else (P["warn"] if v >= 20 else P["primary"]) for v in pct.values]
    fig = go.Figure(go.Bar(
        y=pct.index.tolist(), x=[float(v) for v in pct.values], orientation="h", marker_color=coul,
        text=[f"{v:.0f} %" for v in pct.values], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:.1f} % d'informations manquantes<extra></extra>"))
    _base(fig, max(360, 26 * len(pct) + 80), legende_visible=False)
    fig.update_xaxes(title_text="Part d'informations manquantes (%)", range=[0, 118])
    fig.update_yaxes(automargin=True)
    return fig


# ==========================================================
# 7. TEXTES D'INTERPRÉTATION (calculés sur les données)
# ==========================================================

def phrase_tendance(t: dict) -> str:
    sens = {"hausse_forte": "une <b>hausse marquée</b>", "hausse": "une <b>hausse</b>",
            "baisse": "une <b>baisse</b>", "stable": "une <b>situation stable</b>"}[t["sens"]]
    return (f"Sur les 4 dernières semaines, on compte en moyenne <b>{t['dern']:.1f} cas par semaine</b>, "
            f"contre {t['prec']:.1f} sur les 4 semaines précédentes : c'est {sens} "
            f"({t['variation']:+.0f} %).")


def lecture_evolution(obs: pd.Series, cpl: pd.Series) -> list[str]:
    if obs.empty:
        return []
    r = resume_serie(obs, cpl)
    pts = [f"Le <b>pic</b> a été atteint la semaine du <b>{fdate(r['date_max'])}</b> avec <b>{r['maxi']} cas</b>."]
    if r["total"] > 0 and len(obs) >= 5:
        part = obs.nlargest(5).sum() / r["total"] * 100
        pts.append(f"Les <b>5 semaines les plus chargées</b> concentrent <b>{part:.0f} %</b> de tous les cas.")
    if r["moyenne"] > r["mediane"] * 1.2:
        pts.append(f"Une semaine « typique » compte <b>{r['mediane']:.0f} cas</b>, alors que la moyenne est de "
                   f"{r['moyenne']:.1f} : quelques semaines très chargées tirent la moyenne vers le haut.")
    sans = r["n_tot"] - r["n_obs"]
    if sans > 0:
        pts.append(f"<b>{sans} semaine(s)</b> de la période n'ont aucun cas déclaré (comptées à 0 dans les courbes).")
    t = tendance_recente(cpl)
    if t:
        pts.append(phrase_tendance(t))
    return pts


def lecture_territoire(d: pd.DataFrame) -> list[str]:
    if "Nom_region" not in d.columns:
        return []
    vc = d["Nom_region"].value_counts()
    if vc.empty:
        return []
    tot = int(vc.sum())
    pts = [f"<b>{vc.index[0]}</b> concentre <b>{vc.iloc[0] / tot * 100:.1f} %</b> des cas ({int(vc.iloc[0])} cas)."]
    if len(vc) >= 3:
        pts.append(f"Les 3 premières régions ({', '.join(vc.index[:3])}) regroupent "
                   f"<b>{vc.iloc[:3].sum() / tot * 100:.0f} %</b> des cas.")
    faibles = int((vc < 5).sum())
    pts.append(f"<b>{len(vc)} région(s)</b> ont signalé au moins un cas ; <b>{faibles}</b> en comptent moins de 5.")
    return pts


def lecture_patients(d: pd.DataFrame) -> list[str]:
    pts = []
    if "Age_Annee" in d.columns:
        a = pd.to_numeric(d["Age_Annee"], errors="coerce").dropna()
        if len(a):
            pts.append(f"La moitié des patients a moins de <b>{a.median():.0f} ans</b> (âge moyen : {a.mean():.1f} ans).")
            tr = tranches_age(a).value_counts()
            if len(tr):
                pts.append(f"La tranche la plus touchée est celle des <b>{tr.idxmax()}</b> "
                           f"({tr.max() / len(a) * 100:.0f} % des cas).")
    sx = sexe_normalise(d)
    if sx is not None:
        vc = sx.dropna().value_counts()
        if len(vc):
            tot = vc.sum()
            pts.append(" · ".join(f"<b>{k}</b> : {v / tot * 100:.0f} %" for k, v in vc.items()) + " des cas.")
    return pts


# ==========================================================
# 8. PRÉVISIONS
# ==========================================================

@st.cache_data(show_spinner=False)
def calculer_prevision(serie: pd.Series, horizon: int, modele: str):
    try:
        from modeles import entrainer_sarima, entrainer_sarima_lisse
    except Exception as e:  # noqa: BLE001
        return {"erreur": f"Le module de prévision (modeles.py) est introuvable : {e}"}
    try:
        res = entrainer_sarima_lisse(serie, horizon) if "lissé" in modele else entrainer_sarima(serie, horizon)
    except Exception as e:  # noqa: BLE001
        return {"erreur": str(e)}
    if res is None:
        return {"erreur": "Le modèle n'a pas pu être entraîné sur ces données."}
    return {"res": res}


def niveau_alerte(prevision_moyenne: float, historique_moyen: float) -> dict:
    if prevision_moyenne > historique_moyen * 1.5:
        return dict(genre="bad", libelle="Alerte", titre="Alerte rouge : hausse significative prévue",
                    actions=["Activer les équipes d'intervention rapide.",
                             "Renforcer la surveillance dans les zones les plus touchées.",
                             "Intensifier le dépistage et préparer les capacités de test."])
    if prevision_moyenne > historique_moyen:
        return dict(genre="warn", libelle="À surveiller", titre="Surveillance renforcée recommandée",
                    actions=["Suivre l'évolution chaque semaine.",
                             "Vérifier la disponibilité des tests et du matériel.",
                             "Informer les équipes régionales d'une possible hausse."])
    return dict(genre="ok", libelle="Maîtrisée", titre="Situation maîtrisée : tendance stable ou en baisse",
                actions=["Continuer la surveillance de routine.",
                         "Maintenir l'analyse hebdomadaire des données.",
                         "Garder des capacités de réaction en cas de reprise."])


def bloc_previsions(df: pd.DataFrame, prefixe: str, detail: bool) -> None:
    obs, cpl = series_hebdo(df)
    if obs.empty:
        callout("warn", "Données temporelles indisponibles",
                "La colonne « Semaine_Epi » est nécessaire pour construire les prévisions.")
        return
    serie = cpl if PREVISION_SUR_SERIE_COMPLETE else obs

    c1, c2 = st.columns(2)
    with c1:
        horizon = st.slider("Combien de semaines à l'avance ?", 1, 12, 8, key=f"{prefixe}_h")
    with c2:
        modele = st.selectbox("Modèle de prévision", ["SARIMA (lissé)", "SARIMA (brut)"], key=f"{prefixe}_m",
                              help="Le modèle « lissé » atténue les à-coups de la série avant de projeter.")

    with st.spinner("Calcul de la prévision…"):
        out = calculer_prevision(serie, int(horizon), modele)
    if "erreur" in out:
        callout("bad", "La prévision n'a pas pu être calculée", out["erreur"])
        return
    res = out["res"]
    prev = np.asarray(res["forecast"], dtype=float)
    bas = np.asarray(res["lower"], dtype=float)
    haut = np.asarray(res["upper"], dtype=float)
    dates = pd.DatetimeIndex(pd.to_datetime(list(res["dates"])))
    negatif = bool((prev < 0).any() or (bas < 0).any())
    prev, bas, haut = np.clip(prev, 0, None), np.clip(bas, 0, None), np.clip(haut, 0, None)

    moy_prev = float(prev.mean())
    moy_hist = float(serie.mean())
    niv = niveau_alerte(moy_prev, moy_hist)
    i_pic = int(np.argmax(prev))

    rangee_kpi([
        dict(libelle="Prévision moyenne", valeur=fmt(moy_prev, 1), sous=f"cas par semaine sur {len(prev)} semaines", ic="target", accent=True),
        dict(libelle="Semaine la plus chargée prévue", valeur=fmt(prev[i_pic], 1), sous=f"semaine du {fdate(dates[i_pic])}", ic="trend"),
        dict(libelle="Moyenne historique", valeur=fmt(moy_hist, 1), sous="cas par semaine (repère de comparaison)", ic="bar"),
        dict(libelle="Niveau", valeur=pastille(niv["libelle"], niv["genre"]), sous="comparé à l'historique", ic="shield"),
    ])

    section("Projection des cas", "La ligne pointillée dorée est la prévision ; la zone dorée indique la fourchette plausible.")
    titre_graphique(f"Cas observés et prévision sur {len(prev)} semaines", "target")
    afficher(fig_prevision(serie, dates, prev, bas, haut))
    legende("plus on s'éloigne dans le temps, plus la zone d'incertitude s'élargit : "
            "la prévision est une <b>estimation</b>, pas une certitude."
            + (" Les valeurs négatives éventuelles sont ramenées à 0 (un nombre de cas ne peut pas être négatif)." if negatif else ""))

    ecrire_alerte(niv, moy_prev)

    if detail:
        section("Détail semaine par semaine")
        table_html(
            ["Semaine du", "Prévision (cas)", "Fourchette basse", "Fourchette haute"],
            [[fdate(d), fmt(p, 1), fmt(b, 1), fmt(h, 1)] for d, p, b, h in zip(dates, prev, bas, haut)],
            num_cols=(1, 2, 3),
        )
        with st.expander("Détails techniques (pour les spécialistes)"):
            if "order" in res:
                st.write(f"Modèle : SARIMA{res['order']}x{res.get('seasonal_order', '')}")
            if "aic" in res:
                try:
                    st.write(f"AIC : {float(res['aic']):.2f}")
                except (TypeError, ValueError):
                    pass
            st.write(f"Série utilisée pour l'entraînement : {'complète (semaines sans cas = 0)' if PREVISION_SUR_SERIE_COMPLETE else 'semaines avec au moins un cas'}.")


def ecrire_alerte(niv: dict, moy_prev: float) -> None:
    li = "".join(f"<li>{a}</li>" for a in niv["actions"])
    callout(niv["genre"], niv["titre"],
            f"Prévision moyenne : <b>{moy_prev:.1f} cas par semaine</b>.<br><b>Actions suggérées :</b><ul>{li}</ul>")


# ==========================================================
# 9. SECTIONS D'ANALYSE (réutilisées par les pages et le tableau de bord)
# ==========================================================

def sec_evolution(d: pd.DataFrame, obs: pd.Series, cpl: pd.Series) -> None:
    if obs.empty:
        callout("warn", "Aucune donnée pour cette sélection", "Élargissez la période ou les filtres.")
        return
    r = resume_serie(obs, cpl)
    rangee_kpi([
        dict(libelle="Moyenne par semaine", valeur=fmt(r["moyenne"], 2),
             sous=f"semaines avec cas (n = {r['n_obs']}) · {fmt(r['moyenne_cpl'], 2)} en incluant les {r['n_tot'] - r['n_obs']} semaines sans cas", ic="bar"),
        dict(libelle="Semaine typique (médiane)", valeur=fmt(r["mediane"], 0), sous="la moitié des semaines est en dessous", ic="activity"),
        dict(libelle="Semaine la plus chargée", valeur=fmt(r["maxi"], 0), sous=f"semaine du {fdate(r['date_max'])}", ic="trend", accent=True),
        dict(libelle="Irrégularité (écart-type)", valeur=fmt(r["ecart"], 2), sous="plus c'est grand, plus les semaines diffèrent", ic="layers"),
    ])
    section("Évolution hebdomadaire", "Combien de cas suspects sont signalés chaque semaine ?")
    titre_graphique("Cas suspects par semaine", "trend")
    afficher(fig_evolution(cpl))
    legende("chaque point est une semaine (repérée par son lundi). La ligne dorée lisse les à-coups en moyennant 4 semaines : "
            "elle montre la <b>direction générale</b>. Les semaines sans cas déclaré sont affichées à 0.")
    pts = lecture_evolution(obs, cpl)
    if pts:
        carte_lecture("Ce qu'il faut retenir", pts)

    section("Répartition des semaines", "Les semaines très chargées sont-elles fréquentes ou exceptionnelles ?")
    titre_graphique("Combien de semaines pour chaque niveau d'activité ?", "bar")
    afficher(fig_distribution(cpl))
    legende("chaque barre indique combien de semaines ont eu ce nombre de cas. La barre grise correspond aux semaines "
            "sans cas. Une longue « queue » à droite signale quelques semaines exceptionnelles.")


def sec_territoire(d: pd.DataFrame) -> None:
    if "Nom_region" not in d.columns or d["Nom_region"].dropna().empty:
        callout("warn", "Données géographiques indisponibles", "La colonne « Nom_region » est absente ou vide.")
        return
    vc = d["Nom_region"].value_counts()
    section("Où sont les cas ?", "Répartition des cas suspects par région.")
    c1, c2 = st.columns([1.15, 1])
    with c1:
        titre_graphique("Nombre de cas par région", "map")
        afficher(fig_regions(vc))
        legende("la barre dorée est la région la plus touchée ; le pourcentage est sa part du total national.")
    with c2:
        titre_graphique("Poids de chaque région", "pie")
        afficher(fig_treemap(vc))
        legende("plus le rectangle est grand et foncé, plus la région compte de cas.")
    pts = lecture_territoire(d)
    if pts:
        carte_lecture("Ce qu'il faut retenir", pts)

    section("Évolution dans les régions principales", "Les régions les plus touchées évoluent-elles en même temps ?")
    titre_graphique("Cas par semaine dans les 5 régions les plus touchées", "trend")
    afficher(fig_evolution_regions(d))
    legende("chaque courbe correspond à une région. Passez la souris sur le graphique pour comparer les régions semaine par semaine.")

    if "Nom_District_Residence" in d.columns and d["Nom_District_Residence"].notna().any():
        section("Districts les plus touchés")
        vd = d["Nom_District_Residence"].value_counts().head(10)
        titre_graphique("10 districts comptant le plus de cas", "building")
        afficher(fig_regions(vd))
    if len(vc) >= 3:
        callout("tip", "Pistes d'action",
                "<ul><li>Renforcer la surveillance dans les 3 régions les plus touchées.</li>"
                "<li>Coordonner les actions au niveau national.</li>"
                "<li>Pré-positionner les ressources avant une éventuelle reprise.</li></ul>")


def sec_patients(d: pd.DataFrame) -> None:
    ages = pd.to_numeric(d["Age_Annee"], errors="coerce") if "Age_Annee" in d.columns else pd.Series(dtype=float)
    sexe = sexe_normalise(d)
    if ages.dropna().empty and (sexe is None or sexe.dropna().empty):
        callout("warn", "Données de profil indisponibles", "Les colonnes « Age_Annee » et « Sexe » sont absentes ou vides.")
        return
    items = []
    if not ages.dropna().empty:
        a = ages.dropna()
        items.append(dict(libelle="Âge médian", valeur=f"{a.median():.0f} ans", sous=f"âge moyen : {a.mean():.1f} ans", ic="user", accent=True))
        items.append(dict(libelle="Moins de 15 ans", valeur=f"{(a < 15).mean() * 100:.0f} %", sous="part des cas", ic="users"))
    if sexe is not None and not sexe.dropna().empty:
        vc = sexe.dropna().value_counts()
        for k in ["Masculin", "Féminin"]:
            if k in vc.index:
                items.append(dict(libelle=k, valeur=f"{vc[k] / vc.sum() * 100:.0f} %", sous=f"{int(vc[k])} cas", ic="users"))
    if items:
        rangee_kpi(items[:4])
    section("Qui est touché ?", "Âge et sexe des personnes concernées.")
    c1, c2 = st.columns([1.3, 1])
    with c1:
        titre_graphique("Âge des patients", "user")
        afficher(fig_age(ages))
        legende("chaque barre regroupe les patients par tranche de 5 ans d'âge.")
    with c2:
        titre_graphique("Répartition par sexe", "users")
        if sexe is not None:
            afficher(fig_sexe(sexe))
    if sexe is not None and not ages.dropna().empty:
        titre_graphique("Tranches d'âge selon le sexe", "layers")
        afficher(fig_age_sexe(ages, sexe))
        legende("compare, pour chaque tranche d'âge, le nombre de cas masculins et féminins.")
    pts = lecture_patients(d)
    if pts:
        carte_lecture("Ce qu'il faut retenir", pts)


def sec_clinique(d: pd.DataFrame) -> None:
    pcr = statut_pcr(d)
    if pcr is not None and len(pcr):
        vc = pcr.value_counts()
        n = len(pcr)
        npos = int(vc.get("Positif", 0))
        nneg = int(vc.get("Négatif", 0))
        natt = int(vc.get("En attente / non renseigné", 0))
        rangee_kpi([
            dict(libelle="Cas confirmés (PCR positif)", valeur=fmt(npos), sous=f"{npos / n * 100:.1f} % des cas suspects", ic="flask", accent=True),
            dict(libelle="Tests négatifs", valeur=fmt(nneg), sous=f"{nneg / n * 100:.1f} % des cas suspects", ic="check"),
            dict(libelle="En attente / non renseigné", valeur=fmt(natt), sous=f"{natt / n * 100:.1f} % des cas suspects", ic="clock"),
        ])
        section("Résultats des tests de laboratoire", "Parmi les personnes suspectes, combien sont réellement confirmées ?")
        c1, c2 = st.columns([1, 1.1])
        with c1:
            titre_graphique("Résultat du test PCR", "flask")
            afficher(fig_pcr(pcr))
        with c2:
            titre_graphique("Détail", "info")
            table_html(["Résultat", "Cas", "Part"],
                       [[pastille(k, {"Positif": "bad", "Négatif": "info"}.get(k, "warn")), fmt(int(v)), f"{v / n * 100:.1f} %"]
                        for k, v in vc.items()], num_cols=(1, 2))
            callout("info", "À savoir",
                    "Un <b>cas suspect</b> est une personne présentant des signes évocateurs ; seul le <b>test PCR</b> "
                    "confirme la maladie. Avec un petit nombre de cas confirmés, les pourcentages sont à interpréter avec prudence.")
    section("Signes cliniques", "Quels symptômes sont les plus fréquents parmi les cas ?")
    c1, c2 = st.columns(2)
    with c1:
        titre_graphique("Symptômes", "thermo")
        t = taux_oui(d, SYMPTOMES)
        if t.empty:
            st.info("Aucune colonne de symptômes exploitable.")
        else:
            afficher(fig_taux(t))
            legende("part des cas qui présentent chaque symptôme, parmi ceux pour lesquels l'information est renseignée "
                    "(entre parenthèses : cas concernés / cas renseignés).")
    with c2:
        titre_graphique("Localisation des lésions", "user")
        t = taux_oui(d, LESIONS)
        if t.empty:
            st.info("Aucune colonne de localisation exploitable.")
        else:
            afficher(fig_taux(t))
            legende("où apparaissent les lésions sur le corps, parmi les cas renseignés.")


def sec_tendance(cpl: pd.Series) -> None:
    dec = None
    if len(cpl) >= 8:
        try:
            dec = decomposer(cpl)
        except Exception as e:  # noqa: BLE001
            callout("warn", "Décomposition indisponible", f"{e}")
            return
    if dec is None:
        callout("warn", "Pas assez de semaines", "Il faut au moins 8 semaines pour séparer tendance et cycle.")
        return
    section("Décomposer la courbe", "Séparer ce qui est durable de ce qui est ponctuel.")
    titre_graphique("Cas observés, tendance de fond, cycle et variations", "layers")
    afficher(fig_decomposition(dec))
    legende("la courbe observée (en haut) est découpée en trois ingrédients : la <b>tendance de fond</b> (hausse ou baisse durable), "
            "un <b>cycle répétitif de 4 semaines</b>, et les <b>variations inexpliquées</b> (le « bruit »).")
    tr = dec.trend.dropna()
    if len(tr) >= 6:
        k = max(2, len(tr) // 3)
        deb, fin = float(tr.iloc[:k].mean()), float(tr.iloc[-k:].mean())
        var = (fin - deb) / max(deb, 1.0) * 100
        if var <= -15:
            lecture = f"La tendance de fond est <b>à la baisse</b> ({deb:.1f} → {fin:.1f} cas par semaine, {var:+.0f} %)."
        elif var >= 15:
            lecture = f"La tendance de fond est <b>à la hausse</b> ({deb:.1f} → {fin:.1f} cas par semaine, {var:+.0f} %)."
        else:
            lecture = f"La tendance de fond est <b>globalement stable</b> ({deb:.1f} → {fin:.1f} cas par semaine)."
        amp = float(dec.seasonal.max() - dec.seasonal.min())
        carte_lecture("Ce qu'il faut retenir", [
            lecture,
            f"Le cycle de 4 semaines est d'amplitude <b>{amp:.1f} cas</b> : "
            + ("il est faible, ce n'est pas lui qui explique les variations." if amp < max(1.0, 0.15 * cpl.max()) else "il pèse sensiblement sur les variations."),
            "La série couvre moins de deux ans : on ne peut pas conclure à une <b>saisonnalité annuelle</b> (ex. pics récurrents à une saison donnée).",
        ])


def sec_modeles() -> None:
    m = MEILLEUR
    rangee_kpi([
        dict(libelle="Meilleur modèle", valeur=str(m["Modèle"]), sous="le plus précis sur les deux mesures d'erreur", ic="award", accent=True),
        dict(libelle="Erreur moyenne (RMSE)", valeur=f"{m['RMSE']:.2f}", sous="cas par semaine d'écart typique", ic="target"),
        dict(libelle="Écart absolu moyen (MAE)", valeur=f"{m['MAE']:.2f}", sous="cas par semaine d'écart moyen", ic="bar"),
        dict(libelle="Modèles comparés", valeur=str(len(MODELES_EVAL)), sous="du plus simple au plus avancé", ic="layers"),
    ])
    section("Quel modèle prévoit le mieux ?",
            "Plusieurs méthodes de prévision ont été mises en concurrence. Plus l'erreur est petite, plus le modèle est fiable.")
    c1, c2 = st.columns(2)
    with c1:
        titre_graphique("Erreur moyenne — RMSE", "award")
        afficher(fig_modeles("RMSE"))
        legende("le RMSE est l'écart typique entre la prévision et la réalité, en cas par semaine. "
                "Il <b>pénalise davantage les grosses erreurs</b>.")
    with c2:
        titre_graphique("Écart absolu moyen — MAE", "award")
        afficher(fig_modeles("MAE"))
        legende("le MAE est l'écart moyen entre la prévision et la réalité. Il traite toutes les erreurs de la même façon.")
    callout("ok", f"{m['Modèle']} est le modèle retenu",
            f"Avec une erreur typique de <b>{m['RMSE']:.1f} cas par semaine</b> (RMSE) et de <b>{m['MAE']:.1f}</b> (MAE), "
            "il fait mieux que tous les autres, y compris les modèles plus complexes. Ses deux mesures d'erreur sont cohérentes, "
            "ce qui indique qu'il ne commet pas de grosses erreurs isolées.")
    section("Classement détaillé")
    d = MODELES_EVAL.sort_values("RMSE").reset_index(drop=True)
    lignes = []
    for i, r in d.iterrows():
        rel = r["RMSE"] / m["RMSE"]
        verdict = pastille("Meilleur", "gold") if i == 0 else (pastille("Bon", "ok") if rel < 1.5 else (pastille("Moyen", "warn") if rel < 2.8 else pastille("Faible", "bad")))
        lignes.append([i + 1, f"<b>{r['Modèle']}</b>", f"{r['RMSE']:.2f}", f"{r['MAE']:.2f}",
                       "—" if pd.isna(r["AIC"]) else f"{r['AIC']:.2f}", verdict])
    table_html(["Rang", "Modèle", "RMSE", "MAE", "AIC", "Verdict"], lignes, num_cols=(0, 2, 3, 4))
    legende("le <b>AIC</b> mesure la qualité d'ajustement aux données passées (plus petit = mieux, surtout utile pour comparer des modèles proches) ; "
            "RMSE et MAE mesurent la qualité des prévisions.")


def sec_qualite(df: pd.DataFrame) -> None:
    cols = [c for c in df.columns if c not in COLONNES_TECH]
    pct = df[cols].isna().mean() * 100
    n_sup = int((pct > 80).sum())
    n_knn = int(((pct >= 20) & (pct <= 80)).sum())
    n_simple = int(((pct > 0) & (pct < 20)).sum())
    n_ok = int((pct == 0).sum())
    complet = 100 - float(pct.mean())
    sans_date = int(df["Date"].isna().sum()) if "Date" in df.columns else 0
    rangee_kpi([
        dict(libelle="Complétude globale", valeur=f"{complet:.0f} %", sous="cases renseignées dans la base", ic="database", accent=True),
        dict(libelle="Variables complètes", valeur=fmt(n_ok), sous=f"sur {len(cols)} variables", ic="check"),
        dict(libelle="Variables quasi vides", valeur=fmt(n_sup), sous="plus de 80 % manquant", ic="alert"),
        dict(libelle="Cas sans date exploitable", valeur=fmt(sans_date), sous="semaine non reconnue", ic="calendar"),
    ])
    section("Les données sont-elles complètes ?", "Part d'informations manquantes par variable (les 25 plus concernées).")
    titre_graphique("Informations manquantes par variable", "database")
    afficher(fig_manquantes(df))
    legende(f"<span style='color:{P['bad']}'><b>rouge</b></span> : plus de 80 % manquant (variable écartée) · "
            f"<span style='color:{P['warn']}'><b>orange</b></span> : entre 20 et 80 % (estimation par ressemblance, méthode KNN) · "
            f"<span style='color:{P['primary']}'><b>bleu</b></span> : moins de 20 % (remplacement par la valeur la plus courante).")
    section("Règles de préparation des données")
    table_html(
        ["Part de valeurs manquantes", "Traitement appliqué", "Variables concernées"],
        [
            ["Plus de 80 %", "La variable est écartée : trop peu d'information pour la reconstituer", fmt(n_sup)],
            ["Entre 20 % et 80 %", "Estimation à partir des 5 cas les plus ressemblants (méthode KNN)", fmt(n_knn)],
            ["Moins de 20 %", "Médiane (nombres) ou valeur la plus fréquente (catégories)", fmt(n_simple)],
        ], num_cols=(2,))
    callout("info", "Pourquoi c'est important",
            "Les analyses reposent sur des déclarations de terrain : certaines informations ne sont pas renseignées. "
            "Chaque traitement est documenté et les variables presque vides ne sont pas utilisées.")


# ==========================================================
# 10. PAGES
# ==========================================================

def page_synthese(df: pd.DataFrame) -> None:
    obs, cpl = series_hebdo(df)
    n = len(df)
    pcr = statut_pcr(df)
    npos = int((pcr == "Positif").sum()) if pcr is not None else None
    chips = []
    if not cpl.empty:
        chips.append(f"Du {fdate(cpl.index.min())} au {fdate(cpl.index.max())}")
        chips.append(f"{len(cpl)} semaines suivies")
    chips.append("Source : surveillance DHIS2")
    entete("home", "Vue d'ensemble", "La situation de la Mpox au Sénégal, en un coup d'œil",
           "L'essentiel pour décider : où en est l'épidémie, où se concentrent les cas, et ce qu'il faut surveiller.", chips)

    nreg = df["Nom_region"].nunique() if "Nom_region" in df.columns else 0
    ndis = df["Nom_District_Residence"].nunique() if "Nom_District_Residence" in df.columns else 0
    age = pd.to_numeric(df["Age_Annee"], errors="coerce").dropna() if "Age_Annee" in df.columns else pd.Series(dtype=float)
    rangee_kpi([
        dict(libelle="Cas suspects signalés", valeur=fmt(n), sous="personnes présentant des signes évocateurs", ic="virus", accent=True),
        dict(libelle="Régions touchées", valeur=fmt(nreg), sous="ayant signalé au moins un cas", ic="map"),
        dict(libelle="Districts touchés", valeur=fmt(ndis), sous="lieux de résidence des cas", ic="building"),
        dict(libelle="Âge médian", valeur=f"{age.median():.0f} ans" if len(age) else "—",
             sous=f"âge moyen : {age.mean():.1f} ans" if len(age) else "", ic="user"),
    ])

    t = tendance_recente(cpl)
    if t:
        cfg = {
            "hausse_forte": ("bad", "alert", "Hausse marquée des cas"),
            "hausse": ("warn", "up", "Hausse à surveiller"),
            "stable": ("info", "flat", "Situation stable"),
            "baisse": ("ok", "down", "Tendance à la baisse"),
        }[t["sens"]]
        ecrire(
            f'<div class="status {cfg[0]}"><div class="dot">{icone(cfg[1], 30, "#FFFFFF")}</div><div>'
            f'<div class="lab">Situation actuelle</div><div class="tt">{cfg[2]}</div>'
            f'<div class="ds">{phrase_tendance(t)}<br>Les dernières semaines peuvent encore être complétées par de nouvelles déclarations.</div>'
            f'</div></div>')
    else:
        callout("info", "Situation actuelle", "Il faut au moins 8 semaines de données pour évaluer la tendance récente.")

    c1, c2 = st.columns([1.7, 1])
    with c1:
        titre_graphique("Cas suspects par semaine", "trend")
        afficher(fig_evolution(cpl))
        legende("la ligne dorée lisse les à-coups (moyenne sur 4 semaines) et montre la direction générale.")
    with c2:
        pts = []
        if not obs.empty:
            r = resume_serie(obs, cpl)
            pts.append(f"<b>{fmt(n)} cas suspects</b> signalés sur <b>{r['n_tot']} semaines</b>.")
            pts.append(f"Pic : <b>{r['maxi']} cas</b> la semaine du <b>{fdate(r['date_max'])}</b>.")
        if "Nom_region" in df.columns and not df["Nom_region"].dropna().empty:
            vc = df["Nom_region"].value_counts()
            pts.append(f"<b>{vc.index[0]}</b> concentre <b>{vc.iloc[0] / vc.sum() * 100:.0f} %</b> des cas.")
        if npos is not None:
            pts.append(f"<b>{npos} cas</b> sont confirmés par un test PCR (positif).")
        carte_lecture("À retenir", pts)

    if t:
        recos = {
            "hausse_forte": ("bad", "Que faire ?", ["Renforcer la surveillance et le dépistage dans les zones les plus touchées.",
                                                   "Préparer les capacités de test et de prise en charge.",
                                                   "Consulter la page « Prévisions » pour anticiper les prochaines semaines."]),
            "hausse": ("warn", "Que faire ?", ["Suivre l'évolution chaque semaine.",
                                              "Vérifier la disponibilité des tests et du matériel.",
                                              "Consulter la page « Prévisions »."]),
            "stable": ("info", "Que faire ?", ["Maintenir la surveillance de routine.",
                                              "Suivre ce tableau de bord chaque semaine.",
                                              "Consulter la page « Prévisions » pour anticiper."]),
            "baisse": ("ok", "Que faire ?", ["Maintenir la vigilance malgré la baisse.",
                                            "Poursuivre la surveillance de routine.",
                                            "Garder des capacités de réaction en cas de reprise."]),
        }[t["sens"]]
        callout(recos[0], recos[1], "<ul>" + "".join(f"<li>{x}</li>" for x in recos[2]) + "</ul>")
    callout("info", "Cas suspects et cas confirmés : ce n'est pas la même chose",
            "Les chiffres de cette application comptent les <b>cas suspects</b> (personnes présentant des signes évocateurs). "
            "Seuls les cas dont le test de laboratoire (PCR) est positif sont <b>confirmés</b>."
            + (f" Ici : <b>{npos}</b> confirmé(s) sur <b>{fmt(n)}</b> cas suspects." if npos is not None else ""))

    section("Explorer plus loin", "Choisissez la page qui répond à votre question.")
    cartes = [
        ("dashboard", "Tableau de bord", "Toutes les analyses réunies au même endroit, avec filtres par période, région et sexe.", "Tableau de bord"),
        ("target", "Prévisions", "À quoi s'attendre dans les prochaines semaines, avec un niveau d'alerte.", "Prévisions"),
        ("map", "Analyse spatiale", "Quelles régions sont les plus touchées ?", "Analyse spatiale"),
        ("file", "Rapport", "Télécharger le rapport complet (PDF, TXT) et les chiffres clés.", "Rapport"),
    ]
    cols = st.columns(len(cartes))
    for col, (ic, titre, desc, cible) in zip(cols, cartes):
        with col:
            ecrire(f'<div class="card nav"><div class="ic">{icone(ic, 26)}</div><div class="h">{titre}</div><p>{desc}</p></div>')
            st.button("Ouvrir", key=f"go_{cible}", on_click=aller_a, args=(cible,))


def page_dashboard(df: pd.DataFrame) -> None:
    obs_all, cpl_all = series_hebdo(df)
    entete("dashboard", "Tableau de bord", "Toutes les analyses, au même endroit",
           "Filtrez par période, région ou sexe, puis parcourez les sections : évolution, territoire, patients, laboratoire, tendance, prévisions, modèles et qualité des données.",
           [f"{fmt(len(df))} cas suspects", f"{len(cpl_all)} semaines" if len(cpl_all) else "Sans dates"])

    # ---------- Filtres ----------
    sem_options = list(cpl_all.index) if not cpl_all.empty else []
    with st.expander("Filtres de l'analyse", expanded=True):
        f1, f2, f3 = st.columns([1.6, 1.4, 1])
        with f1:
            if len(sem_options) >= 2:
                periode = st.select_slider("Période (semaines)", options=sem_options,
                                           value=(sem_options[0], sem_options[-1]),
                                           format_func=lambda x: pd.Timestamp(x).strftime("%d/%m/%Y"), key="f_periode")
            else:
                periode = None
        with f2:
            regions = []
            if "Nom_region" in df.columns:
                regions = st.multiselect("Régions", sorted(df["Nom_region"].dropna().unique().tolist()),
                                         placeholder="Toutes les régions", key="f_regions")
        with f3:
            sexe_f = st.selectbox("Sexe", ["Tous", "Masculin", "Féminin"], key="f_sexe") if "Sexe" in df.columns else "Tous"

    d = df
    if periode and (periode[0] != sem_options[0] or periode[1] != sem_options[-1]):
        d = d[(d["Date"] >= periode[0]) & (d["Date"] <= periode[1])]
    if regions:
        d = d[d["Nom_region"].isin(regions)]
    if sexe_f != "Tous":
        d = d[sexe_normalise(d) == sexe_f]

    actifs = []
    if periode and (periode[0] != sem_options[0] or periode[1] != sem_options[-1]):
        actifs.append("période")
    if regions:
        actifs.append("régions")
    if sexe_f != "Tous":
        actifs.append("sexe")
    if actifs:
        callout("info", "Filtres actifs", f"Les analyses ci-dessous portent sur <b>{fmt(len(d))} cas</b> sur {fmt(len(df))} (filtre : {', '.join(actifs)}). "
                "Les prévisions, la comparaison des modèles et la qualité des données portent toujours sur l'ensemble des données.")
    if d.empty:
        callout("warn", "Aucun cas pour cette sélection", "Élargissez la période ou retirez un filtre.")
        return

    d_obs = d.dropna(subset=["Date"]).groupby("Date").size().sort_index().astype(int) if "Date" in d.columns else pd.Series(dtype=int)
    if periode:
        d_cpl = completer(d_obs, periode[0], periode[1])
    else:
        d_cpl = completer(d_obs)

    pcr = statut_pcr(d)
    npos = int((pcr == "Positif").sum()) if pcr is not None else None
    r = resume_serie(d_obs, d_cpl) if not d_obs.empty else None
    items = [dict(libelle="Cas suspects", valeur=fmt(len(d)), sous="dans la sélection", ic="virus", accent=True)]
    if r:
        items.append(dict(libelle="Semaine la plus chargée", valeur=fmt(r["maxi"]), sous=f"semaine du {fdate(r['date_max'])}", ic="trend"))
        items.append(dict(libelle="Moyenne par semaine", valeur=fmt(r["moyenne_cpl"], 1), sous="semaines sans cas incluses", ic="bar"))
    if "Nom_region" in d.columns:
        items.append(dict(libelle="Régions touchées", valeur=fmt(d["Nom_region"].nunique()), sous="dans la sélection", ic="map"))
    if npos is not None:
        items.append(dict(libelle="Cas confirmés (PCR+)", valeur=fmt(npos), sous="test de laboratoire positif", ic="flask"))
    rangee_kpi(items[:5])

    sections = ["Évolution", "Territoire", "Patients", "Laboratoire & clinique", "Tendance", "Prévisions", "Modèles", "Qualité des données"]
    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
    choix = st.radio("Section", sections, horizontal=True, label_visibility="collapsed", key="dash_section")

    if choix == "Évolution":
        sec_evolution(d, d_obs, d_cpl)
    elif choix == "Territoire":
        sec_territoire(d)
    elif choix == "Patients":
        sec_patients(d)
    elif choix == "Laboratoire & clinique":
        sec_clinique(d)
    elif choix == "Tendance":
        sec_tendance(d_cpl)
    elif choix == "Prévisions":
        bloc_previsions(df, "dash", detail=False)
    elif choix == "Modèles":
        sec_modeles()
    else:
        sec_qualite(df)


def page_temporelle(df: pd.DataFrame) -> None:
    entete("trend", "Analyse temporelle", "Comment les cas évoluent-ils dans le temps ?",
           "Évolution semaine par semaine, répartition des niveaux d'activité et décomposition de la tendance.")
    if "Date" not in df.columns:
        callout("warn", "Données temporelles indisponibles", "La colonne « Semaine_Epi » est nécessaire.")
        return
    regions = []
    if "Nom_region" in df.columns:
        regions = st.multiselect("Filtrer par région (laisser vide = tout le pays)",
                                 sorted(df["Nom_region"].dropna().unique().tolist()),
                                 placeholder="Toutes les régions", key="t_regions")
    d = df[df["Nom_region"].isin(regions)] if regions else df
    obs, cpl_all = series_hebdo(df)
    d_obs = d.dropna(subset=["Date"]).groupby("Date").size().sort_index().astype(int)
    cpl = completer(d_obs, cpl_all.index.min(), cpl_all.index.max()) if not cpl_all.empty and not d_obs.empty else d_obs
    sec_evolution(d, d_obs, cpl)
    sec_tendance(cpl)


def page_previsions(df: pd.DataFrame) -> None:
    entete("target", "Prévisions", "À quoi s'attendre dans les prochaines semaines ?",
           "Projection du nombre de cas suspects par semaine, avec une fourchette d'incertitude et un niveau d'alerte.")
    callout("info", "Comment lire ces prévisions ?",
            "<ul><li>Modèle : <b>SARIMA</b>, une méthode statistique qui prolonge la courbe en tenant compte de l'historique.</li>"
            "<li>La zone dorée est un <b>intervalle de confiance à 95 %</b> : la réalité devrait s'y situer dans la grande majorité des cas.</li>"
            "<li>Plus l'horizon est lointain, plus l'incertitude augmente.</li></ul>")
    bloc_previsions(df, "prev", detail=True)


def page_modeles() -> None:
    entete("award", "Comparaison des modèles", "Quel modèle prévoit le mieux ?",
           f"{len(MODELES_EVAL)} méthodes de prévision comparées sur les mêmes données : la plus précise est retenue.")
    sec_modeles()


def page_spatiale(df: pd.DataFrame) -> None:
    entete("map", "Analyse spatiale", "Où se concentrent les cas ?",
           "Répartition géographique des cas suspects par région et par district.")
    sec_territoire(df)


def page_rapport(df: pd.DataFrame) -> None:
    entete("file", "Rapport", "Télécharger les documents",
           "Rapport complet de surveillance au format PDF ou texte, et chiffres clés exportables dans Excel.")
    obs, cpl = series_hebdo(df)
    rangee_kpi([
        dict(libelle="Cas suspects", valeur=fmt(len(df)), sous="dans le rapport", ic="virus", accent=True),
        dict(libelle="Régions", valeur=fmt(df["Nom_region"].nunique() if "Nom_region" in df.columns else 0), sous="touchées", ic="map"),
        dict(libelle="Districts", valeur=fmt(df["Nom_District_Residence"].nunique() if "Nom_District_Residence" in df.columns else 0), sous="touchés", ic="building"),
    ])
    rapport = None
    if os.path.exists("rapport_final_mpox.txt"):
        with open("rapport_final_mpox.txt", "r", encoding="utf-8") as f:
            rapport = f.read()

    section("Documents disponibles")
    c1, c2, c3 = st.columns(3)
    with c1:
        ecrire(f'<div class="card nav"><div class="ic">{icone("file", 26)}</div><div class="h">Rapport PDF</div>'
               "<p>Document professionnel avec page de garde, sommaire, graphiques et recommandations.</p></div>")
        if st.button("Préparer le PDF", key="btn_pdf"):
            with st.spinner("Génération du PDF en cours…"):
                try:
                    from pdf_generator_v6 import generer_pdf_v6
                    chemin = generer_pdf_v6(
                        rapport_txt=rapport if rapport else "Rapport de surveillance Mpox - Sénégal",
                        df=df, modeles_data=MODELES_DATA,
                        output_path=f"rapport_mpox_{datetime.now().strftime('%Y%m%d')}.pdf")
                    with open(chemin, "rb") as f:
                        st.session_state["pdf_bytes"] = f.read()
                    st.session_state["pdf_nom"] = os.path.basename(chemin)
                except Exception as e:  # noqa: BLE001
                    st.session_state.pop("pdf_bytes", None)
                    callout("bad", "Le PDF n'a pas pu être généré", f"{e}")
                    with st.expander("Détails techniques"):
                        st.code(traceback.format_exc())
        if "pdf_bytes" in st.session_state:
            st.download_button("Télécharger le PDF", data=st.session_state["pdf_bytes"],
                               file_name=st.session_state["pdf_nom"], mime="application/pdf", key="dl_pdf")
    with c2:
        ecrire(f'<div class="card nav"><div class="ic">{icone("file", 26)}</div><div class="h">Rapport texte</div>'
               "<p>Version texte simple du rapport, facile à copier dans un autre document.</p></div>")
        if rapport:
            st.download_button("Télécharger le TXT", data=rapport,
                               file_name=f"rapport_mpox_{datetime.now().strftime('%Y%m%d')}.txt",
                               mime="text/plain", key="dl_txt")
        else:
            st.caption("Fichier rapport_final_mpox.txt non trouvé.")
    with c3:
        ecrire(f'<div class="card nav"><div class="ic">{icone("database", 26)}</div><div class="h">Chiffres clés (Excel)</div>'
               "<p>Cas par semaine, prêts à être ouverts dans Excel (fichier CSV).</p></div>")
        if not cpl.empty:
            tab = cpl.rename("Cas_suspects").rename_axis("Semaine_du_lundi").reset_index()
            tab["Semaine_du_lundi"] = tab["Semaine_du_lundi"].dt.strftime("%d/%m/%Y")
            st.download_button("Télécharger le CSV", data=tab.to_csv(index=False, sep=";").encode("utf-8-sig"),
                               file_name=f"cas_par_semaine_{datetime.now().strftime('%Y%m%d')}.csv",
                               mime="text/csv", key="dl_csv")

    if "pdf_bytes" in st.session_state:
        callout("ok", "PDF prêt", "Contenu : page de garde · sommaire · synthèse et évolution · top 10 des régions · "
                "comparaison des modèles · décomposition de la série · prévisions · recommandations.")
    if rapport:
        section("Aperçu du rapport")
        with st.expander("Lire le rapport texte"):
            st.text(rapport)


GLOSSAIRE = [
    ("Cas suspect", "Personne présentant des signes pouvant évoquer la Mpox (fièvre, éruption…). Son statut n'est pas encore confirmé."),
    ("Cas confirmé (PCR positif)", "Cas dont le test de laboratoire (PCR) a détecté le virus."),
    ("Test PCR", "Analyse de laboratoire qui recherche le matériel génétique du virus. Résultat : positif, négatif ou en attente."),
    ("Semaine épidémiologique", "Semaine numérotée utilisée par les services de santé pour comparer les périodes. Ici, chaque semaine est repérée par son lundi."),
    ("Moyenne et médiane", "La moyenne est la somme divisée par le nombre de semaines ; la médiane est la valeur « du milieu ». Quand quelques semaines sont très chargées, la médiane décrit mieux la semaine typique."),
    ("Moyenne mobile (4 semaines)", "Moyenne glissante qui lisse les à-coups pour faire ressortir la direction générale."),
    ("Tendance de fond", "Évolution durable (hausse ou baisse) une fois les variations de court terme retirées."),
    ("Prévision", "Estimation du nombre de cas des prochaines semaines, calculée à partir de l'historique. Ce n'est pas une certitude."),
    ("Intervalle de confiance à 95 %", "Fourchette autour de la prévision dans laquelle la réalité devrait se situer dans environ 95 % des cas si le modèle est fiable."),
    ("SARIMA", "Modèle statistique de séries temporelles : il prolonge la courbe en tenant compte de la tendance et des cycles passés."),
    ("RMSE et MAE", "Deux mesures de l'erreur d'un modèle, en cas par semaine. Plus elles sont petites, meilleur est le modèle. Le RMSE pénalise davantage les grosses erreurs."),
    ("Valeurs manquantes", "Informations non renseignées dans les fiches de déclaration. Elles sont traitées selon des règles prudentes et documentées."),
]


def page_guide(df: pd.DataFrame) -> None:
    entete("help", "Aide", "Guide de lecture et glossaire",
           "Tout ce qu'il faut savoir pour utiliser cette application sans connaissance technique.")
    section("Utiliser l'application en 3 étapes")
    c1, c2, c3 = st.columns(3)
    for col, (n, titre, txt) in zip((c1, c2, c3), [
        (1, "Commencer par la synthèse", "La page « Synthèse » donne la situation actuelle, les chiffres clés et ce qu'il faut faire."),
        (2, "Approfondir dans le tableau de bord", "Filtrez par période, région ou sexe, puis choisissez une section d'analyse."),
        (3, "Anticiper et partager", "La page « Prévisions » projette les prochaines semaines ; la page « Rapport » permet de tout télécharger."),
    ]):
        with col:
            ecrire(f'<div class="card nav"><div class="ic" style="font-family:Fraunces,serif;font-size:1.6rem;font-weight:700">{n}</div>'
                   f'<div class="h">{titre}</div><p>{txt}</p></div>')

    section("Ce qu'il faut garder en tête", "Pour interpréter les chiffres avec justesse.")
    pcr = statut_pcr(df)
    npos = int((pcr == "Positif").sum()) if pcr is not None else None
    callout("warn", "Cas suspects ≠ personnes malades",
            "Les chiffres comptent les cas suspects. La grande majorité d'entre eux se révèle négative au test."
            + (f" Ici, seuls <b>{npos}</b> cas sont confirmés sur <b>{fmt(len(df))}</b>." if npos is not None else ""))
    callout("warn", "Les dernières semaines sont provisoires", "Les déclarations arrivent avec un délai : les chiffres des semaines les plus récentes peuvent encore augmenter.")
    callout("warn", "Une prévision est une estimation", "Elle est d'autant moins précise que l'horizon est lointain. Utilisez-la pour anticiper, pas pour affirmer.")
    callout("info", "Petits effectifs", "Quand un groupe compte peu de cas (par exemple une petite région ou les cas confirmés), les pourcentages varient beaucoup d'une semaine à l'autre.")

    section("Comment le niveau de situation est évalué")
    table_html(
        ["Variation des 4 dernières semaines vs les 4 précédentes", "Niveau affiché"],
        [["+50 % ou plus", pastille("Hausse marquée", "bad")],
         ["De +20 % à +50 %", pastille("Hausse à surveiller", "warn")],
         ["Entre −20 % et +20 %", pastille("Situation stable", "info")],
         ["−20 % ou moins", pastille("Tendance à la baisse", "ok")]])
    legende("ces seuils sont des repères de lecture adoptés dans cette application, pas des seuils officiels. "
            "Pour les prévisions, le niveau compare la prévision moyenne à la moyenne historique (alerte au-delà de 1,5 fois).")

    section("Glossaire")
    for k, v in GLOSSAIRE:
        ecrire(f'<div class="gl"><div class="k">{k}</div><div class="v">{v}</div></div>')

    section("D'où viennent les données ?")
    callout("info", "Source et méthode",
            "Les données proviennent de la surveillance nationale (plateforme DHIS2) : une ligne par cas suspect. "
            "Les cas sont regroupés par semaine pour construire la courbe d'évolution, puis analysés et utilisés pour les prévisions. "
            "Aucune donnée individuelle n'est affichée dans cette application : seuls des totaux et des répartitions le sont.")


# ==========================================================
# 11. PROGRAMME PRINCIPAL
# ==========================================================

def main() -> None:
    injecter_css()

    sb = st.sidebar
    sb.markdown(
        f'<div class="brand"><div class="lg">{icone("virus", 24, "#0E1A33")}</div>'
        f'<div><div class="n">Mpox Sénégal</div><div class="s">Surveillance</div></div></div>',
        unsafe_allow_html=True)
    sb.markdown('<div class="slab">Navigation</div>', unsafe_allow_html=True)
    page = sb.radio("Navigation", [p for p, _ in PAGES], label_visibility="collapsed", key="nav")

    df, erreur = charger_donnees()

    if df is not None:
        obs, cpl = series_hebdo(df)
        lignes = [("Cas suspects", fmt(len(df)))]
        if "Nom_region" in df.columns:
            lignes.append(("Régions", fmt(df["Nom_region"].nunique())))
        if not cpl.empty:
            lignes.append(("Semaines suivies", fmt(len(cpl))))
            lignes.append(("Période", f"{fdate(cpl.index.min(), True)} → {fdate(cpl.index.max(), True)}"))
        lignes.append(("Meilleur modèle", f"{MEILLEUR['Modèle']} (RMSE {MEILLEUR['RMSE']:.2f})"))
        sb.markdown('<div class="slab">Aperçu des données</div>', unsafe_allow_html=True)
        ecrire_sb = "".join(f'<div class="r"><span>{a}</span><span>{b}</span></div>' for a, b in lignes)
        sb.markdown(f'<div class="sbcard">{ecrire_sb}</div>', unsafe_allow_html=True)

    sb.markdown('<div class="slab">Affichage</div>', unsafe_allow_html=True)
    sb.toggle("Mode sombre", key="mode_sombre")
    sb.markdown(f'<div class="sbfoot">© {datetime.now().year} — Etud_L3 SID<br>Données de surveillance · usage interne</div>',
                unsafe_allow_html=True)

    if df is None:
        entete("alert", "Données indisponibles", "L'application ne trouve pas la base de données",
               "Vérifiez que le fichier Excel de la base est bien présent à côté de l'application.")
        callout("bad", "Impossible de charger les données", erreur or "Erreur inconnue.")
        return

    if page == "Synthèse":
        page_synthese(df)
    elif page == "Tableau de bord":
        page_dashboard(df)
    elif page == "Analyse temporelle":
        page_temporelle(df)
    elif page == "Prévisions":
        page_previsions(df)
    elif page == "Comparaison des modèles":
        page_modeles()
    elif page == "Analyse spatiale":
        page_spatiale(df)
    elif page == "Rapport":
        page_rapport(df)
    else:
        page_guide(df)


if __name__ == "__main__":
    main()