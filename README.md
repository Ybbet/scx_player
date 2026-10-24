# Scoralyx Player

Scoralyx Player est le lecteur kiosque Linux de l’écosystème Scoralyx. Il ouvre dans Chromium la page d’affichage du club, en plein écran, avec le paramètre `ecran=<identifiant>`. Le contenu affiché est choisi par le serveur Scoralyx ; le Player applique les horaires et transmet au serveur les heartbeats, événements et déclenchements prévus par le contrat d’écran.

Version : **0.3.4**. La numérotation suit SemVer. Licence : GNU GPL v3 ou ultérieure (`GPL-3.0-or-later`). Voir le fichier [`LICENSE`](LICENSE).

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

### Préparer les droits administrateur sous Debian

L’installation des paquets système nécessite un compte membre du groupe `sudo`. Vérifier les groupes du compte :

```sh
groups
```

Si `sudo` n’apparaît pas, relever le nom du compte avec `id -un`, puis ouvrir une session `root` et ajouter ce compte au groupe :

```sh
su -
adduser <nom_utilisateur> sudo
exit
```

Remplacer `<nom_utilisateur>` par le nom relevé avant le passage à `root`. Se déconnecter puis se reconnecter pour appliquer le changement, puis vérifier de nouveau avec `groups`. Cette opération nécessite le mot de passe `root`. En l’absence de ce mot de passe, demander à un administrateur d’effectuer l’ajout.

## Compatibilité avec l’écosystème Scoralyx

Pour utiliser le Player avec un écran Scoralyx, installer sur le site les composants et versions de référence suivants :

| Composant | Version de référence | Rôle dans l’intégration |
|---|---:|---|
| SPIP | 4.4.x | Version requise par le plugin de gestion des écrans. |
| `scx_core` | 0.1.1 ou supérieure | Dépendance requise par les plugins de gestion des écrans et d’affichage. |
| `scx_ecrans` | 0.3.0 | Fournir l’API Player v1 pour l’enrôlement, les heartbeats, les états et les déclenchements. |
| `scx_affichage` | 0.2.14 | Fournir la page `affichage_ecran` et accepter le paramètre `ecran=<identifiant>`. |

Le contrat retenu suppose que l’identifiant de l’écran (`screen.id`) est aussi celui de la composition. Les versions indiquées correspondent à la base de versions utilisée pour valider cette intégration. Les autres plugins métier dépendent des contenus souhaités sur le site et ne sont pas des prérequis directs du Player.

## Récupérer les sources et installer

Lancer l’installation depuis le compte Linux qui ouvrira la session graphique. **Ne pas lancer l’installateur avec `sudo`** : Chromium et le service systemd utilisateur utilisent le compte courant.

1. Ouvrir un terminal sur le mini-PC. Installer Git si nécessaire :

   ```sh
   sudo apt update
   sudo apt install git
   ```

2. Depuis le répertoire personnel du compte Linux utilisé pour l’installation (`/home/<utilisateur>`), cloner le dépôt GitHub. Le dépôt sera placé dans `/home/<utilisateur>/scx_player` :

   ```sh
   cd ~
   git clone https://github.com/Ybbet/scx_player.git
   cd scx_player
   ```

3. Lancer l’installateur interactif :

   ```sh
   bash install.sh
   ```

4. Répondre aux questions de l’installateur :

   - **URL de Scoralyx Serveur** : indiquer l’URL de base du site, par exemple `https://club.example.org`, sans ajouter `spip.php` ni le chemin de la page d’affichage ;
   - **nom du Player** : choisir un nom stable et unique, par exemple `clubhouse-01` ;
   - **prérequis** : si Python `venv` ou Chromium manque, l’installateur propose de les installer avec `apt` ;
   - **réveil RTC** : si `rtcwake` est présent, l’installateur vérifie qu’une alarme peut être programmée puis demande si le BIOS/UEFI permet le réveil après un arrêt électrique.

L’installateur crée un environnement Python isolé, écrit la configuration locale et prépare le service systemd. En mode RTC, il installe aussi un helper root limité à la programmation du réveil et à l’arrêt de la machine. Si `rtcwake` est absent, si le test échoue ou si le réveil firmware n’est pas confirmé, le Player reste allumé et affiche une page noire lorsque l’état attendu est `off`.

## Autoriser et associer l’écran dans SPIP

Après l’installation, le Player envoie une demande d’enrôlement à Scoralyx Serveur. Dans l’administration SPIP, autoriser ce Player, puis l’associer à un écran existant ou créer l’écran correspondant. Consulter les journaux pour obtenir le code d’appairage :

```sh
journalctl --user -u scoralyx-player.service -f
```

Une fois autorisé, le Player récupère son identifiant d’écran et ouvre la page kiosque avec `ecran=<screen.id>`. Il interroge ensuite le serveur pour connaître son état et ses horaires.

## Démarrage et commandes utiles

Le service démarre avec la session graphique de l’utilisateur. Pour relancer le kiosque après un démarrage électrique, configurer la connexion automatique de cette session dans l’environnement de bureau.

```sh
systemctl --user status scoralyx-player.service
journalctl --user -u scoralyx-player.service -f
~/.local/share/scoralyx-player/venv/bin/scoralyx-player --config ~/.config/scoralyx-player/config.toml status
```

Si l’installateur n’a pas pu joindre le gestionnaire systemd utilisateur, ouvrez la session graphique puis activez le service :

```sh
systemctl --user daemon-reload
systemctl --user enable --now scoralyx-player.service
```

Les fichiers sont placés dans `~/.config/scoralyx-player/`, `~/.local/share/scoralyx-player/` et `~/.local/state/scoralyx-player/`. Le dernier répertoire contient l’état local d’enrôlement et le jeton ; il ne doit pas être partagé.

## Horaires et alimentation

Le serveur reste la source de vérité. Le Player applique `state.expected`, `next_start` et `next_stop` sans recalculer les créneaux ou exceptions. Lorsque le mode RTC est actif, il programme le prochain réveil puis arrête le mini-PC à l’état `off`. Le Player ne met pas séparément hors tension l’écran externe.

La programmation d’une alarme ne garantit pas que le mini-PC se réveillera après un arrêt S5 : cela dépend du BIOS/UEFI, de la carte mère et de l’horloge RTC. Le test de l’installateur vérifie la programmation de l’alarme, pas le réveil complet depuis l’arrêt. Vérifier ce comportement sur le matériel avant de compter sur le démarrage automatique. Lorsque le mode RTC n’est pas utilisable, la machine reste allumée et Chromium affiche une page noire hors plage.

## Dépannage

- **Le code d’appairage n’apparaît pas** : vérifier le fonctionnement du service et l’accès du mini-PC à l’URL configurée ; consulter `journalctl`.
- **Le Player est autorisé mais l’écran ne s’affiche pas** : vérifier l’association à un écran dans SPIP, la session graphique et la présence de Chromium.
- **Le service ne démarre pas** : ouvrir la session graphique du compte ayant lancé l’installation, puis consulter le statut et les journaux du service.
- **La machine ne se réveille pas** : désactiver le mode RTC dans `~/.config/scoralyx-player/config.toml` (`[power]`, `rtcwake_enabled = false`), puis redémarrer le service avec `systemctl --user restart scoralyx-player.service`. La machine restera alors allumée hors plage.
- **Le réveil RTC a été activé à tort** : désactiver le mode dans la configuration et redémarrer le service. Pour retirer ensuite le helper privilégié, exécuter `sudo rm /etc/sudoers.d/scoralyx-player /usr/local/sbin/scoralyx-player-rtcwake`.

## Développement et tests

Depuis le répertoire du dépôt :

```sh
python3 -m unittest discover -s tests -v
```
