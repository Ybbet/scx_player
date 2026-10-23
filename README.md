# Scoralyx Player

Client Linux de l'écosystème Scoralyx. La première version vise Debian 13 et les distributions Linux disposant de Python 3.11+, de systemd et d'un navigateur Chromium compatible.

Version : **0.2.0** (installateur interactif, SemVer). Le choix de licence reste à fixer avant publication publique.

## Périmètre de cette version

- enrôlement auprès de `scx_ecrans` et affichage du code d'appairage dans les journaux ;
- conservation locale de l'identifiant d'installation, du secret temporaire et du jeton ;
- lecture périodique de l'état et de la configuration de l'écran ;
- lancement du kiosque avec `ecran=<screen.id>` ;
- écran noir lorsque l'état attendu est `off`, tout en maintenant les échanges de supervision ;
- heartbeat et déclenchement `actualisation` lorsque cette capacité est autorisée ;
- appels HTTP JSON sans dépendance Python externe.

Le Player ne lance aucune commande shell reçue de SPIP. Cette version ne coupe pas l'alimentation du mini-PC : l'état `off` place le navigateur sur une page noire. La veille, l'extinction physique et le réveil matériel nécessitent un choix d'intégration propre au matériel et à la session graphique.

## Contrats Scoralyx utilisés

- API technique `scx_ecrans` v1 (cible du plugin 0.3.0) ;
- page kiosque `scx_affichage` avec `ecran=<identifiant>` (cible du plugin 0.2.14) ;
- `screen.id` et identifiant de composition sont supposés identiques, conformément au déploiement Scoralyx retenu.

Le Player ne reçoit pas l'URL complète de l'affichage. Il la construit depuis `server.site_url`, `paths.display` et `screen.id`.

## Configuration

Depuis le répertoire du projet, lancer l'installateur avec le compte Linux qui ouvre la session graphique :

```sh
bash install.sh
```

L'installateur vérifie Python 3.11+, `venv` et un navigateur Chromium. Sur Debian/Ubuntu, il peut installer les paquets système manquants avec `apt` et `sudo`. Il demande l'URL du site Scoralyx et le nom unique du Player, écrit la configuration protégée, installe le Player dans un environnement Python isolé et prépare son service systemd utilisateur. Le service est activé immédiatement si la session systemd utilisateur est disponible.

Le compte doit disposer d'une session graphique fonctionnelle, avec connexion automatique du bureau configurée sur le mini-PC. Le Player s'enrôle ensuite auprès du serveur. Dans SPIP, autoriser le Player et l'associer à un écran ; surveiller le code avec :

```sh
journalctl --user -u scoralyx-player.service -f
```

L'installateur enregistre les fichiers dans `~/.config/scoralyx-player/`, `~/.local/share/scoralyx-player/` et `~/.local/state/scoralyx-player/`. Il ne configure pas la connexion automatique du bureau, le réveil BIOS ni la mise hors tension physique de l'écran.

Pour vérifier l'état de l'enrôlement :

```sh
~/.local/share/scoralyx-player/venv/bin/scoralyx-player --config ~/.config/scoralyx-player/config.toml status
```

Sur une distribution sans `apt`, installer Python 3.11+, le module `venv`, systemd et Chromium avant de lancer l'installateur. La compatibilité dépend aussi de la disponibilité d'un navigateur Chromium exécutable dans la session graphique.

## Développement et tests

```sh
python3 -m unittest discover -s tests -v
```

