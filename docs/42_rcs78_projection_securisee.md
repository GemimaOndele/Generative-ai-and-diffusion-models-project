# RCS-78 — projection de benchmark vers le contrat RCS-89

Pilote : Gémima. Contribution distincte ; contrat RCS-89 d’Ayoub inchangé.
Cette PR est empilée sur la PR #29, pas directement intégrable dans main.
La PR #27 conserve son rôle d’audit agrégé ; ce complément produit des événements stricts.

## Fonctionnement et limites

`tools/rcs78_trace_projection.py` projette des métadonnées JSONL dans
`data/contracts/trace_event_v1.json`, validé avec JSON Schema Draft 2020-12.
La sortie contient uniquement les propriétés explicites du contrat fermé.
Aucun prompt, réponse, question, catégorie métier, justification de score,
exception brute, champ patient, secret ou attribut source supplémentaire ne peut
être recopié. Les valeurs `model_version` sont des alias de registre contrôlés,
reliés aux identités/version exactes par le contexte revu. Ce contexte ne doit
jamais contenir d’identité patient ni de secret, même sous forme d’alias.

- Le SHA-256 lie le contexte aux octets exacts du JSONL consommé.
- `trace_id` est une empreinte de l’identité source et de la provenance ; `run_id`
  est un identifiant dérivé du fichier. Ce sont des corrélations techniques,
  pas un mécanisme d’anonymisation de données patient autorisant leur collecte.
- `timestamp_utc` représente **l’émission de la projection**, pas l’heure historique
  d’inférence : le fichier source examiné ne fournit pas cette heure.
- `cost_eur` conserve une valeur numérique valide ou `null` (ND). Un zéro reste
  distinct de ND. Ce champ ne valide ni la facture ni le coût complet du projet.
- L’énergie par événement reste `null` / `ND`. Aucune mesure par run n’est divisée
  artificiellement entre les traces. La frontière est fournie par contexte revu.
- Aucun fallback n’est déduit d’une cascade, d’un statut `ok`, d’un refus ou d’un
  modèle absent. Un booléen explicite par trace est obligatoire dans le contexte ;
  une contradiction avec un champ source explicite bloque tout l’export.
- Modèle sans appel : `models=[]` produit `model_version="none"` (aucun modèle
  exécuté dans cet événement). Un modèle non enregistré est refusé.
- Doublons d’identités/clefs JSON, champs requis absents, NaN/Inf/booléens dans les
  métriques et statuts inconnus bloquent l’export. Les codes d’erreur sont fixes.
- L’écriture est atomique après validation de tout le lot. Un échec conserve
  l’ancien fichier de sortie ; ce fichier n’est donc pas la preuve d’un nouvel
  export réussi. Consommer le code de retour et le résultat de la commande.

## Exécution

```bash
python -m pip install -r requirements-rcs78-projection.txt
python -m unittest discover -s tests -p test_rcs78_trace_projection.py -v
python -m tools.rcs78_trace_projection --input /chemin/hors-git/traces.jsonl --context /chemin/hors-git/contexte.json --output /chemin/hors-git/events.jsonl
```

Le contexte JSON doit contenir exactement ces propriétés :

```json
{
  "source_sha256": "SHA256_DES_OCTETS_ENTREE",
  "boundary": "local_compute",
  "model_registry": {"identite-exacte-modele@revision": "alias-version-revue"},
  "fallback_by_trace": {"identite-source-trace": false}
}
```

Exemple de forme uniquement : le booléen ci-dessus n’est pas une preuve réelle.
Un relecteur doit renseigner les fallbacks depuis le code et les traces d’origine,
les versions depuis les manifests et la frontière depuis le protocole. Code 0 :
`PROJECTED_NOT_APPROVED`. Code 2 : `BLOCKED` et motif fixe. Les journaux et le contexte
réels restent hors Git et ne doivent pas être publiés comme artifacts de CI.

## Vérification du 24 novembre 2026

Windows / Python 3.12 : 18 nouveaux tests de projection et les 5 tests existants
du contrat RCS-89 réussissent (23/23). Le contrat et les tests d’Ayoub sont
utilisés sans modification. CI dédiée prévue sur Windows et Ubuntu.

La forme du fichier RCS-77 `experiments/results/tp04_local_traces.jsonl`
(blob GitHub `492b853891da93b7d2357aa66f12b060f34b17cf`) a été inspectée :
90 lignes, aucune propriété `fallback_triggered` ni heure d’inférence.
Une copie locale réduite aux seuls champs techniques nécessaires, sans réponses
ni questions, a été soumise au projecteur. Résultat effectif :
`BLOCKED / missing_fallback_evidence`, aucun fichier d’événements créé.
Cette copie a son propre SHA-256 : ce test n’est pas une exécution du projecteur
sur les octets complets du fichier source. Aucun contexte de fallback n’a été
fabriqué pour obtenir un export. Aucun LLM n’a été exécuté.

## Revue à obtenir

Ayoub : conformité RCS-89 et distinction heure d’émission / heure d’inférence.
Omar : provenance RCS-77, modèles exacts et preuve de fallback par trace.
Elias : identité/version des modèles et protocole RCS-81.
Aminata : interprétation métier ; aucune validation de succès clinique implicite.

L’outil ne lance aucun LLM, ne valide aucun seuil opérationnel de RCS-89 et ne
remplace ni l’évaluation humaine ni les mesures de coûts complets RCS-90.
