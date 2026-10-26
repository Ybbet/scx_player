# Scoralyx Player

**Un affichage de club qui se pilote depuis Scoralyx.** Scoralyx Player transforme un mini-PC Linux relié à un écran en lecteur d’affichage numérique. Il ouvre en plein écran la page du club dans Chromium et la maintient synchronisée avec le serveur Scoralyx.

Le Player est conçu pour les clubs et les structures qui souhaitent diffuser leurs informations sur un écran sans en faire un poste informatique à gérer au quotidien. Les contenus et leur organisation restent pilotés côté serveur ; le Player assure la lecture, le suivi de l’écran et l’application des horaires configurés.

> **Version 0.6.0** · Linux · Chromium · Licence GNU GPL v3 ou ultérieure

## Ce que permet le Player

- **Diffuser les informations du club** sur un écran dédié, en mode kiosque plein écran.
- **Centraliser la gestion des contenus** : le serveur Scoralyx décide des diapositives à afficher ; le Player ouvre la page correspondant à son écran.
- **Suivre les horaires configurés** : le serveur indique si l’écran doit être actif et les prochaines transitions.
- **Exploiter un mini-PC de façon autonome** : démarrage du service avec la session graphique, désactivation configurable de la veille et, si le matériel le permet, extinction et réveil par RTC.
- **Superviser et actualiser le parc** : heartbeats, événements et déclenchements sont transmis au serveur. Les mises à jour logicielles distantes nécessitent une autorisation explicite dans l’administration Scoralyx.

Le Player ne décide pas du contenu éditorial et ne nécessite aucun port entrant ouvert sur le mini-PC. Il communique avec le serveur Scoralyx en HTTPS.

## Pour quel matériel et quel niveau technique ?

Prévoir un mini-PC compatible avec Debian 13, une sortie vidéo, un écran et une connexion réseau stable. Chromium, Python 3.11 ou supérieur, `systemd` utilisateur et une session graphique sont nécessaires. Debian 13 est la cible principale ; Ubuntu et d’autres distributions Linux peuvent fonctionner si elles fournissent ces composants, mais ne sont pas encore validées sur matériel.

Aucun minimum de processeur, de mémoire vive ou d’espace disque n’a encore été établi par des tests représentatifs. Choisir une machine capable de faire fonctionner confortablement Debian avec une session graphique et Chromium à la résolution de l’écran. Tester le réveil depuis l’arrêt sur le matériel concerné : il dépend du BIOS/UEFI et de l’horloge RTC.

L’installation est interactive, mais suppose de savoir utiliser un terminal, cloner un dépôt Git, employer `sudo` pour les paquets système et retrouver les journaux d’un service systemd. La configuration de la connexion automatique supprime la demande de mot de passe au démarrage : réserver cette machine à l’affichage et la protéger physiquement.

## Démarrage rapide

Depuis le compte Linux qui ouvrira la session graphique :

```sh
sudo apt update
sudo apt install git
cd ~
git clone https://github.com/Ybbet/scx_player.git
cd scx_player
bash install.sh
```

L’installateur demande l’URL de Scoralyx Serveur et un nom unique pour le Player, vérifie les composants nécessaires et prépare le service. Il guide également la configuration Digital Signage et le choix du mode d’alimentation. **Ne pas lancer `install.sh` avec `sudo`** : le service et Chromium doivent s’exécuter sous le compte de la session graphique.

Après l’installation, autoriser le Player dans l’administration Scoralyx, puis l’associer à un écran. Le code d’appairage et l’état du service sont consultables ainsi :

```sh
journalctl --user -u scoralyx-player.service -f
```

Le détail des étapes figure dans [Installation](docs/INSTALLATION.md).

## Documentation

- [Installation et préparation de la machine](docs/INSTALLATION.md)
- [Fonctionnement et exploitation](docs/EXPLOITATION.md)
- [Compatibilité avec l’écosystème Scoralyx](docs/COMPATIBILITE.md)
- [Dépannage](docs/DEPANNAGE.md)

## Développement

Les tests unitaires s’exécutent depuis la racine du dépôt :

```sh
python3 -m unittest discover -s tests -v
```

Les publications suivent SemVer. La version est déclarée dans `pyproject.toml` et `src/scoralyx_player/__init__.py`. Le workflow GitHub vérifie leur cohérence et les tests avant de créer le tag et la release.

## Licence et contributions

Scoralyx Player est distribué sous GNU GPL version 3 ou toute version ultérieure. Consulter [`LICENSE`](LICENSE). Les contributions sont les bienvenues : proposer une issue pour décrire un besoin ou une anomalie, puis une pull request ciblée accompagnée des tests adaptés.
