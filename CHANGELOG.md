# Journal des modifications

## 0.2.0 — installation interactive

- Ajoute `install.sh` pour vérifier et installer les prérequis, demander l'URL Scoralyx et le nom du Player, écrire la configuration, puis préparer et activer le service systemd utilisateur.
- Guide l'utilisateur pour terminer l'autorisation et l'association de l'écran dans SPIP.

## 0.1.0 — première version de développement

- Ajoute l'enrôlement auprès de `scx_ecrans` et la conservation locale des secrets.
- Lit la configuration de l'écran et applique les états `on` et `off`.
- Lance Chromium en kiosque sur `scx_affichage` avec l'identifiant d'écran.
- Transmet les heartbeats, événements techniques et déclenchements `actualisation` autorisés.
- Fournit une unité systemd utilisateur et une configuration TOML.
- Limite cette première version à un écran noir logiciel hors plage ; aucune extinction matérielle n'est déclenchée.

