#!/usr/bin/env bash
set -Eeuo pipefail

VERSION="0.3.4"
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/scoralyx-player"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/scoralyx-player"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/scoralyx-player"
SYSTEMD_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

die() { printf 'Erreur : %s\n' "$*" >&2; exit 1; }
info() { printf '\n==> %s\n' "$*"; }
command -v python3 >/dev/null || die "Python 3 est absent. Installe Python 3.11 ou supérieur puis relance cet installateur."

PYTHON="$(command -v python3)"
PYTHON_VERSION="$($PYTHON -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
PYTHON_MAJOR="${PYTHON_VERSION%%.*}"
PYTHON_MINOR="${PYTHON_VERSION#*.}"
(( PYTHON_MAJOR > 3 || (PYTHON_MAJOR == 3 && PYTHON_MINOR >= 11) )) || die "Python 3.11+ est requis (détecté : $PYTHON_VERSION)."

if [[ $EUID -eq 0 ]]; then
    die "Ne lance pas ce script avec sudo : le Player doit être installé dans le compte qui ouvre la session graphique."
fi

printf 'Scoralyx Player — installation %s\n' "$VERSION"
printf 'Ce script configure le compte Linux actuel : %s\n' "$USER"
printf 'Le mini-PC doit ouvrir une session graphique pour afficher le kiosque.\n\n'

if ! "$PYTHON" -c 'import venv, tomllib' >/dev/null 2>&1; then
    if command -v apt-get >/dev/null 2>&1; then
        read -r -p "Le module Python venv manque. Installer python3-venv avec apt ? [O/n] " answer
        if [[ ! "$answer" =~ ^[nN] ]]; then
            command -v sudo >/dev/null 2>&1 || die "sudo est nécessaire pour installer python3-venv."
            sudo apt-get update
            sudo apt-get install -y python3-venv
        else
            die "Installe python3-venv puis relance l'installateur."
        fi
    else
        die "Le module venv manque dans Python. Installe-le avec le gestionnaire de paquets de ta distribution."
    fi
fi

if ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1 && ! command -v google-chrome >/dev/null 2>&1; then
    printf 'Aucun navigateur Chromium compatible n’a été détecté.\n'
    if command -v apt-get >/dev/null 2>&1; then
        read -r -p "Installer Chromium avec apt ? [O/n] " answer
        if [[ ! "$answer" =~ ^[nN] ]]; then
            SUDO=""
            if [[ $EUID -ne 0 ]]; then
                command -v sudo >/dev/null 2>&1 || die "sudo est nécessaire pour installer Chromium. Installe-le manuellement puis relance."
                SUDO="sudo"
            fi
            info "Installation des prérequis système"
            $SUDO apt-get update
            $SUDO apt-get install -y python3-venv chromium
        else
            die "Installe chromium, chromium-browser ou google-chrome puis relance l'installateur."
        fi
    else
        die "Installe chromium, chromium-browser ou google-chrome avec le gestionnaire de paquets de ta distribution puis relance."
    fi
fi

BROWSER="$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)"
[[ -x "$BROWSER" ]] || die "Le navigateur installé n'a pas été trouvé dans le PATH."

read -r -p "URL du site Scoralyx (ex. https://club.example.org) : " SITE_URL
SITE_URL="${SITE_URL%/}"
[[ "$SITE_URL" =~ ^https?://[^[:space:]]+$ ]] || die "L'URL doit commencer par https:// (ou http:// pour un serveur de test)."
if [[ "$SITE_URL" == http://* ]]; then
    read -r -p "HTTP transmet les échanges sans chiffrement. Continuer pour un test isolé ? [o/N] " answer
    [[ "$answer" =~ ^[oO]$ ]] || die "Installation annulée ; utilise HTTPS ou confirme HTTP pour un environnement de test isolé."
    ALLOW_HTTP=true
else
    ALLOW_HTTP=false
fi

DEFAULT_MACHINE="$(hostname -s 2>/dev/null || hostname)"
read -r -p "Nom unique de ce Player dans Scoralyx [$DEFAULT_MACHINE] : " MACHINE_NAME
MACHINE_NAME="${MACHINE_NAME:-$DEFAULT_MACHINE}"
[[ "$MACHINE_NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]{0,62}$ ]] || die "Utilise 1 à 63 caractères : lettres, chiffres, point, tiret ou souligné."

if [[ -f "$CONFIG_DIR/config.toml" ]]; then
    read -r -p "Une configuration existe déjà. La remplacer ? [o/N] " answer
    [[ "$answer" =~ ^[oO]$ ]] || die "Installation annulée ; configuration existante conservée."
fi

RTCWAKE_ENABLED=false
if command -v rtcwake >/dev/null 2>&1; then
    printf '\nrtcwake est présent. Le test suivant programme brièvement une alarme RTC sans mettre la machine en veille.\n'
    if command -v sudo >/dev/null 2>&1; then
        if sudo -v \
            && sudo rtcwake --mode no --seconds 300 \
            && RTC_ALARM="$(LC_ALL=C sudo rtcwake --mode show 2>/dev/null)" \
            && [[ "$RTC_ALARM" =~ alarm:[[:space:]]on ]]; then
            sudo rtcwake --mode disable >/dev/null 2>&1 || true
            read -r -p "Le BIOS/UEFI est-il réglé pour réveiller le mini-PC après un arrêt électrique (S5) ? [o/N] " answer
            if [[ "$answer" =~ ^[oO]$ ]]; then
                RTCWAKE_ENABLED=true
            fi
        else
            sudo rtcwake --mode disable >/dev/null 2>&1 || true
            printf 'Le test de programmation de l’alarme RTC a échoué ; le Player conservera la machine allumée et utilisera l’écran noir hors plage.\n'
        fi
    else
        printf 'sudo est absent ; le Player ne peut pas valider le réveil RTC et utilisera l’écran noir hors plage.\n'
    fi
else
    printf 'rtcwake est absent ; le Player conservera la machine allumée et utilisera l’écran noir hors plage.\n'
fi

info "Installation du Player et génération de la configuration"
mkdir -p "$CONFIG_DIR" "$DATA_DIR" "$STATE_DIR" "$SYSTEMD_DIR"
chmod 700 "$CONFIG_DIR" "$DATA_DIR" "$STATE_DIR"
"$PYTHON" -m venv "$DATA_DIR/venv"
"$DATA_DIR/venv/bin/python" -m pip install --upgrade pip
"$DATA_DIR/venv/bin/python" -m pip install "$PROJECT_DIR"

SITE_URL="$SITE_URL" MACHINE_NAME="$MACHINE_NAME" BROWSER="$BROWSER" ALLOW_HTTP="$ALLOW_HTTP" RTCWAKE_ENABLED="$RTCWAKE_ENABLED" CONFIG_DIR="$CONFIG_DIR" STATE_DIR="$STATE_DIR" "$PYTHON" - <<'PY'
import os
from pathlib import Path

def quote(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'

config = Path(os.environ['CONFIG_DIR']) / 'config.toml'
config.write_text(
    '[server]\n'
    f"site_url = {quote(os.environ['SITE_URL'])}\n"
    f"allow_insecure_http = {os.environ['ALLOW_HTTP']}\n\n"
    '[player]\n'
    f"machine_name = {quote(os.environ['MACHINE_NAME'])}\n"
    f"browser = {quote(os.environ['BROWSER'])}\n\n"
    '[paths]\n'
    'display = "/spip.php?page=affichage_ecran"\n'
    f"state = {quote(str(Path(os.environ['STATE_DIR']) / 'state.json'))}\n\n"
    '[intervals]\nconfiguration = 60\nheartbeat = 60\nactualisation = 60\nenrollment = 15\nrequest_timeout = 15\n'
    '[power]\n'
    f"rtcwake_enabled = {os.environ['RTCWAKE_ENABLED']}\n",
    encoding='utf-8',
)
config.chmod(0o600)
PY

if [[ "$RTCWAKE_ENABLED" == true ]]; then
    PLAYER_USER="$(id -un)"
    [[ "$PLAYER_USER" =~ ^[a-zA-Z0-9_-]+\$?$ ]] || die "Nom de compte Linux non compatible avec la règle sudoers générée."
    info "Installation du contrôle RTC à privilèges limités"
    sudo install -D -o root -g root -m 0755 "$PROJECT_DIR/deploy/power/scoralyx-player-rtcwake" /usr/local/sbin/scoralyx-player-rtcwake
    SUDOERS_TEMP="$(mktemp)"
    printf '%s ALL=(root) NOPASSWD: /usr/local/sbin/scoralyx-player-rtcwake *\n' "$PLAYER_USER" > "$SUDOERS_TEMP"
    if ! sudo visudo -cf "$SUDOERS_TEMP" >/dev/null; then
        rm -f "$SUDOERS_TEMP"
        die "La règle sudoers RTC est invalide."
    fi
    sudo install -o root -g root -m 0440 "$SUDOERS_TEMP" /etc/sudoers.d/scoralyx-player
    rm -f "$SUDOERS_TEMP"
elif command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
    sudo rm -f /etc/sudoers.d/scoralyx-player /usr/local/sbin/scoralyx-player-rtcwake
fi

cat > "$SYSTEMD_DIR/scoralyx-player.service" <<EOF
[Unit]
Description=Scoralyx Player
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
Environment=PATH=$DATA_DIR/venv/bin:/usr/bin:/bin
ExecStart=$DATA_DIR/venv/bin/scoralyx-player --config $CONFIG_DIR/config.toml run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical-session.target
EOF
chmod 600 "$SYSTEMD_DIR/scoralyx-player.service"

if systemctl --user daemon-reload >/dev/null 2>&1 && systemctl --user enable --now scoralyx-player.service >/dev/null 2>&1; then
    info "Service systemd activé"
else
    printf '\nLe service a été créé, mais systemd utilisateur n’est pas joignable dans cette session.\n'
    printf 'Après ouverture de la session graphique, exécute :\n  systemctl --user daemon-reload\n  systemctl --user enable --now scoralyx-player.service\n'
fi

cat <<EOF

Installation terminée.

Le Player va demander son enrôlement au serveur. Autorise-le et associe-le à un écran
dans l’administration Scoralyx. Le code d’appairage est visible avec :
  journalctl --user -u scoralyx-player.service -f

Configuration : $CONFIG_DIR/config.toml
État local protégé : $STATE_DIR/state.json
État du Player : $DATA_DIR/venv/bin/scoralyx-player --config $CONFIG_DIR/config.toml status

Le démarrage automatique nécessite une session graphique ouverte sur ce compte.
Mode RTC : $RTCWAKE_ENABLED
EOF
