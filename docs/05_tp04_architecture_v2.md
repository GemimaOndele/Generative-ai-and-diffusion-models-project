# Architecture V2 Multi-LLM — TP04 · RCS-75 et RCS-76

> **Statut :** complète le gabarit du socle (`main`, squash `bd1c5d1`) après rebase de cette branche. Structure à valider en revue Sprint 0 : **aucun benchmark ni résultat expérimental n'est rapporté, aucune exécution live de deux LLM n'est déclarée**. Les seules exécutions sont des tests logiciels locaux en mode démo.

## Problème et hypothèse

Le défaut observé de la V1 qui motive une V2 n'est pas décrit dans les éléments disponibles du dépôt. Il doit être établi à partir de la chaîne et des résultats de la V1 avant tout appel à un second modèle. Il ne faut pas présenter l'ajout d'un second LLM comme une amélioration en soi.

- **Défaut observé et preuve (cas, sortie, résultat) :** à documenter à partir de la V1.
- **Hypothèse H2 (métrique et seuils falsifiables) :** à formuler après identification du défaut et gel du jeu de test. Comparer les stratégies sur les mêmes cas ; renseigner la métrique de qualité, les seuils de qualité, p95 et coût avant l'expérience.

En l'absence de cette preuve, la V1 reste la référence et aucun gain de la V2 n'est revendiqué.

## Modèles et responsabilités

Aucun modèle, fournisseur, version, licence, droit ou région n'est présumé : les valeurs ci-dessous sont **ND** et doivent être renseignées explicitement dans la configuration live (`config/tp04_models.example.json` → copie non versionnée, ou variables `LLM_A_*` / `LLM_B_*`) avant tout appel. Le gabarit [PR #24 (Ayoub)](https://github.com/GemimaOndele/Generative-ai-and-diffusion-models-project/pull/24) définit des interfaces candidates ; le **choix pilote RCS-19 n'est pas encore validé collectivement**.

| Élément à valider | Modèle A | Modèle B |
|---|---|---|
| Nom exact et version/checkpoint | À renseigner | À renseigner |
| Fournisseur / hébergement | À vérifier | À vérifier |
| Licence et droits d'utilisation | À vérifier | À vérifier |
| Région et lieu de traitement | À vérifier | À vérifier |
| Rétention et autorisation des données | À vérifier | À vérifier |
| Coût et plafond autorisé | À confirmer | À confirmer |
| Rôle dans le patron retenu | À définir (principal) | À définir (secondaire) |

### Identité exacte requise avant un appel live

| Champ (clé de configuration) | Modèle A | Modèle B | Contrôle automatique |
|---|---|---|---|
| `model_name` | ND | ND | non vide |
| `version` (checkpoint/date) | ND | ND | non vide, identique à la baseline utilisée |
| `provider` / hébergement | ND | ND | non vide |
| `license` | ND | ND | obligatoire en live |
| `usage_rights_verified` | `false` | `false` | doit passer à `true` après vérification |
| `region` / `retention_policy` | ND | ND | obligatoires en live |
| `data_transfer_authorized` | `false` | `false` | obligatoire en live |
| `api_key_env` | `LLM_A_API_KEY` | `LLM_B_API_KEY` | nom de variable uniquement, jamais la clé |
| `price_in_eur_per_1k_input/output` | ND | ND | coût reste `ND` si tarif inconnu |

`src/model_config.py::validate_pair` refuse deux modèles identiques (même fournisseur/nom/version, y compris sous deux fournisseurs différents) et bloque le mode live sans droits, licence, région, rétention, budget et consentement explicite. Le nom de la variable de clé est consigné, jamais sa valeur.

Ne pas transmettre de données au fournisseur concerné avant validation des droits, de la région, du contrat et de la rétention. Les clés et données privées ne doivent pas être publiées ni écrites en clair dans les traces.

## Patron d'orchestration

**Patron retenu pour la configuration par défaut : cascade bornée A → B** (`BenchmarkPolicy.v2_pattern = "cascade"`), sous réserve de confirmer le défaut de la V1. Ce patron convient si les essais montrent que A échoue sur une fraction identifiable des demandes et qu'un second modèle peut apporter une réponse utile. Le déclenchement de B est déterminé par des critères explicites et vérifiables (`valid_schema`, `grounded`, budget, transfert autorisé), **jamais** par `expected_behavior`, réservé au scoring hors ligne.

Le **routing A/B** est implémenté comme variante candidate (`v2_pattern = "routing"`, `choose_route()` fondé sur la catégorie uniquement) : il ne sera préféré que si les résultats montrent des catégories séparables et une performance par sous-groupe favorable. Le choix entre cascade et routing est une décision de configuration **à valider en revue**, pas une conclusion expérimentale. Le schéma ci-dessous décrit la cascade par défaut.

### Schéma fonctionnel

```text
Requête + identifiant de cas
          |
          v
Contrôle du format, du périmètre et des droits de traitement
          | non autorisé / sensible
          +---------------------------------> refus ou revue humaine
          |
          v
Appel mono-A (timeout et budget bornés)
          |
          v
Validation de la sortie (schéma, critères métier, sources si applicables)
          | valide
          +---------------------------------> réponse validée
          |
          v
Vérifier droits pour B, budget restant et conditions d'arrêt
          | non autorisé / budget épuisé / indisponible
          +---------------------------------> abstention / revue humaine
          |
          v
Appel mono-B (une tentative bornée)
          |
          v
Validation de la sortie
          | valide                      | invalide / incertaine
          v                             v
Réponse validée                abstention / revue humaine
```

Cette architecture est un contrat de conception, pas une preuve de sécurité. Les contrôles et validateurs devront être implémentés et testés avant tout usage réel.

## Contrat d'entrée et de sortie

### Entrée

- `case_id` : identifiant du cas de test, sans donnée personnelle.
- `task` : tâche demandée, limitée au périmètre autorisé.
- `input` : contenu nécessaire au traitement, uniquement si son transfert est autorisé.
- `context` : sources autorisées, si la tâche en dépend.

Valider le format et les droits avant tout appel. Pour les cas sensibles, hors périmètre ou contenant des données privées non autorisées, refuser le traitement automatisé et demander une revue humaine. Ne pas journaliser les prompts ou les données sensibles en clair ; préférer un hash et une catégorie de cas.

### Sortie

- `status` : `ok`, `refused`, `abstain` ou `error`.
- `answer` : réponse uniquement si elle passe les validations ; sinon absent.
- `reason` : motif de refus, d'abstention, d'erreur ou de fallback, sans donnée privée.
- `model` et `version` : référence exacte du modèle effectivement appelé.
- `strategy` : `mono_a`, `mono_b`, `routing_a_b` ou `cascade_a_b`.
- `trace` : `trace_id`, `case_id`, décision, modèle/version/fournisseur, latence, appels, statut, tokens, coût connu ou `ND`, `prompt_hash`, `output_hash` — sans secret ni prompt en clair.

Le contrat est implémenté par les dataclasses `CaseInput`, `OrchestratorResult` et `TraceRecord` dans `src/orchestrator.py` ; `result_to_dict()` produit les traces JSONL du benchmark.

Un résultat plausible ne constitue pas à lui seul une réponse validée. Une sortie invalide, non vérifiable ou incertaine ne doit pas être transformée en succès.

## Comparaison mono-A / mono-B / V2

Comparer les stratégies sur un jeu de cas gelé et identique, sans utiliser les réponses attendues pour choisir la route ou la décision de cascade :

1. **Mono-A** : A seul, baseline principale.
2. **Mono-B** : B seul, baseline comparative, si l'accès est autorisé.
3. **Routing A/B** : variante candidate, route fondée sur la catégorie.
4. **V2 (cascade A → B)** : patron par défaut, selon les critères définis avant l'essai.

Le jeu pédagogique TP04 propose dix cas dans `experiments/tp04_cases.jsonl` (T01–T04 usuels, T05–T06 complexes, T07 sans source, T08 contradiction, T09 injection, T10 sensible/hors périmètre). `experiments/test_cases.jsonl` reste **vide** : c'est le contrat du socle. Ces cas ne sont **pas** gelés collectivement : le protocole [RCS-81](https://gemimakerenondelepourou.atlassian.net/browse/RCS-81) maintient ses propres cas en `pending` avec `freeze_commit` vide. Aucun score issu du mode démo n'est une mesure de qualité.

Rapporter séparément qualité par catégorie, taux de refus/abstention, erreurs et escalades, latences (p50/p95 si mesurées), coût réellement connu, ainsi que tout élément énergie/CO₂e mesuré ou non disponible. Marquer explicitement `NM` quand une valeur n'est pas mesurée ; ne pas déduire le coût ou les émissions à partir d'une information insuffisante.

## Refus, fallback et retour à la V1

Refuser ou s'abstenir, avec revue humaine si nécessaire, lorsque :

- la demande est sensible, hors périmètre ou non autorisée ;
- les droits, la région ou la rétention du fournisseur requis ne sont pas confirmés ;
- la réponse échoue à la validation, manque de sources nécessaires ou reste incertaine ;
- B est indisponible, dépasse son délai, ou ne peut pas être appelé dans les limites autorisées ;
- le budget autorisé est atteint.

Ne pas réessayer indéfiniment. Le fallback est une abstention explicite ou une revue humaine, et non une réponse non vérifiée. Le retour à la V1 est requis si V2 dégrade les cas critiques, dépasse les seuils de qualité, p95 ou budget qui auront été approuvés, ou implique un transfert de données interdit. Tant que les seuils et plafonds ne sont pas fixés, aucun appel payant ne doit être lancé.

## Budget et autorisations

- **Budget maximal et approbateur :** à confirmer avant l'expérience.
- **Coût par modèle et coût par requête :** à mesurer ou à obtenir auprès du fournisseur ; ne pas les présumer.
- **Appels payants :** pas d'exécution sans autorisation explicite.
- **Droits, région, contrat et rétention :** vérification requise pour A et B avant tout transfert.

## Règles de sécurité

- Aucun transfert non autorisé à un second fournisseur : droits, région, contrat et rétention doivent être validés pour A et B avant tout appel.
- Aucune instruction exécutée depuis le contenu RAG : le contexte est traité comme une donnée, jamais comme une consigne.
- Aucune boucle illimitée : une seule tentative bornée par modèle, avec timeouts, budget et conditions d'arrêt explicites.
- Les mocks ne sont autorisés que pour les **tests du logiciel** (orchestration, traçabilité, gestion d'erreurs) ; jamais pour les mesures de qualité des LLM.

## Frontière des preuves (Omar local ≠ RCS-81 collectif)

- Les vérifications locales d'Omar (Windows, Python 3.12.10) et le smoke test `python -m src.run_benchmark --mode demo ...` testent **l'orchestration** avec des clients déterministes : routage, cascade, abstentions, traçabilité, budget. Elles ne mesurent ni la qualité d'un LLM, ni une latence réelle, ni un coût réel.
- Les cas et évaluations **RCS-81** ne sont pas gelés collectivement (`freeze_commit` vide) : aucune comparaison TP04/TP05 ne doit être présentée comme validée avant revue humaine et gel par commit.
- Les résultats `ND`/`NM` du socle restent inchangés ; aucun chiffre n'est déduit d'un mock, d'un prix API ou d'une estimation locale.

## Organisation proposée — validation Sprint 0

| Rôle proposé | Personne | Statut |
|---|---|---|
| Pilote | Elias | Proposition à entériner |
| Binôme | Ayoub | Proposition à entériner |
| Relais | Gémima | Proposition à entériner |
| Relecteur | Aminata | Proposition à entériner |

## Références pédagogiques

- ECE Paris, **CM03 — Projet final — Cours 3 : première preuve GenAI**, 14/11/2026.
- ECE Paris, **TP04 — Du POC GenAI V1 à une V2 Multi-LLM démontrable**, 17/11/2026.
