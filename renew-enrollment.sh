#!/usr/bin/env bash
set -Eeuo pipefail

SERVICE="scoralyx-player.service"
CONFIG_FILE="${1:-${XDG_CONFIG_HOME:-$HOME/.config}/scoralyx-player/config.toml}"

die() { printf 'Erreur : %s\n' "$*" >&2; exit 1; }

if [[ $# -gt 1 ]]; then
    die "Usage : $0 [chemin/vers/config.toml]"
fi
if [[ $EUID -eq 0 ]]; then
    die "Exécuter ce script depuis le compte Linux du Player, sans sudo."
fi
command -v python3 >/dev/null 2>&1 || die "Python 3.11 ou supérieur est requis pour lire la configuration TOML."
python3 -c 'import sys, tomllib; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || die "Python 3.11 ou supérieur est requis."
[[ -r "$CONFIG_FILE" ]] || die "Configuration introuvable ou illisible : $CONFIG_FILE"
command -v systemctl >/dev/null 2>&1 || die "systemctl est introuvable."
systemctl --user cat "$SERVICE" >/dev/null 2>&1 || die "Service utilisateur $SERVICE introuvable. Lancer d'abord install.sh."

STATE_FILE="$(python3 - "$CONFIG_FILE" <<'PY'
import sys
import tomllib
from pathlib import Path

with open(sys.argv[1], "rb") as stream:
    config = tomllib.load(stream)
state = config.get("paths", {}).get("state", "/var/lib/scoralyx-player/state.json")
print(Path(state).expanduser())
PY
)" || die "Impossible de lire le chemin de l'état local dans $CONFIG_FILE"
[[ -f "$STATE_FILE" ]] || die "État local introuvable : $STATE_FILE"
[[ -w "$(dirname -- "$STATE_FILE")" ]] || die "Droits insuffisants pour modifier $(dirname -- "$STATE_FILE")."

MACHINE_NAME="$(python3 - "$CONFIG_FILE" <<'PY'
import sys
import tomllib

with open(sys.argv[1], "rb") as stream:
    config = tomllib.load(stream)
print(config.get("player", {}).get("machine_name", "Player"))
PY
)" || die "Impossible de lire le nom du Player dans $CONFIG_FILE"

ENROLLMENT_STATE="$(python3 - "$STATE_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    state = json.load(stream)
print("autorisé" if state.get("token") else "en attente ou non enrôlé")
PY
)" || die "État local invalide : $STATE_FILE"

printf 'Renouvellement de l’enrôlement Scoralyx Player\n'
printf 'Player : %s (%s)\n' "$MACHINE_NAME" "$ENROLLMENT_STATE"
printf 'Configuration : %s\n' "$CONFIG_FILE"
printf 'État local : %s\n\n' "$STATE_FILE"
printf 'Ce script ne révoque pas le Player sur Scoralyx Serveur.\n'
printf 'Révoquer le Player déjà autorisé dans l’administration SPIP avant de continuer.\n'
printf 'Pour une demande encore en attente, la refuser ou la supprimer afin d’éviter un doublon.\n\n'
read -r -p 'Après cette action sur le serveur, saisir RENOUVELER pour continuer : ' confirmation
[[ "$confirmation" == "RENOUVELER" ]] || die "Opération annulée."

BACKUP_FILE="$(mktemp "${STATE_FILE}.renew.XXXXXX")" || die "Impossible de sauvegarder l’état local."
chmod 600 "$BACKUP_FILE"
cp -p -- "$STATE_FILE" "$BACKUP_FILE" || { rm -f -- "$BACKUP_FILE"; die "Impossible de sauvegarder l’état local."; }

restore_state() {
    systemctl --user stop "$SERVICE" >/dev/null 2>&1 || true
    mv -f -- "$BACKUP_FILE" "$STATE_FILE"
    systemctl --user start "$SERVICE" >/dev/null 2>&1 || true
}

if ! systemctl --user stop "$SERVICE"; then
    rm -f -- "$BACKUP_FILE"
    die "Impossible d’arrêter le service. L’état local n’a pas été modifié."
fi

if ! rm -f -- "$STATE_FILE"; then
    restore_state
    die "Impossible de supprimer l’état local. L’ancien enrôlement a été restauré."
fi

if ! systemctl --user start "$SERVICE" || ! systemctl --user is-active --quiet "$SERVICE"; then
    restore_state
    die "Le Player n’a pas redémarré. L’ancien état local a été restauré. Consulter journalctl."
fi

rm -f -- "$BACKUP_FILE"
printf '\nNouvelle demande d’enrôlement lancée.\n'
printf 'Consulter le code d’appairage avec :\n'
printf '  journalctl --user -u %s -f\n' "$SERVICE"
