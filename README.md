# Scoralyx Player

Client Linux de l'écosystème Scoralyx. La première version vise Debian 13 et les distributions Linux disposant de Python 3.11+, de systemd et d'un navigateur Chromium compatible.

Version : **0.1.0** (première version de développement, SemVer). Le choix de licence reste à fixer avant publication publique.

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

Copier `config.example.toml` vers `~/.config/scoralyx-player/config.toml`, puis régler au minimum `server.site_url` et `player.machine_name`. Le nom machine doit être stable et unique. Le fichier d'état, qui contient le jeton, doit rester lisible uniquement par le compte Linux exécutant le Player.

```sh
python3 -m venv ~/.local/share/scoralyx-player/venv
~/.local/share/scoralyx-player/venv/bin/pip install .
~/.local/share/scoralyx-player/venv/bin/scoralyx-player --config ~/.config/scoralyx-player/config.toml run
```

Le compte Linux doit disposer d'une session graphique fonctionnelle. Chromium hérite des variables de cette session (`DISPLAY` ou `WAYLAND_DISPLAY`). Installer Chromium avec le gestionnaire de paquets de la distribution.

Dans une première console, surveiller le code d'appairage ; dans SPIP, autoriser ensuite le Player et l'associer à un écran. Le Player détecte l'autorisation automatiquement.

```sh
~/.local/share/scoralyx-player/venv/bin/scoralyx-player --config ~/.config/scoralyx-player/config.toml status
```

## Service systemd utilisateur

Après installation dans le compte qui ouvre la session graphique, adapter `deploy/systemd/scoralyx-player.service` puis l'activer :

```sh
mkdir -p ~/.config/systemd/user
cp deploy/systemd/scoralyx-player.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now scoralyx-player.service
```

Le service doit être lancé dans la session graphique du compte dédié, afin que Chromium accède au serveur d'affichage. Ce service ne configure pas la connexion automatique du bureau ni le réveil BIOS.

## Développement et tests

```sh
python3 -m unittest discover -s tests -v
```

