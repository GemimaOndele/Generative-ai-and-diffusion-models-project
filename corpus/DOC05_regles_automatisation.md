# DOC05 — Règles d'automatisation du pipeline (v1.0, 2026-11-18)
Idempotence : chaque fichier importé est identifié par son empreinte SHA-256. Un fichier dont l'empreinte existe déjà est ignoré, ce qui évite de créer deux fois le même lot et donc des alertes en double.

Déduplication : une observation est unique par couple (équipement, clé source). Les doublons sont comptés et non insérés.

Validation : chaque ligne est contrôlée selon le contrat de données (champs obligatoires, types, plages physiques, cohérence température process ≥ température air). Les lignes invalides sont placées en quarantaine dans un fichier de rejets.

Reprises : en cas d'erreur réseau d'une source API, au plus 3 tentatives avec attente exponentielle, puis escalade à un humain.

Une analyse produit au plus une alerte. Une alerte n'est créée que si le score dépasse le seuil configuré.
