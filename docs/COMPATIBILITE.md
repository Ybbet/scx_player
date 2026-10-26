# Compatibilité avec l’écosystème Scoralyx

Scoralyx Player est un lecteur Linux. Pour afficher un écran géré par Scoralyx, le site doit exposer les contrats de gestion d’écran et la page d’affichage attendus par le Player.

## Versions de référence

| Composant | Version de référence | Fonction nécessaire |
|---|---:|---|
| SPIP | 4.4.x | Socle du site Scoralyx et des plugins requis. |
| `scx_core` | 0.1.1 ou supérieure | Dépendance des plugins de gestion des écrans et d’affichage. |
| `scx_ecrans` | 0.7.0 ou supérieure | Enrôlement, association, API Player v1, horaires, heartbeats et contrat de mise à jour distante autorisée. |
| `scx_affichage` | 0.2.14 ou supérieure | Page `affichage_ecran` et paramètre `ecran=<identifiant>`. |

Le contrat actuel utilise l’identifiant de l’écran (`screen.id`) comme identifiant transmis à la composition d’affichage. Les versions indiquées forment la base de compatibilité retenue pour Scoralyx Player 0.6.0. Vérifier les notes de version des plugins avant toute montée de version du site.

Les plugins métier sont à choisir selon les contenus attendus par le club. Ils ne sont pas des dépendances directes du Player.

## Systèmes Linux

| Environnement | État |
|---|---|
| Debian 13 | Cible principale du Player. |
| Ubuntu | Peut fonctionner avec Python 3.11+, Chromium, Bash, systemd utilisateur et une session graphique ; validation matérielle encore nécessaire. |
| Autres distributions Linux | Compatibilité possible si les mêmes prérequis sont présents ; non validées. |

La configuration d’ouverture automatique est prévue pour GDM, LightDM et SDDM. Les réglages de désactivation persistante de la veille et du verrouillage sont automatisés pour GNOME. Les autres environnements peuvent exiger une configuration spécifique.

## Réseau et sécurité

- Le Player initie les connexions vers le serveur Scoralyx ; aucune connexion entrante vers le mini-PC n’est requise.
- HTTPS est attendu pour les échanges avec le serveur en production.
- Le jeton définitif reste dans l’état local protégé du compte Player et n’est pas placé dans l’URL.
- Les mises à jour distantes ne s’installent qu’après autorisation explicite dans l’administration Scoralyx.

