"""RCS-52 — Vue des mesures et anomalies (Streamlit).

    streamlit run src/rcs/ui/dashboard.py
Prérequis : `python scripts/demo_pipeline.py` (remplit data/rcs_poc.sqlite). Chaque graphique affiche sa source
(lot d'import, empreinte SHA-256, licence) pour que la visualisation reste traçable.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

from contextlib import closing
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
DB = Path(os.environ.get("RCS_DB", ROOT / "data" / "rcs_poc.sqlite"))
MEASURES = {"air_temp_k": "Température air [K]", "process_temp_k": "Température process [K]",
            "rpm": "Vitesse [tr/min]", "torque_nm": "Couple [N·m]", "tool_wear_min": "Usure outil [min]"}

st.set_page_config(page_title="RoboCare Sentinel — mesures & anomalies", layout="wide")
st.title("Mesures et anomalies")
st.caption("POC académique — données AI4I synthétiques NON médicales ; aucune action sur un équipement réel.")

if not DB.exists():
    st.error(f"Base absente ({DB}). Lancer d'abord : python scripts/demo_pipeline.py")
    st.stop()

def q(sql, *params):
    with closing(sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)) as con:
        return pd.read_sql_query(sql, con, params=params)

eq = q("SELECT id, type, criticite FROM equipement ORDER BY id")
equip = st.sidebar.selectbox("Équipement", eq["id"])
mesure = st.sidebar.selectbox("Mesure", list(MEASURES), format_func=MEASURES.get)
n = st.sidebar.slider("Nombre d'observations", 100, 3000, 500, step=100)

versions = q("SELECT DISTINCT a.model_version FROM analyse_modele a JOIN observation o ON o.id=a.observation_id WHERE o.equipement_id=? ORDER BY a.model_version", equip)["model_version"].tolist()
version = st.sidebar.selectbox("Version du modèle", versions) if versions else None
obs = q("""SELECT CAST(o.cle_source AS INTEGER) AS udi, o.*, l.fichier, l.sha256, l.importe_le,
                  s.nom AS source, s.licence, a.score, a.seuil, a.model_version, al.id AS alerte_id, al.statut
           FROM observation o
           JOIN lot_import l ON l.id = o.lot_id JOIN source_donnees s ON s.id = l.source_id
           LEFT JOIN analyse_modele a ON a.observation_id = o.id AND a.model_version = ?
           LEFT JOIN alerte al ON al.analyse_id = a.id
           WHERE o.equipement_id = ? ORDER BY udi, o.id LIMIT ?""", version, equip, n)
assert obs["id"].is_unique, "Une observation doit apparaître une seule fois"

# --- qualité des données
lot = q("SELECT * FROM lot_import ORDER BY id DESC LIMIT 1")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Observations affichées", len(obs))
c2.metric("Lignes rejetées (dernier lot)", int(lot["nb_rejetees"].iloc[0]) if len(lot) else 0)
c3.metric("Doublons (dernier lot)", int(lot["nb_doublons"].iloc[0]) if len(lot) else 0)
c4.metric("Alertes à qualifier", int((obs["statut"] == "a_qualifier").sum()))

st.subheader(f"{MEASURES[mesure]} — {equip}")
st.line_chart(obs.set_index("udi")[[mesure]])
st.caption("Axe x = identifiant source (UDI) : l'ordre AI4I n'est pas une vraie chronologie.")

scored = obs.dropna(subset=["score"])
if len(scored):
    st.subheader("Score d'anomalie et seuil")
    st.line_chart(scored.set_index("udi")[["score", "seuil"]])
    st.caption(f"Modèle : {scored['model_version'].iloc[0]} — seuil = quantile 95 % des normaux de validation.")
else:
    st.info("Aucun score pour cet équipement : lancer scripts/demo_pipeline.py --limit 2000.")

st.subheader("Anomalies détectées (traçabilité)")
st.caption("Le label AI4I Machine failure est une vérité terrain synthétique du dataset, pas une mesure ni une information disponible en temps réel.")
anom = obs[obs["alerte_id"].notna()][["udi", "model_version", "score", "seuil", "statut", "label", "fichier", "sha256", "source", "licence"]]
st.dataframe(anom, use_container_width=True)

with st.expander("Provenance des données"):
    st.write(q("SELECT * FROM source_donnees"))
    st.write(q("SELECT id, fichier, sha256, nb_lignes, nb_acceptees, nb_rejetees, nb_doublons, importe_le FROM lot_import"))
