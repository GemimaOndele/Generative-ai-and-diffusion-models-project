# DOC02 — Fiche source S04 : AI4I 2020 Predictive Maintenance Dataset (vérifiée 2026-11-20)
Organisme : UCI Machine Learning Repository. URL : https://archive.ics.uci.edu/dataset/601/ai4i. Licence : CC BY 4.0 (citation obligatoire).

Le jeu contient 10 000 observations synthétiques d'une fraiseuse industrielle, avec 14 colonnes : identifiants, type de qualité du produit (L, M, H), température de l'air, température du process, vitesse de rotation, couple et usure de l'outil. Environ 3,4 % des observations sont des pannes (« Machine failure » = 1).

Usage dans le projet : substitut méthodologique NON médical pour la baseline et la diffusion J1. Aucune validité hospitalière n'est revendiquée et l'ordre des lignes ne représente pas une vraie temporalité.

Mode TWF (usure de l'outil) : l'outil est remplacé ou casse à un temps d'usure tiré aléatoirement entre 200 et 240 minutes.

Mode HDF (dissipation thermique) : panne si l'écart entre température du process et température de l'air est inférieur à 8,6 K ET si la vitesse de rotation est inférieure à 1380 tr/min.

Mode PWF (puissance) : la puissance est le produit du couple et de la vitesse angulaire (rad/s) ; panne si la puissance est inférieure à 3500 W ou supérieure à 9000 W.

Mode OSF (surcontrainte) : panne si le produit usure de l'outil × couple dépasse 11 000 min·Nm pour un produit de qualité L, 12 000 min·Nm pour M et 13 000 min·Nm pour H.

Mode RNF (aléatoire) : chaque observation a une probabilité de 0,1 % de panne, indépendamment des paramètres.
