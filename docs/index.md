---
title: Scoralyx Player — l’affichage du club en grand
description: Une solution libre pour diffuser automatiquement la vie du club sur un écran, depuis Scoralyx.
hide:
  - navigation
---

<section class="scoralyx-hero" markdown>
<div class="scoralyx-hero__content" markdown>

# Votre club. En grand.

### Un affichage de club qui se pilote depuis Scoralyx.

Scoralyx Player transforme un mini-PC Linux relié à un écran en lecteur d’affichage numérique. Il ouvre en plein écran la page du club dans Chromium et la maintient synchronisée avec le serveur Scoralyx.

[Découvrir l’installation](INSTALLATION.md){ .md-button .md-button--primary }
[Voir le projet sur GitHub](https://github.com/Ybbet/scx_player){ .md-button }

</div>
<div class="scoralyx-hero__visual">
  <img src="assets/images/scoralyx_player.svg" alt="Logo Scoralyx Player">
</div>
</section>

<section class="scoralyx-benefits" markdown>

## La vie du club, à la bonne place

Les informations utiles gagnent à être visibles là où les adhérents, les bénévoles et les visiteurs se retrouvent.

<div class="grid cards" markdown>

-   :material-calendar-month-outline: **Un écran qui suit la vie du club**

    Programme, événements, résultats, messages ou match en cours : les contenus sont préparés côté serveur selon les modules et les réglages du club.

-   :material-clock-outline: **Une diffusion qui suit les horaires**

    Le serveur indique quand l’écran doit être actif. Si le mini-PC et son firmware le permettent, il peut aussi s’éteindre puis se réveiller automatiquement.

-   :material-cog-sync-outline: **Un pilotage centralisé**

    Le Player ne choisit pas les diapositives. Il affiche la page associée à son écran et laisse la gestion des contenus dans Scoralyx.

-   :material-open-source-initiative: **Une solution libre et maîtrisable**

    Le Player est publié sous GNU GPL v3 ou ultérieure et fonctionne sur un mini-PC Linux standard, sans lecteur propriétaire dédié.

</div>
</section>

<section class="scoralyx-how" markdown>

## Du serveur à l’écran, en quelques étapes

<div class="grid cards" markdown>

-   **1. Installer**

    Lancer l’installateur interactif sur le mini-PC, saisir l’adresse du serveur Scoralyx et choisir un nom unique pour le Player.

-   **2. Associer**

    Autoriser la demande d’enrôlement dans l’administration puis associer le Player à l’écran du club.

-   **3. Diffuser**

    Au démarrage de la session graphique, Chromium s’ouvre en plein écran et affiche la page de l’écran associé.

</div>

Le Player communique avec le serveur en HTTPS. Il n’a besoin d’aucun port entrant ouvert sur le mini-PC.

[Suivre le guide d’installation](INSTALLATION.md){ .md-button .md-button--primary }

</section>

## Pensé pour un affichage autonome

Scoralyx Player convient aux clubs et structures qui disposent d’un écran d’information et souhaitent automatiser sa diffusion à partir de leur site Scoralyx. Il s’appuie sur un mini-PC Linux relié à l’écran ; l’administration et les contenus restent côté serveur.

La préparation Digital Signage peut configurer l’ouverture automatique de session et désactiver la veille dans les environnements pris en charge. Si le matériel permet le réveil RTC, le Player peut programmer l’arrêt et le redémarrage électrique. Sinon, il maintient la machine active et affiche une page noire hors plage.

## Une installation accessible, avec quelques prérequis

| À prévoir | Détail |
|---|---|
| Matériel | Mini-PC Linux, sortie vidéo, écran et connexion réseau stable. |
| Système | Debian 13 est la cible principale. Ubuntu et les autres distributions Linux restent à valider sur le matériel choisi. |
| Logiciels | Chromium, Python 3.11+, Bash, systemd utilisateur et une session graphique. |
| Mise en place | Savoir utiliser un terminal, cloner un dépôt Git et disposer d’un accès `sudo`. |
| Serveur | Un site Scoralyx joignable en HTTPS avec les versions compatibles des plugins. |

Aucun minimum de processeur, mémoire ou stockage n’a encore été validé. Le réveil depuis un arrêt complet dépend du BIOS/UEFI et du matériel RTC : le tester sur le mini-PC retenu. La configuration de connexion automatique supprime la demande de mot de passe au démarrage ; réserver l’équipement à l’affichage et le protéger physiquement.

[Voir la compatibilité détaillée](COMPATIBILITE.md) · [Consulter les guides](INSTALLATION.md)

## Ouvert et évolutif

Scoralyx Player est un logiciel libre, versionné selon SemVer. Les mises à jour distantes ne sont pas appliquées sans accord : une nouvelle version est proposée au serveur, puis doit être autorisée dans l’administration Scoralyx.

**Version actuelle : 0.6.0** · [Code source et contributions sur GitHub](https://github.com/Ybbet/scx_player)
