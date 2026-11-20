# TP05 — FinOps, Green AI & Éthique · RoboCare Sentinel (ECE, 20/11/2026)

> **Statut : protocole prêt / résultats ND (non disponibles).** Le TP05 dure **90 minutes**, complète **le jalon J2 Multi-LLM** et ne crée ni nouveau POC ni troisième jalon. Le jalon J1 diffusion est inchangé. Source normative : PDF enseignant « TP05 / FinOps, Green AI & Éthique », 4 pages, 20/11/2026. Jira : RCS-81 à RCS-86.

## 1 — Périmètre commun et preuve d'entrée (00–10 min) · RCS-81

- Baseline **mono-A** (et mono-B si testée) vs **V2 TP04** (routing / cascade, à justifier).
- Mêmes **10 cas gelés TP04**, notamment cas difficiles T07–T10 ; ne pas inventer les réponses ni remplacer les cas difficiles.
- **Unité fonctionnelle proposée, à valider :** une demande documentaire de maintenance correctement traitée, avec citation valide ou abstention/refus lorsque requis. Aucun choix de maintenance réel pris par l'IA.
- Qualité : nombre de tâches réussies selon grille fixée avant évaluation ; fidélité aux citations évaluée séparément ; p95 sur le même environnement.
- Périmètre réel TP04 actuel : **à confirmer à l'exécution** ; ne pas présenter les brouillons ou mocks comme des exécutions de LLM.

| Élément | Baseline mono | V2 TP04 | Source/preuve |
|---|---|---|---|
| Modèles, versions, fournisseur | ND | ND | ID exact et config |
| Cas communs / succès | ND | ND | tests gelés + grille |
| Appels, retries, tokens entrée/sortie | ND | ND | traces propres |
| p95 / échecs | ND | ND | logs horodatés |
| Données et licences autorisées | À confirmer | À confirmer | data/manifest.md |

## 2 — FinOps (10–35 min) · RCS-82

**Coût API (€) = somme [(tokens en / 1 000 000 × tarif en) + (tokens sortants / 1 000 000 × tarif sortant)].**

**Coût total sur l'échantillon** = coûts variables + coûts fixes/alloués **non déjà inclus** dans le prix API (p. ex. stockage, contrôle humain si effectivement quantifié), évitant tout double comptage.

**Coût par tâche réussie (€)** = coût total / nombre de tâches réussies **si le dénominateur est strictement positif**. Sinon **ND** (et non 0 €).

**Projection mensuelle** = coûts fixes mensuels + volume mensuel supposé × coût variable par tâche ; indiquer que cette projection est une **hypothèse**.

| Indicateur | Mono | V2 | Source/date/devise | Statut |
|---|---|---|---|---|
| Nombre de cas / succès | ND | ND | À vérifier | ND |
| Appels / retries | ND | ND | Traces | ND |
| Tokens entrée/sortie | ND | ND | Comptage fournisseur | ND |
| Coût variable € | ND | ND | Modèle/version/tarif URL | ND |
| Coût fixe ou alloué € | ND | ND | Hypothèses sourcées | ND |
| Coût par succès € | ND | ND | Formule ci-dessus | ND |
| p95 / échecs | ND | ND | Logs | ND |

**Levier proposé à tester** : limiter les tokens de contexte ou modifier la cascade **sans diminuer la qualité sur T07–T10**. Optimisation non testée = **gain hypothétique**, jamais gain constaté.

## 3 — Green AI (35–55 min) · RCS-83, RCS-63 et RCS-86

**Même unité fonctionnelle, mêmes cas, qualité et p95.**

| Frontière | Observabilité admissible | Ce qui ne peut être revendiqué |
|---|---|---|
| **Calcul Python local** (CPU/RAM/GPU selon disponibilité) | CodeCarbon : puissance/énergie observées ou estimées selon le matériel, équivalent CO₂ estimé | Énergie exacte de la seule tâche si GPU partagé ; émissions cycle de vie |
| **LLM via API distante** | Durée, tokens, appels, retries, facturation si connue | CodeCarbon local **ne mesure pas l'énergie du serveur distant** |
| **Hybride** | Séparer énergie locale et API distante non observée | Ne pas confondre empreinte partielle et totale |

CodeCarbon : https://docs.codecarbon.io/latest/ (documentation officielle). L'intégration Python **facultative**, destinée au matériel local, est proposée dans `src/observability/codecarbon_local.py`. Installer localement `pip install codecarbon`, lancer un véritable calcul autorisé et conserver la sortie brute **hors Git**. Les métadonnées de localisation et de matériel peuvent nécessiter une revue de confidentialité avant partage.

**Formule d'estimation simplifiée seulement si les données le permettent** : `CO2e_kg ≈ énergie_IT_kWh × PUE × intensité_carbone_kg_par_kWh`. **Ne pas réappliquer un PUE déjà inclus dans le chiffre d'énergie/CO₂e CodeCarbon.** Indiquer la source/lieu/date de l'intensité carbone, statut mesuré / calculé / estimé / ND et incertitudes.

**Distinction essentielle :** une facture en € ou un nombre de tokens ne fournit pas une mesure d'énergie. L'énergie locale CodeCarbon peut reposer sur des modèles d'estimation ; les serveurs des LLM distants ne sont pas instrumentés par cet outil. Ne pas mettre artificiellement 0 kWh lorsque la valeur est inconnue.

**Monitoring applicatif futur (RCS-86) :** voir `docs/09_codecarbon_monitoring.md`, KPI par run/modèle/version/stratégie, provenance et statut des données ; ne pas confondre métriques d'utilisation et données cliniques.

## 4 — Éthique (55–75 min) · RCS-84 / RCS-66

| Risque (personnes touchées) | Test/preuve prévu | Mesure de réduction | Responsable | Résultat |
|---|---|---|---|---|
| **Hallucination ou citation absente** (technicien, sécurité du service) | T07 source absente : tester abstention et absence de manuel inventé | Validation des sources, refus contrôlé, supervision humaine | Aminata / Elias | ND |
| **Injection indirecte de document** (technicien, équipe sécurité) | T09 : contenu source contenant ordre hostile ; vérifier qu'il n'est pas exécuté | Séparer sources non fiables des instructions, refus, journal nettoyé | Elias / Ayoub | ND |
| **Données patient et droits** (patients, établissement) | T10 : demande d'identifiant nominatif ; vérifier refus et non-divulgation | Contrôle d'accès, minimisation, absence de données patients dans le dépôt | Aminata / Gémima | ND |
| **Décision de maintenance autonome** (technicien, personnes concernées) | T02 : alerte sans validation humaine ; vérifier non-exécution d'action | Permissions, revue par technicien habilité, pas de commande machine | Ayoub / Gémima | ND |

Au moins **un test réel** de la séance doit avoir une trace et un résultat **PASS/FAIL/ND**. Ici ND signifie **non exécuté / non disponible à la rédaction**, pas PASS. Un audit technique ne constitue **pas** une preuve de conformité RGPD/AI Act ; le cadre d'usage et la vérification juridique restent à documenter.

## 5 — Synthèse (75–90 min) · RCS-85

| Question | Réponse actuelle (non exécutoire) |
|---|---|
| Coût par tâche réussie et source ? | ND : exécution et tarif source manquants |
| Empreinte Green : mesurée / estimée / ND ? | ND ; instrumentation CodeCarbon locale préparée seulement |
| Principal risque résiduel ? | À apprécier après tests sur hallucination/injection/données sensibles |
| GO / NO-GO / À TESTER ? | **À TESTER** : aucune comparaison TP04 ni audit TP05 mesuré n'est validé par la présente préparation |

### Livrables et preuve de contribution
- `docs/06_tp05_finops_green_ethique.md` : présent document, à compléter avec **preuves réelles** ;
- `experiments/results/tp05_mesures.csv` : schéma **sans valeurs chiffrées fictives** ;
- `docs/09_codecarbon_monitoring.md` et `src/observability/codecarbon_local.py` : instrumentation expérimentale locale opt-in ;
- `README.md` : liens et limites ;
- `docs/05_tp04_benchmark.md` : le TP05 le **complète** (une fois la PR #1 fusionnée).

**Ne pas démarrer le Sprint et ne pas cocher Done sur une tâche de recherche simplement parce que le document gabarit est prêt.**

## Attribution proposée (à confirmer par les cinq membres)
| Jira | Pilote | Binôme |
|---|---|---|
| RCS-81 périmètre | Gémima | Aminata |
| RCS-82 FinOps | Omar | Elias |
| RCS-83 Green AI / CodeCarbon | Ayoub | Omar |
| RCS-84 Éthique | Aminata | Gémima |
| RCS-85 Synthèse | Elias | Aminata |
| RCS-86 Monitoring applicatif | Ayoub | Gémima |

## Références
1. ECE Paris, « TP05 FinOps, Green AI & Éthique », 20/11/2026, pp. 1–4.
2. CodeCarbon, documentation officielle : https://docs.codecarbon.io/latest/.
3. CodeCarbon, Output Formats : https://docs.codecarbon.io/latest/reference/output/.
4. CodeCarbon, tracking mode : https://docs.codecarbon.io/latest/how-to/configuration/.
5. FinOps Foundation, AI FinOps : https://www.finops.org/wg/finops-for-ai-overview/.
6. Green Software Foundation SCI-AI : https://greensoftware.foundation/standards/sci-ai/.
7. CNIL : https://www.cnil.fr/fr/les-fiches-pratiques-ia.

## Articulation au suivi transversal (20/11/2026)
Le TP05 ne remplace pas la surveillance du budget du **premier jour au dernier** : RCS-90 regroupe dépense monétaire, temps des membres, infrastructure, coûts de supervision et hypothèses de valorisation humaine ; RCS-82 utilise un sous-ensemble observé pour calculer le coût par tâche réussie. Les versions modèles/datasets/prompt et hashes suivis par RCS-87 sont indispensables pour une comparaison financière et énergétique équitable. Le registre des risques RCS-18 et le protocole de biais RCS-88 s'appliquent aux seuils et changements de version ; RCS-89 définit la traçabilité du monitoring. Détails préparés dans la PR #4 (non fusionnée).
