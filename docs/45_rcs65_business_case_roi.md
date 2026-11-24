# RCS-65 — Business case ROI à trois scénarios

> Les valeurs livrées sont `ND` : aucune hypothèse financière n'est inventée et aucune projection n'est présentée comme une mesure. Décision automatique : **ND**, revue humaine obligatoire.

## Formules vérifiables

- `cout_variable_mensuel` = volume * cout_variable_par_tache
- `cout_total_mensuel` = couts_fixes_non_inclus_API + cout_variable_mensuel
- `cout_total_annuel` = mise_en_place + horizon * cout_total_mensuel
- `benefice_annuel_brut_valorise` = volume * horizon * delta_taux_reussite * (gain_minutes/60) * cout_horaire_hypothetique
- `gain_net_annuel` = benefice_annuel_brut_valorise - cout_total_annuel
- `roi` = gain_net_annuel / cout_total_annuel (ND si dénominateur nul)
- `payback_mois` = mise_en_place / (benefice_mensuel - cout_total_mensuel) (ND si net mensuel <= 0)

Règles : EUR uniquement (aucune conversion implicite), `ND` plutôt que zéro. Pas de double comptage des postes déjà inclus dans le tarif API.

## Hypothèses et résultats

| ID | Hypothèse | Pessimiste | Central | Optimiste | Statut/source |
|---|---|---|---|---|---|
| H-01 | volume tâches / mois | ND | ND | ND | ND / ND |
| H-02 | delta taux de réussite (fraction) | ND | ND | ND | ND / ND |
| H-03 | gain de temps / tâche réussie (minutes) | ND | ND | ND | ND / ND |
| H-04 | coût horaire valorisé (EUR/h, hypothétique) | ND | ND | ND | ND / ND |
| H-05 | coût variable / tâche (EUR, hors postes déjà inclus dans l'API) | ND | ND | ND | ND / ND |
| H-06 | coûts fixes mensuels non inclus dans le tarif API (EUR) | ND | ND | ND | ND / ND |
| H-07 | mise en place initiale (EUR) | ND | ND | ND | ND / ND |
| H-08 | horizon (mois) | ND | ND | ND | ND / ND |
| H-09 | confirmation absence de double comptage API/infrastructure | ND | ND | ND | ND / ND |

| Résultat | Pessimiste | Central | Optimiste |
|---|---|---|---|
| cout_variable_mensuel_eur | ND | ND | ND |
| cout_total_mensuel_eur | ND | ND | ND |
| cout_total_annuel_eur | ND | ND | ND |
| benefice_annuel_brut_valorise_eur | ND | ND | ND |
| gain_net_annuel_eur | ND | ND | ND |
| roi | ND | ND | ND |
| payback_mois | ND | ND | ND |

## Limites et décision

- Hypothèses toutes ND : volume, taux de réussite, tarifs et effort restent à sourcer.
- Tant que les scénarios ne sont pas sourcés et relus, aucune projection n'est une mesure.
- Le temps étudiant est une valorisation hypothétique, pas une dépense facturée.
- Le double comptage infrastructure/tarif API doit être explicitement écarté.
- Décision automatique : **ND** ; relecteur : ND.

## Reproduction

```bash
python -m tools.rcs65_business_case --write
python -m tools.rcs65_business_case --check
python -m tools.rcs65_business_case --assumptions <fichier.json> --write
python -m unittest tests.test_rcs65_business_case -v
```

Lien avec RCS-90 (`tools/rcs90_finops.py`, coûts complets), RCS-82 (`experiments/results/tp05_mesures.csv`, coût par tâche réussie) et ADR-002 (ne pas publier d'estimation comme mesure).
