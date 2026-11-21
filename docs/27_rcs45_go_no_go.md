# RCS-45 — Critères Go/No-Go avant développement (décision datée)

Date de la grille : **2026-11-20** · pilote : Omar · binôme : Elias · relecteur : Ayoub.
⚠ Le code du POC a été écrit en parallèle des TP03–TP05 (contrainte de calendrier des séances) : cette grille
**régularise** la décision et liste ce qui doit être validé par le groupe et le professeur pour que le Go soit complet.

| # | Critère | Preuve attendue | État au 2026-11-20 | Verdict |
|---|---|---|---|---|
| 1 | Cahier des charges : exigences prioritaires numérotées + tests d'acceptation | CDC v1 relu | trame CDC V2 non complétée ; FR-01…FR-16 candidates (Bibliothèque §6.4) | 🟡 à compléter |
| 2 | Dataset licite identifié, droits évalués | `docs/24_rcs40_dictionnaire_contrat_donnees.md`, `docs/22_rcs24_fiche_accessgudid.md et docs/23_rcs25_fiches_ai4i_mimii.md` | AI4I CC BY 4.0 (J1), corpus interne (J2) ; AccessGUDID/MIMII évalués | ✅ GO |
| 3 | Validité scientifique bornée | limites écrites | « substitut NON médical » affiché partout ; H1/H2 réfutables | ✅ GO |
| 4 | Ressources de calcul | mesure | CPU suffit : DDPM ≤ 1 min/seed, LLM ≤ 0,5 B en local ; pas de GPU requis | ✅ GO |
| 5 | Coût borné | estimation | 0 € d'API (local) ; énergie estimée < 2 Wh par passe de 10 cas (TP05) | ✅ GO |
| 6 | RGPD / données sensibles | registre + test | aucune donnée patient ; blocage PII testé (T10) ; AIPD non requise à ce stade | ✅ GO (revue référent à faire) |
| 7 | Architecture et modèle de données revus | schéma + MCD/MLD | `docs/03_architecture.md (dépôt omk181920/robocare-sentinel)`, `docs/25_rcs41_mcd.md et docs/26_rcs42_mld_sql.md` ; MCD JMerise à dessiner | 🟡 revue groupe |
| 8 | Conventions Jira/Git adoptées | vote | `docs/21_rcs16_conventions_jira.md`, `CONTRIBUTING.md` proposés | 🟡 vote |
| 9 | Avis du professeur sur le périmètre et le substitut AI4I | réponse écrite | fiche de prévalidation V2 prête, réponse non reçue | 🔴 en attente |

**Décision proposée** : **GO conditionnel** pour la poursuite technique (J1 diffusion et J2 Multi-LLM sur données
substituts), **NO-GO** pour toute collecte de données hospitalières ou connexion à un équipement réel tant que les
critères 1, 6 (revue) et 9 ne sont pas levés. Points à valider au prochain point de coordination : 1, 7, 8.
