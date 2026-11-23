# TP04 — Architecture V2 Multi-LLM · RCS-75 et RCS-76

**État : structure à remplir ; aucune exécution de deux LLM déclarée.**

## Problème et hypothèse
Défaut V1 (preuve) : ...
H2 (métrique et seuils falsifiables) : ...

## Modèles et responsabilités
| Modèle | ID et version | Fournisseur / hébergement | Licence / droits | Rôle |
|---|---|---|---|---|
| A | À définir | À vérifier | À vérifier | À définir |
| B | À définir | À vérifier | À vérifier | À définir |

## Patron d'orchestration
Choix et justification (routing, cascade, writer/reviewer, parallèle) : ...
Schéma, entrées/sorties, format attendu, validation, refus, escalade humaine, timeouts, budgets et fallback : ...

## Règles de sécurité
Pas de transfert non autorisé à un second fournisseur, pas d'instructions exécutées depuis le contenu RAG, pas de boucles illimitées. Mocks possibles pour **tests du logiciel**, jamais pour les mesures de qualité des LLM.
