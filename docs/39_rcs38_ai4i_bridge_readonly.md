# RCS-38 / RCS-49 / RCS-50 / RCS-52 — contrat d'intégration en lecture seule

**Statut : intégration finale en revue (#32).** Le socle SQL/CSV/stockage/dashboard et les tests croisés sont déjà fusionnés dans `main`. Elle n'écrase pas les modules d'Omar et ne modifie ni son schéma SQL ni sa vue Streamlit.

## Pourquoi deux catégories de démonstration distinctes ?

| RCS-38, démo fictive | Pipeline Omar AI4I, substitut industriel |
|---|---|
| `data_mode = fictional_demo_only` | `source_mode = industrial_proxy_non_medical` |
| Données et sites inventés ; aucune mesure réelle | Enregistrements AI4I industriels synthétiques avec `source_donnees`, `lot_import`, SHA-256 |
| `tools/rcs38_demo_server.py` (API local-only) | `src/rcs/db.py` + SQLite RCS-50 |
| Décisions simulées, validables **uniquement** en mode local fictif | **Aucune** décision exposée ; anomalies candidates à interprétation scientifique uniquement |
| UI web `frontend/monitoring` | UI Streamlit `src/rcs/ui/dashboard.py` |
| Sites fictifs A/B | `simulé` / étiquettes industrielles ; pas de site hospitalier |

**Interdiction** : transformer les données AI4I en `fictional_demo_only`, introduire des alertes AI4I dans l'API d'approbation fictive, ou prétendre détenir des équipements médicaux réels.

## Premier adaptateur livré

`tools/rcs38_ai4i_bridge.py` expose `preview_ai4i(path, limit=100)`. Il lit le fichier SQLite **en mode read-only**, filtre `source_donnees.id = S04` et les équipements fictifs `AI4I-*`, exige un marquage *NON médical*, puis produit un objet JSON-sérialisable. Champs explicites :

- `schema_version = rcs38-ai4i-readonly-v0.1`
- `source_mode = industrial_proxy_non_medical`, `medical_data = false`, `clinical_use = false`, `control_enabled = false`, `read_only = true`
- `equipment[]` (identifiant, type, site, criticité)
- `observations[]` (source_record_id AI4I **non temporel**, températures K, tr/min, Nm, min, score/seuil/version, indicateur `null` si non scoré)
- `provenance` (source S04, fichier, empreinte SHA-256, date import)
- `actions = []` (aucune suggestion d'action ni ordre à une machine)

L'adaptateur ne prend pas les labels de vérité terrain dans l'aperçu ; ils restent réservés à l'évaluation scientifique. Il exige que le schéma RCS-50 existe déjà. Il ne récupère aucune donnée externe et ne démarre aucun service réseau.

## Vérification sans données privées

Depuis la branche de cette PR :

```bash
python -m unittest discover -s tests -p 'test_rcs38_ai4i_bridge.py' -v
```

Tests sur mini-base synthétique construite et détruite en mémoire/disque temporaire : provenance, catégories, absence d'actions, valeurs ND, refus des sources non marquées, refus des équipements non fictifs, limites, absence de mutation.

Pour tester avec la base créée par le pipeline RCS-50/RCS-52 intégré (sans la committer), un script ou notebook local peut importer l'adaptateur et appeler :

```python
from tools.rcs38_ai4i_bridge import preview_ai4i
preview = preview_ai4i("data/rcs_poc.sqlite", limit=100)
assert preview["control_enabled"] is False
```

**Test croisé #23 intégré** (`072e32b9`) : les migrations réelles, l'import CSV, l'enregistrement de scores et le pont sont vérifiés sur deux lignes industrielles synthétiques. Les 24 workflows et 31 contrôles du commit d'intégration étaient verts. Cela ne constitue pas un rejeu du dataset complet. Le nouveau contrôle CI télécharge AI4I depuis UCI avec vérification SHA-256, exécute `scripts/demo_pipeline.py` sur une base temporaire, exporte le JSON puis vérifie la provenance, les scores et l'intégrité en lecture seule. Son résultat reste à constater sur le nouveau SHA ; aucune réussite n'est présumée. La revue manuelle UX d'Aminata reste requise.

## Suite après accord collectif

1. Omar : vérifier que les noms SQL de la branche RCS-50 sont stables (MCD/MLD RCS-41/42), ajouter son test de compatibilité de lecture.
2. Ayoub : définir une API de consultation **séparée** du mode fictif ; sécurité, rôles et stratégie de persistance.
3. Aminata : valider les messages UI « proxy industriel non médical », la compréhension des limites, et l'absence de actions cliniques.
4. Gémima : prévoir un onglet UI « expérimentation AI4I » identifié, distinct du parcours fictif RCS-38 ; pas de connexion à un appareil médical.
5. Elias : valider protocole seuils / labels / splits et versions de modèle, sans interprétation clinique.

**Ordre actuel :** #31 et #19 → #12 → #20 → #14 → #23 sont fusionnées. #32 cible `main` ; attendre le rejeu complet, la CI et la revue finale.

## Aperçu web local, strictement en lecture seule

Une page distincte `frontend/monitoring/ai4i_preview.html` est reliée depuis le monitoring fictif. **Ce n'est pas un cinquième module clinique** : le navigateur lit exclusivement un export JSON choisi localement via `<input type=file>` (pas d'upload ni de fetch). Le contrat refuse `data_mode=fictional_demo_only`, exige `source_mode=industrial_proxy_non_medical`, `medical_data=false`, `control_enabled=false`, `actions=[]`, une source S04 non médicale et un SHA-256 par observation.

Après génération de la base **sur une copie locale du pipeline RCS-52**, depuis la branche contenant l'adaptateur :

```bash
python -m tools.rcs38_ai4i_bridge --db data/rcs_poc.sqlite --out .local/rcs38_ai4i_preview.json --limit 100
```

Puis démarrer le serveur RCS-38 local comme d'habitude et ouvrir `http://127.0.0.1:8000/ai4i_preview.html`. Sélectionner le JSON local ; il reste sur le poste de démonstration. Le fichier de sortie est volontairement stocké sous `.local/` et **ne doit pas être ajouté au dépôt**. Le schéma industriel et l'adaptateur Python sont réunis dans `main` depuis #23. Le présent changement ajoute le rejeu complet du pipeline et l'aperçu web ; aucune validation UX manuelle n'est revendiquée.

**Portée de la preuve** : page d'affichage locale et pont de lecture. Ce n'est ni un serveur connecté au POC d'Omar en continu, ni un simulateur de décision hospitalière, ni une évaluation médicale. Ne pas importer de données d'hôpital réelles dans cette page.
