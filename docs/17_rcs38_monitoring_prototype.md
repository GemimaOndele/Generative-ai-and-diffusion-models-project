# RCS-38 — Quatre volets de monitoring : premier prototype web exécutable

**Référente : Gémima. Binôme : Aminata. Relais : Ayoub. Relecteur : Omar.**  
**Statut : prototype navigable, non validé fonctionnellement, sans données réelles ni connexion au SI biomédical.**

## Prototype à ouvrir dans Cursor
Après récupération de la branche `feature/RCS-38-monitoring-quatre-vues` :

```bash
python -m http.server 8000
```

Ouvrir `http://localhost:8000/frontend/monitoring/`. Cliquer les **quatre volets**, puis filtrer les sites **A/B**. Le fichier `frontend/monitoring/demo.json` contient uniquement des fixtures fictives et l'UI affiche en permanence le bandeau « démonstration ». Aucun framework nécessaire.

## Spécification de chacun des quatre volets
| Vue | Contenu cible | Prototype effectivement livré | Critères métier restant à valider |
|---|---|---|---|
| Parc équipements | identifiant, site, famille, état, disponibilité | Inventaire fictif filtrable, état déclaré | Choisir famille pilote, catalogue autorisé, droits, seuil disponibilité |
| Données & anomalies | qualité capteurs, anomalies, FP/FN, dérive | Valeurs fictives, qualité, alertes candidates ; métriques scientifiques ND | Sources, étiquettes, seuils et gestion anomalies de données (RCS-69) |
| Maintenance & interventions | alertes revues, intervention, validation technicien, historique | Tableau des interventions fictives et étapes du workflow | RBAC, trace d'approbation, formulaires réels et aucun ordre machine |
| Plateforme & Green AI | p95, coût par succès, versions modèle/données, énergie local/API, incidents | Exécutions fictives, versions, coût simulé et énergie distante ND | Instrumentation RCS-81/82/83/87/89/90, budget, couverture et provenance |

**Les chiffres du prototype sont fictifs et ne constituent pas des KPI réels.** La qualité et la latence p95 restent `ND` faute de tests gelés ; la CO₂e des API distantes reste `ND`. CodeCarbon local ne mesure pas le fournisseur distant.

## Tests
```bash
python -m unittest discover -s tests -p 'test_rcs38_monitoring.py' -v
python -m tools.rcs38_contract
node --check frontend/monitoring/app.js
```

Le contrôle automatique vérifie le nombre des vues, la cohérence des fixtures, la politique de `null` pour l'énergie distante, l'absence de clés/patients dans les champs, et la syntaxe JS. **Il ne remplace pas une revue UX ou un test de sécurité applicative réel.**

## Prochaines étapes avec les membres
- **Aminata (binôme)** : tester les quatre parcours, définir le lexique de métier, vérifier l'absence de décisions automatiques.
- **Omar (relecteur)** : contrôler KPI, champs, statuts et futures sources/qualité de données.
- **Ayoub (relais technique)** : intégrer le prototype dans l'architecture web quand la PR #1 sera fusionnée, préparer tests d'API et observabilité.
- **Gémima** : mettre en correspondance les écrans du cahier des charges V1.3, l'évolution RCS-86 et les décisions du groupe.

RCS-38 phase initialement indicative S2 : ce premier prototype ne signifie pas que l'intégration applicative et la validation d'écrans sont terminées. PR distincte ; ne pas fusionner avant la revue humaine.
