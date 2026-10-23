# Scoralyx Player

Scoralyx Player est le lecteur kiosque Linux de l’écosystème Scoralyx. Il ouvre dans Chromium la page d’affichage du club, en plein écran, avec le paramètre `ecran=<identifiant>`. Le contenu affiché est choisi par le serveur Scoralyx ; le Player applique les horaires et transmet au serveur les heartbeats, événements et déclenchements prévus par le contrat `scx_ecrans`.

Version : **0.3.1**. La numérotation suit SemVer. Le choix de licence reste à fixer avant une publication publique.

## Compatibilité et prérequis

| Élément | Prérequis |
|---|---|
| Système | Debian 13 est la cible principale. Ubuntu et les autres distributions Linux peuvent convenir si elles fournissent Python, Chromium, systemd et une session graphique ; elles ne sont pas encore validées sur matériel. |
| Architecture | Mini-PC compatible avec Debian 13 et Chromium. x86_64 est la cible initiale ; les autres architectures ne sont pas encore validées. |
| Affichage | Sortie vidéo et écran connectés ; environnement graphique fonctionnel. Une ouverture de session automatique est nécessaire pour afficher le kiosque après un redémarrage. |
| Logiciels | Bash, Git pour récupérer le dépôt, Python 3.11 ou supérieur avec `venv`, systemd utilisateur et Chromium (ou navigateur Chromium compatible). |
| Réseau | Le mini-PC doit joindre le serveur Scoralyx et résoudre son nom DNS. HTTPS sortant vers le serveur est requis en production. Aucun port entrant vers le mini-PC n’est nécessaire. |
| Installation | `sudo` est nécessaire pour installer des paquets système. Il est aussi utilisé pour installer le helper RTC si le mode réveil matériel est activé. |

Le projet ne fixe pas encore de seuil minimum de processeur, de mémoire ou d’espace disque validé. La machine doit pouvoir exécuter Debian 13 avec une session graphique et Chromium à la résolution de l’écran visé. Cette configuration reste à valider sur le mini-PC cible.

L’accès réseau est nécessaire pendant l’installation pour cloner le dépôt GitHub et, si besoin, récupérer les paquets système sur les dépôts de la distribution ainsi que les outils de construction Python sur PyPI. Au fonctionnement, le Player doit pouvoir accéder au serveur Scoralyx depuis le réseau local ou Internet, selon son hébergement. Un serveur accessible uniquement en HTTPS est attendu en production.

## Récupérer les sources et installer

L’installation doit être lancée depuis le compte Linux qui ouvrira la session graphique. **Ne lance pas l’installateur avec `sudo`** : il utilise le compte courant pour Chromium et le service systemd utilisateur.

1. Ouvre un terminal sur le mini-PC. Installe Git si nécessaire :

   ```sh
   sudo apt update
   sudo apt install git
   ```

2. Clone le dépôt GitHub. Remplace `<organisation-ou-utilisateur>` par le propriétaire du dépôt :

   ```sh
   git clone https://github.com/<organisation-ou-utilisateur>/scx_player.git
   cd scx_player
   ```

3. Lance l’installateur interactif :

   ```sh
   bash install.sh
   ```

4. Réponds aux questions de l’installateur :

   - **URL de Scoralyx Serveur** : indique l’URL de base du site, par exemple `https://club.example.org`, sans ajouter `spip.php` ni le chemin de la page d’affichage ;
   - **nom du Player** : choisis un nom stable et unique, par exemple `clubhouse-01` ;
   - **prérequis** : si Python `venv` ou Chromium manque, l’installateur propose de les installer avec `apt` ;
   - **réveil RTC** : si `rtcwake` est présent, l’installateur vérifie qu’une alarme peut être programmée puis demande si le BIOS/UEFI permet le réveil après un arrêt électrique.

L’installateur crée un environnement Python isolé, écrit la configuration locale et prépare le service systemd. En mode RTC, il installe aussi un helper root limité à la programmation du réveil et à l’arrêt de la machine. Si `rtcwake` est absent, si le test échoue ou si le réveil firmware n’est pas confirmé, le Player reste allumé et affiche une page noire lorsque l’état attendu est `off`.

## Autoriser et associer l’écran dans SPIP

Après l’installation, le Player envoie une demande d’enrôlement à Scoralyx Serveur. Dans l’administration SPIP, autorise ce Player puis associe-le à un écran existant ou crée l’écran correspondant. Le code d’appairage apparaît dans les journaux :

```sh
journalctl --user -u scoralyx-player.service -f
```

Une fois autorisé, le Player récupère son identifiant d’écran et ouvre la page kiosque avec `ecran=<screen.id>`. Il interroge ensuite l’API `scx_ecrans` pour connaître son état et ses horaires.

## Démarrage et commandes utiles

Le service démarre avec la session graphique de l’utilisateur. Pour que le kiosque reparte après un démarrage électrique, configure la connexion automatique de cette session dans l’environnement de bureau.

```sh
systemctl --user status scoralyx-player.service
journalctl --user -u scoralyx-player.service -f
~/.local/share/scoralyx-player/venv/bin/scoralyx-player --config ~/.config/scoralyx-player/config.toml status
```

Si l’installateur n’a pas pu joindre le gestionnaire systemd utilisateur, ouvre la session graphique puis active le service :

```sh
systemctl --user daemon-reload
systemctl --user enable --now scoralyx-player.service
```

Les fichiers sont placés dans `~/.config/scoralyx-player/`, `~/.local/share/scoralyx-player/` et `~/.local/state/scoralyx-player/`. Le dernier répertoire contient l’état local d’enrôlement et le jeton ; il ne doit pas être partagé.

## Horaires et alimentation

Le serveur reste la source de vérité. Le Player applique `state.expected`, `next_start` et `next_stop` sans recalculer les créneaux ou exceptions. Lorsque le mode RTC est actif, il programme le prochain réveil puis arrête le mini-PC à l’état `off`. Le Player ne met pas séparément hors tension l’écran externe.

La programmation d’une alarme ne garantit pas que le mini-PC se réveillera après un arrêt S5 : cela dépend du BIOS/UEFI, de la carte mère et de l’horloge RTC. Le test de l’installateur vérifie la programmation de l’alarme, pas le réveil complet depuis l’arrêt. Vérifie ce comportement sur le matériel avant de compter sur le démarrage automatique. Lorsque le mode RTC n’est pas utilisable, la machine reste allumée et Chromium affiche une page noire hors plage.

## Dépannage

- **Le code d’appairage n’apparaît pas** : vérifie que le service fonctionne et que le mini-PC peut joindre l’URL configurée ; consulte `journalctl`.
- **Le Player est autorisé mais l’écran ne s’affiche pas** : vérifie l’association à un écran dans SPIP, la session graphique et la présence de Chromium.
- **Le service ne démarre pas** : vérifie que tu es dans la session graphique du compte ayant lancé l’installation, puis consulte son statut et ses journaux.
- **La machine ne se réveille pas** : désactive le mode RTC dans `~/.config/scoralyx-player/config.toml` (`[power]`, `rtcwake_enabled = false`), puis redémarre le service avec `systemctl --user restart scoralyx-player.service`. La machine restera alors allumée hors plage.
- **Le réveil RTC a été activé à tort** : désactive d’abord le mode dans la configuration et redémarre le service. Pour retirer ensuite le helper privilégié, exécute `sudo rm /etc/sudoers.d/scoralyx-player /usr/local/sbin/scoralyx-player-rtcwake`.

## Contrats Scoralyx utilisés

- API technique `scx_ecrans` v1 ;
- page kiosque `scx_affichage` avec `ecran=<identifiant>` ;
- `screen.id` et identifiant de composition sont supposés identiques dans le déploiement retenu.

Le Player construit l’URL d’affichage à partir de `server.site_url`, du chemin local `paths.display` et de `screen.id`. Il ne reçoit pas de commande système du serveur et ne choisit pas le contenu des diapositives.

## Développement et tests

Depuis le répertoire du dépôt :

```sh
python3 -m unittest discover -s tests -v
```
