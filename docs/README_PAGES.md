# GitHub Pages — source unique de publication (RCS-46)

**Source de référence du site vitrine : branche `gh-pages`, dossier racine `/(root)`.** La configuration active doit encore être confirmée dans **Settings → Pages** ; la présence de la branche ne prouve pas à elle seule que la publication est activée.

## Décision de structuration prise en compte après la revue d'Ayoub (23/11/2026)

- Les fichiers `docs/index.html`, `docs/landing.css` et `docs/landing.js` ont été **retirés de la PR #1** pour éviter deux copies concurrentes du site web.
- Les deux SVG `docs/assets/robocare-hero-animated.svg` et `docs/assets/architecture.svg` restent dans `main` après fusion, uniquement pour les illustrations de `README.md` et la documentation.
- La branche `gh-pages` héberge les fichiers de la vitrine à la racine : `index.html`, `landing.css`, `landing.js` et les assets correspondants.
- **Ne pas sélectionner `main /docs`** comme source Pages : cela réintroduirait une deuxième source de publication.
- Une correction future du site doit passer par la branche `gh-pages` avec revue, sans recopier toute la vitrine dans `main`.

## Vérifier la publication

1. Ouvrir le dépôt dans GitHub → **Settings → Pages**.
2. Dans **Build and deployment**, vérifier **Deploy from a branch → gh-pages / (root)**.
3. Consulter l'URL fournie par GitHub Pages, puis mettre à jour le champ **About → Website** si elle est effectivement publiée.
4. Contrôler manuellement sur navigateur le rendu responsive, les onglets et les animations réduites. Ce contrôle d'interface du site publié est distinct des tests GitHub Actions de la PR #1.

Adresse attendue mais **non vérifiée** : `https://gemimaondele.github.io/Generative-ai-and-diffusion-models-project/`.

## Tests dans PR #1

Le workflow `.github/workflows/pages-readiness.yml` vérifie maintenant : absence des trois copies du site dans `docs/`, présence/validité des SVG du README et documentation de la source unique de publication. **Il n'effectue aucun déploiement** et ne prétend pas tester le HTML/CSS/JS de la branche indépendante `gh-pages`.

## Sécurité et périmètre

Site institutionnel de démonstration uniquement. Aucune collecte de données personnelles ou médicales, aucun secret ni connexion à un équipement. Les validations scientifiques (diffusion, Multi-LLM et maintenance biomédicale) ne sont pas implicites dans la publication d'une vitrine.

Référence : [Documentation officielle GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
