# Paramètres du dépôt GitHub — configuration à appliquer

**État contrôlé le 21 novembre 2026 :** le dépôt public avait une ancienne description générique sur les modèles de diffusion, **aucun topic**, **aucune Homepage** et **GitHub Pages initialement désactivé ; `has_pages=true` après la création de `gh-pages`, source et adresse publique non vérifiées**.

Les valeurs suivantes sont préparées pour les paramètres **About**. Elles ne sont **pas encore enregistrées dans les Settings**, car la connexion GitHub actuelle ne propose pas de mutation administrative du dépôt.

## Proposition pour « About »

**Description (copier exactement) :**
> RoboCare Sentinel · Plateforme de recherche IA d'assistance à la maintenance biomédicale | Diffusion, Multi-LLM, RAG, FinOps & Green AI.

**Website :** laisser vide jusqu'à publication effective de GitHub Pages. URL future attendue, à vérifier :
`https://gemimaondele.github.io/Generative-ai-and-diffusion-models-project/`

**Topics à ajouter** (un par un, séparés, sans # ni virgule dans le champ GitHub) :
`generative-ai`, `diffusion-models`, `multi-llm`, `rag`, `green-ai`, `finops`, `predictive-maintenance`, `medical-equipment`, `mlops`, `human-in-the-loop`, `python`, `ece-paris`.

**Social preview :** GitHub ne peut pas générer automatiquement une vignette à partir du README. Utiliser une image PNG originale, approuvée par le groupe, ajoutée manuellement dans Settings → General → Social preview ; ne pas publier de capture de dispositifs/patients réels. L'image animée SVG du README n'est pas une garantie de rendu dans les cartes sociales.

## Détails de la configuration

1. Aller dans le dépôt → **About** (panneau à droite) → roue dentée.
2. Remplacer Description, ajouter Topics, laisser Website vide tant que la page n'est pas active.
3. **Sans attendre PR #1**, vérifier **Settings → Pages → Deploy from a branch → gh-pages / (root)**, et enregistrer si ce n'est pas déjà sélectionné. Cette branche indépendante a déjà été créée et contient le site. Elle ne modifie pas `main`.
4. Vérifier l'URL de publication ; l'ajouter dans Website.
5. Garder la **protection de `main`** et les validations de PR. Ne pas désactiver le ruleset pour effectuer ces réglages.

## Responsabilité
**Gémima**, en tant qu'administratrice du dépôt, peut appliquer ces paramètres dans l'interface GitHub. **Ayoub** vérifie l'aspect technique et le déploiement. Le groupe approuve les visuels, l'identité et la politique de publication. La synchronisation des pages ne vaut pas validation clinique ni achèvement de C3/TP04/TP05.
