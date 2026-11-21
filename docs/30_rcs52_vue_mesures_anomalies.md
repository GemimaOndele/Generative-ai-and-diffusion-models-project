# RCS-52 — Vue des mesures et anomalies

Pilote : Omar · binôme : Gémima · relectrice : Aminata. Code : `src/rcs/ui/dashboard.py` (Streamlit).

```bash
pip install -r requirements-rcs52.txt
python scripts/download_ai4i.py
python scripts/demo_pipeline.py --limit 2000      # import idempotent -> scores -> alertes -> décision -> audit
streamlit run src/rcs/ui/dashboard.py
```

| Élément de la vue | Contenu | Traçabilité |
|---|---|---|
| Indicateurs | observations affichées, lignes rejetées, doublons, alertes à qualifier | dernier `lot_import` |
| Courbe de mesure | température air/process, vitesse, couple, usure par équipement | axe = UDI source (l'ordre AI4I n'est pas une chronologie) |
| Score et seuil | score d'anomalie vs seuil (quantile 95 % des normaux de validation) | `analyse_modele.model_version` |
| Anomalies | alertes avec statut, label, **fichier, SHA-256, source, licence** | jointure `observation → lot_import → source_donnees` |
| Provenance | tables `source_donnees` et `lot_import` | — |

Exécution réelle (2026-11-20) : 2 000 observations scorées par la baseline z-score « physics », **209 alertes**, une
alerte validée → intervention, une rejetée, toutes auditées. Test automatisé : `tests/test_rcs52_dashboard.py`
(exécute la démo puis la vue avec `streamlit.testing`; ignoré si AI4I n'est pas téléchargé).

Limites : données synthétiques **non médicales** ; profil utilisateur simulé ; la vue lit la base, elle n'envoie
aucune commande à un équipement. Le score de démonstration est la baseline ; le DDPM (RCS-71) peut s'y brancher.
