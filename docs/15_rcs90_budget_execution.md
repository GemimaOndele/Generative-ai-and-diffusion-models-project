# RCS-90 — Budget complet et temps humain : premier livrable exécutable

**Responsable proposé : Gémima · binôme Omar · relectrice Aminata · relais Elias.**  
**Statut : calculateur + tests prêts à relire.** Les registres sont VIDES, sans dépenses ni heures fictives. Ceci ne clôt pas RCS-90 et ne prouve pas le ROI.

## Périmètre des coûts

- **Trésorerie réelle :** factures API, GPU/cloud, stockage, licences et services réellement payés (avec preuve, date et fournisseur).
- **Prévision :** enveloppes futures estimées, **jamais ajoutées** à la trésorerie réelle.
- **Temps :** heures de conception, coordination, expérimentation, tests, revue et supervision enregistrées séparément.
- **Valorisation humaine hypothétique :** heures multipliées par un taux *documenté comme hypothèse* ; ce n'est pas une facture, ne pas additionner automatiquement aux dépenses.
- **Double comptage :** une infrastructure déjà comprise dans le prix API est marquée `included_in_api=yes` et exclue du total.

Le coût complet d'une tâche réussie n'est comparable entre mono-A et V2 que si : même workload gelé, mêmes règles de réussite, coûts documentés/alloués au même périmètre, et nombre de succès connu. Le script produit **seulement un coût observé partiel** avec avertissement de couverture.

## Exécution locale dans Cursor, VS Code ou terminal

Après avoir récupéré la branche `feature/RCS-90-suivi-couts-complets` :

```bash
python -m unittest discover -s tests -p "test_rcs90_finops.py" -v
python -m tools.rcs90_finops --costs planning/rcs90_costs.csv --worklogs planning/rcs90_worklogs.csv
```

L'exécution sur les CSV vierges doit afficher `null` pour les montants et le temps non renseignés. C'est un **test de fonctionnement**, pas un chiffrage.

Après collecte réelle, utiliser des copies locales contrôlées des CSV et éventuellement :

```bash
python -m tools.rcs90_finops --costs planning/rcs90_costs.csv --worklogs planning/rcs90_worklogs.csv --successes 7 --success-source experiments/results/VALIDATED-RUN.csv
```

**Le nombre 7 est un exemple de commande et ne doit jamais être lancé comme résultat de RoboCare tant qu'il n'existe pas une vraie preuve.** Aucune donnée privée/secret ne doit être poussée sur le dépôt public. Si des montants sont confidentiels, utiliser uniquement des agrégats autorisés et stocker les factures hors GitHub.

## Structure des registres

`planning/rcs90_costs.csv` (vierge) : `entry_id,jira_ticket,category,cost_class,status,amount_eur,currency,included_in_api,source_ref,notes`.

`planning/rcs90_worklogs.csv` (vierge) : `entry_id,jira_ticket,member,activity,status,hours,hypothetical_hourly_rate_eur,rate_source,notes`.

La bibliothèque V3.6 et le CDC V1.3 décrivent la gouvernance globale ; la PR #4 contient des registres de référence complémentaires. **Avant fusion**, aligner si nécessaire les champs des deux schémas pour éviter la duplication documentaire.

## À valider avec le groupe
1. Unité d'analyse et périodes, tâches J1/J2 et mode de répartition des coûts fixes.
2. Conditions d'accès aux factures/tarifs et confidentialité du temps humain.
3. Collecte minimale du budget avant chaque Sprint et revue après chaque Sprint.
4. Validation par Omar du calcul, Aminata de la lisibilité des hypothèses et de la cohérence métier.
5. Mesures réelles (encore manquantes), trois scénarios ROI et décision GO/NO-GO seulement après preuves.

**Sources de départ :** TP05 ECE (20/11/2026) ; rappel professeur versionnement/coût du cycle de vie ; tickets RCS-65, RCS-82, RCS-90.
