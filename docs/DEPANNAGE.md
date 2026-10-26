# Dépannage

Commencer par vérifier le service dans la session graphique du compte qui a installé Scoralyx Player :

```sh
systemctl --user status scoralyx-player.service
journalctl --user -u scoralyx-player.service -n 100 --no-pager
```

Le suivi en direct s’effectue avec :

```sh
journalctl --user -u scoralyx-player.service -f
```

## Le code d’appairage n’apparaît pas

Vérifier que le service démarre et que le mini-PC accède à l’URL configurée. Si une demande antérieure existe déjà, vérifier son état dans l’administration serveur. En cas de renouvellement, révoquer ou refuser l’ancien Player côté serveur avant de réinitialiser l’état local avec `bash ~/scx_player/renew-enrollment.sh`.

## Chromium montre une page blanche ou ne montre pas le diaporama

1. Vérifier que le Player a été autorisé et associé à un écran dans l’administration.
2. Consulter les journaux pour confirmer que le Player reçoit la configuration et passe en état `on`.
3. Vérifier que l’identifiant de l’écran est transmis comme `ecran=<identifiant>` et que la page `affichage_ecran` s’ouvre.
4. Vérifier que l’écran est en état actif selon les horaires du serveur. En état `off`, le Player affiche volontairement sa page noire locale, ou éteint la machine si le mode RTC fonctionne.
5. Vérifier que la session graphique est ouverte et que Chromium peut afficher une page dans cette session.

L’ouverture manuelle de Chromium depuis un terminal SSH échoue souvent en l’absence de `DISPLAY` ou de session Wayland. Cela ne permet pas à elle seule de conclure que Chromium ne fonctionne pas depuis le bureau local.

## Le service ne démarre pas au redémarrage

Le service est un service systemd utilisateur : il démarre avec la session graphique. Vérifier que la connexion automatique est configurée pour ce compte. Si le service n’a pas été activé :

```sh
systemctl --user daemon-reload
systemctl --user enable --now scoralyx-player.service
```

## L’authentification échoue en HTTP 401

Vérifier que le Player est toujours autorisé et associé côté serveur, puis comparer les versions de `scx_ecrans` et du Player avec [la matrice de compatibilité](COMPATIBILITE.md). La version 0.6.0 transmet le Bearer token dans `Authorization` et `X-Scoralyx-Authorization`. Ne jamais publier le contenu du fichier `~/.local/state/scoralyx-player/state.json` : il contient le jeton.

## L’écran reste noir ou le réveil ne fonctionne pas

Un écran noir correspond à l’état `off` lorsque la machine reste allumée. Vérifier l’état attendu et les prochains horaires dans le `status` du Player et dans l’administration. Le réveil RTC depuis l’arrêt dépend du matériel et du BIOS/UEFI ; la programmation d’une alarme seule ne garantit pas le réveil.

Pour désactiver le mode RTC, modifier `~/.config/scoralyx-player/config.toml` :

```toml
[power]
rtcwake_enabled = false
```

Puis redémarrer le service :

```sh
systemctl --user restart scoralyx-player.service
```

La machine restera alors allumée et le Player utilisera la page noire hors plage.

## Retirer le helper RTC privilégié

Après désactivation du mode RTC, retirer si nécessaire le helper installé par l’installateur :

```sh
sudo rm /etc/sudoers.d/scoralyx-player /usr/local/sbin/scoralyx-player-rtcwake
```
