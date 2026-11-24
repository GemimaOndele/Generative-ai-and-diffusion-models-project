# RCS-25 — Fiches comparées AI4I 2020 et MIMII DUE

Pages officielles consultées le **2026-11-20**. Pilote : Omar · binôme : Ayoub · relecteur : Elias.

| Critère | AI4I 2020 (UCI) [S04] | MIMII DUE (Zenodo/Hitachi) [S05] |
|---|---|---|
| URL | https://archive.ics.uci.edu/dataset/601/ai4i (DOI 10.24432/C5HS5C) | https://zenodo.org/records/4740355 (DOI 10.5281/zenodo.4740355) |
| Licence | **CC BY 4.0** (usage et redistribution avec citation) | **CC BY-NC-SA 4.0** (non commercial, partage à l'identique) |
| Nature | tabulaire **synthétique** (fraiseuse) : type L/M/H, T° air, T° process, vitesse, couple, usure | **sons réels** de machines industrielles : ventilateurs, réducteurs, pompes, rails, vannes ; 6 « sections » par type, domaines source/cible (vitesse, bruit) |
| Volume | 10 000 lignes, ~0,5 Mo | ~9,4 Go (zips par type) |
| Étiquettes | `Machine failure` + 5 modes (TWF 120, HDF 115, PWF 95, OSF 98, RNF 5 — un échantillon peut en cumuler plusieurs) ; pannes **générées par des règles** connues | normal / anormal par clip (tâche DCASE 2021 T2) |
| Format | CSV | audio en zip (fréquence/durée/canaux : voir arXiv 2105.02702, non vérifié ici) |
| Usage RCS | **retenu** pour J1 (baseline + DDPM, docs/32_rcs71_baseline_vs_diffusion.md) : léger, licence permissive, labels par mode | option J1 « acoustique » si un capteur audio est envisagé ; coût GPU/stockage élevé |
| Écart vs machine médicale réelle | pas de temporalité vraie, physique simplifiée, pannes déterministes → **risque de circularité** (une règle retrouve la règle) | machines non médicales, contexte industriel ; pas de journaux de maintenance |
| Citation | S. Matzka, *Explainable AI for Predictive Maintenance Applications*, AI4I 2020 | R. Tanabe et al., *MIMII DUE…*, arXiv:2105.02702, 2021 |

**Conclusion** : les deux sont des **substituts méthodologiques non médicaux** ; aucun ne valide une performance sur
scanner/IRM. AI4I est utilisé comme proxy exploratoire du POC (GO proposé, RCS-45 ; accord collectif non attesté) ; MIMII DUE reste en réserve.


Chiffres et licences issus de la fiche datée du 20/11, à revérifier avant acquisition ou redistribution. Pour MIMII DUE, vérifier les conditions NC/SA pour l'usage envisagé ; aucun droit commercial présumé. Données brutes hors Git, manifeste et empreinte obligatoires. Pas de choix de famille médicale par cette étude.
