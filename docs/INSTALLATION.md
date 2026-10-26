# Installer Scoralyx Player

Ce guide décrit la préparation d’un mini-PC dédié et l’installation de Scoralyx Player 0.6.0.

## Prérequis

- Debian 13 (cible principale) ; Ubuntu ou une autre distribution Linux compatible peut fonctionner, sans validation complète à ce jour.
- Une architecture compatible avec la distribution, Chromium et Python. x86_64 est la cible initiale ; les autres architectures restent à valider.
- Un écran relié au mini-PC et un environnement graphique fonctionnel.
- Python 3.11 ou supérieur, `venv`, Bash, Git, systemd utilisateur et Chromium. L’installateur vérifie certains composants et peut proposer l’installation de dépendances système.
- Un accès Internet pendant l’installation pour GitHub, les dépôts de paquets de la distribution et PyPI. Au fonctionnement, le Player doit joindre le site Scoralyx en HTTPS.
- Un compte Linux membre du groupe `sudo` pour installer les paquets et configurer les fonctions nécessitant les droits administrateur.

Aucune configuration minimale processeur/mémoire/disque n’a été validée. Prévoir une machine qui exécute correctement Debian, son bureau graphique et Chromium à la résolution cible. Aucun port entrant vers le mini-PC n’est requis.

## Préparer le site Scoralyx

Le **site Scoralyx** (parfois appelé « Scoralyx Serveur ») est le site internet du club. Il repose sur SPIP et quelques plugins dédiés, installés sur un hébergement web compatible. Ces plugins fournissent notamment la gestion des écrans et les pages d’affichage.

Le Player ne peut être associé qu’une fois ce site installé, accessible en HTTPS et équipé des versions compatibles indiquées dans [la matrice de compatibilité](COMPATIBILITE.md). La mise en place demande quelques bases d’administration d’un site web et de ses plugins, mais elle s’appuie sur des composants SPIP classiques et reste accessible. Si le site du club existe déjà, vérifier simplement ses versions et son accès HTTPS.

### Vérifier les droits `sudo`

```sh
groups
```

Si `sudo` n’apparaît pas, utiliser un compte administrateur `root` pour ajouter l’utilisateur au groupe :

```sh
su -
adduser <nom_utilisateur> sudo
exit
```

Remplacer `<nom_utilisateur>` par le nom retourné par `id -un`. Fermer puis rouvrir la session pour appliquer le changement. Si le mot de passe `root` n’est pas disponible, demander à l’administrateur de la machine.

## Préparer le mini-PC pour l’affichage autonome

Le Player démarre avec la session graphique de l’utilisateur. Une ouverture automatique de cette session est nécessaire après un redémarrage électrique. L’installateur peut configurer l’ouverture automatique pour GDM, LightDM ou SDDM et proposer la désactivation de la veille et du verrouillage.

La désactivation persistante de la veille et du verrouillage est automatisée pour GNOME. Les autres environnements sont détectés, mais peuvent nécessiter une configuration manuelle. Les changements d’ouverture automatique prennent effet au démarrage suivant. Le script ne redémarre pas le gestionnaire d’affichage pendant l’installation.

L’ouverture automatique supprime la demande de mot de passe à la connexion : réserver cette configuration à une machine dédiée à l’affichage, placée dans un lieu physiquement maîtrisé.

Le contrôle Digital Signage peut également être lancé séparément depuis le dépôt :

```sh
bash deploy/digital-signage/configure-digital-signage.sh --check
bash deploy/digital-signage/configure-digital-signage.sh --configure
```

Ajouter `--user nom` pour cibler un autre compte graphique. `--check` ne modifie pas la machine. `--configure` demande confirmation avant les changements et peut nécessiter `sudo`. Pour réappliquer les réglages GNOME depuis la session graphique :

```sh
bash deploy/digital-signage/configure-digital-signage.sh --apply-session
```

Le script sauvegarde les fichiers de configuration qu’il remplace.

## Cloner et installer

Utiliser le compte Linux qui ouvrira la session graphique. Ne pas exécuter l’installateur avec `sudo`.

```sh
sudo apt update
sudo apt install git
cd ~
git clone https://github.com/Ybbet/scx_player.git
cd scx_player
bash install.sh
```

L’installateur interactif demande :

1. **L’URL du site Scoralyx**, par exemple `https://club.example.org`, sans `spip.php` ni chemin de page.
2. **Le nom unique du Player**, par exemple `clubhouse-01`.
3. **La configuration des prérequis**, si Python `venv` ou Chromium manque.
4. **Le mode RTC**, si `rtcwake` existe et si le test de programmation d’alarme aboutit. L’installateur demande également si le firmware autorise le réveil après arrêt.
5. **La préparation Digital Signage**, notamment l’ouverture automatique de session et les réglages de veille/verrouillage disponibles.

L’installateur crée un environnement Python isolé, écrit la configuration locale et prépare le service systemd utilisateur. Si le mode RTC est utilisable, il installe un helper privilégié limité à l’arrêt et à la programmation du réveil. Si `rtcwake` est absent, le test échoue ou le réveil firmware n’est pas confirmé, le Player laisse la machine allumée et affiche une page noire hors plage.

## Autoriser et associer le Player

À la fin de l’installation, le Player demande son enrôlement au site Scoralyx. Dans l’administration SPIP, autoriser la demande, puis associer le Player à un écran existant ou créer l’écran correspondant. Le code d’appairage apparaît dans les journaux :

```sh
journalctl --user -u scoralyx-player.service -f
```

Après association, le Player récupère l’identifiant de l’écran et ouvre la page d’affichage correspondante dans Chromium.

## Emplacements locaux

- Configuration : `~/.config/scoralyx-player/config.toml`
- Environnement Python : `~/.local/share/scoralyx-player/venv/`
- État local et jeton d’authentification : `~/.local/state/scoralyx-player/state.json`

Ne pas partager le fichier d’état : il contient des informations d’authentification.
