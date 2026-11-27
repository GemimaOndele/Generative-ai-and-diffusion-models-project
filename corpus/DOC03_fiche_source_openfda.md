# DOC03 — Fiches sources S01/S02 : openFDA MAUDE et rappels de dispositifs (vérifiée 2026-11-14)
URLs : https://open.fda.gov/apis/device/event/ et https://open.fda.gov/apis/device/recall/. Données publiques de la FDA américaine, au format JSON via API.

MAUDE contient des signalements textuels d'événements indésirables et de dysfonctionnements de dispositifs médicaux. Les rappels décrivent des défauts ayant conduit à un retrait ou une correction.

Limite majeure : ces données sont des textes de signalement, PAS de la télémétrie de capteurs. Elles ne contiennent pas de séries temporelles de mesures machine et ne permettent donc pas d'entraîner directement un modèle de diffusion de détection d'anomalies sur capteurs.

Les signalements sont volontaires ou réglementaires et incomplets : ils ne permettent pas de calculer un taux de panne. Certains champs textuels peuvent contenir des informations sensibles et doivent être filtrés.

Usage possible : typologie de dysfonctionnements et corpus documentaire pour l'assistant Multi-LLM J2. Quotas d'API à vérifier dans la documentation officielle avant toute collecte.
