# DOC07 — Note technique seuil d'alerte, version 2 (2026-11-18) — EN VIGUEUR
Décision ADR-003 : le seuil d'alerte est fixé au quantile 95 % des scores des observations normales de validation, soit un taux cible de fausses alertes de 5 %.

Justification : avec le quantile 99 %, le rappel des pannes sur validation était jugé trop faible. Cette version remplace la note DOC06 (quantile 99 %). Le seuil n'est jamais calculé sur le jeu de test.
