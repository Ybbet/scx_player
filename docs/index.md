---
title: Afficher la vie du club, simplement
description: Présentation de Scoralyx Player, le lecteur Linux d’affichage numérique relié à Scoralyx.
hide:
  - navigation
---

<div class="scoralyx-hero" markdown>

# L’affichage du club, toujours au bon endroit

Les informations utiles à la vie du club méritent d’être visibles là où les adhérents, les bénévoles et les visiteurs se retrouvent.

**Scoralyx Player transforme un mini-PC Linux en écran d’affichage autonome.** Il ouvre en plein écran la page de votre club et applique les horaires définis dans Scoralyx.

[Découvrir l’installation](INSTALLATION.md){ .md-button .md-button--primary }
[Voir le projet sur GitHub](https://github.com/Ybbet/scx_player){ .md-button }

</div>

## Un écran piloté depuis le serveur du club

Scoralyx Player est le lecteur installé sur le mini-PC raccordé à l’écran. Il affiche la page que le serveur Scoralyx prépare pour cet écran. Les responsables gardent ainsi la maîtrise du contenu dans l’outil du club, tandis que le Player assure la diffusion en mode kiosque.

<div class="grid cards" markdown>

-   :material-calendar-clock: **Diffuser les informations au bon moment**

    Le Player applique les périodes d’activité et les horaires transmis par le serveur. Selon le matériel, il peut aussi arrêter puis réveiller le mini-PC.

-   :material-monitor-dashboard: **Garder la gestion au même endroit**

    Les contenus ne sont pas définis dans le Player. Ils sont gérés côté Scoralyx et affichés par l’écran associé.

-   :material-refresh: **Suivre l’état de l’écran**

    Le Player transmet des heartbeats, événements et déclenchements au serveur pour permettre le suivi prévu par l’écosystème.

-   :material-shield-check: **Garder la main sur les mises à jour**

    Une nouvelle version peut être signalée, mais une mise à jour distante n’est installée qu’après autorisation explicite dans l’administration Scoralyx.

</div>

## Comment cela fonctionne

1. Installer Scoralyx Player sur un mini-PC Linux connecté à l’écran.
2. Indiquer l’URL du serveur Scoralyx et le nom unique du Player dans l’installateur.
3. Autoriser le Player dans l’administration du serveur et l’associer à l’écran souhaité.
4. Laisser le mini-PC démarrer sur sa session graphique : Chromium ouvre alors la page d’affichage en plein écran.

Le Player n’a pas besoin de port entrant ouvert. Il communique avec le serveur Scoralyx en HTTPS et transmet l’identifiant de l’écran dans l’adresse de la page d’affichage.

## Une solution pour les clubs et lieux de vie

Scoralyx Player convient aux associations et structures qui disposent d’un écran d’information et souhaitent automatiser sa diffusion à partir de leur site Scoralyx. La solution s’appuie sur un mini-PC standard plutôt que sur un lecteur propriétaire dédié.

Le Player est un composant de lecture : il ne crée pas les contenus et ne remplace pas l’administration Scoralyx. Les diapositives, leur ordre et les données affichées dépendent des composants installés et configurés sur le serveur.

## Ce qu’il faut prévoir

| Besoin | À prévoir |
|---|---|
| Matériel | Mini-PC Linux, sortie vidéo, écran et connexion réseau stable. |
| Système | Debian 13 est la cible principale. Ubuntu et les autres distributions Linux compatibles restent à valider sur matériel. |
| Session graphique | Chromium, Python 3.11+, systemd utilisateur et ouverture de session graphique automatique. |
| Installation | Usage d’un terminal, clonage Git, notions d’administration Linux et accès `sudo`. |
| Serveur | Un site Scoralyx accessible en HTTPS et les versions de plugins compatibles avec le Player. |

Aucun minimum CPU/RAM/stockage n’a encore été validé. Le réveil après extinction complète dépend aussi du BIOS/UEFI et du matériel RTC ; il doit être testé sur le mini-PC retenu.

[Lire les prérequis détaillés](COMPATIBILITE.md) · [Préparer le mini-PC et installer](INSTALLATION.md)

## Une solution libre

Scoralyx Player est publié sous **GNU GPL v3 ou ultérieure**. Le dépôt est ouvert aux retours et contributions. La version actuelle est **0.6.0** ; les versions suivent SemVer.

[Consulter les sources sur GitHub](https://github.com/Ybbet/scx_player)
