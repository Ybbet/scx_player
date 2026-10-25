#!/usr/bin/env bash
set -Eeuo pipefail

# Configure les prérequis de session couramment utilisés par un kiosque Scoralyx.
# Les réglages de session sont appliqués au démarrage graphique via --apply-session.

SCRIPT_PATH="$(readlink -f -- "${BASH_SOURCE[0]}")"
PLAYER_USER="${SUDO_USER:-${USER:-$(id -un)}}"
MODE="configure"

usage() {
    cat <<'EOF'
Usage : configure-digital-signage.sh [--check | --configure | --apply-session] [--user NOM]

  --check          Afficher les capacités détectées sans rien modifier.
  --configure      Configurer l'ouverture de session automatique et le bureau.
  --apply-session  Appliquer les réglages de veille dans la session graphique active.
  --user NOM       Compte Linux qui ouvre la session graphique.
EOF
}

while (($#)); do
    case "$1" in
        --check) MODE=check ;;
        --configure) MODE=configure ;;
        --apply-session) MODE=apply-session ;;
        --user)
            (($# >= 2)) || { usage >&2; exit 2; }
            PLAYER_USER="$2"
            shift
            ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; exit 2 ;;
    esac
    shift
done

failures=0
note() { printf '%s\n' "$*"; }
warn() { printf 'À vérifier : %s\n' "$*" >&2; failures=$((failures + 1)); }
as_root() { if [[ $EUID -eq 0 ]]; then "$@"; else sudo "$@"; fi; }

[[ "$PLAYER_USER" =~ ^[a-zA-Z0-9_.-]+\$?$ ]] || { echo "Nom de compte Linux invalide." >&2; exit 2; }
PLAYER_HOME="$(getent passwd "$PLAYER_USER" | cut -d: -f6)"
[[ -n "$PLAYER_HOME" && -d "$PLAYER_HOME" ]] || { echo "Compte ou répertoire personnel introuvable : $PLAYER_USER" >&2; exit 2; }

detect_display_manager() {
    local dm=""
    if [[ -r /etc/X11/default-display-manager ]]; then
        dm="$(basename "$(< /etc/X11/default-display-manager)")"
    fi
    if [[ -z "$dm" ]] && command -v systemctl >/dev/null 2>&1; then
        dm="$(systemctl show -p FragmentPath --value display-manager.service 2>/dev/null | head -n1)"
        [[ -n "$dm" ]] && dm="$(basename "$dm")"
        dm="${dm%.service}"
    fi
    case "$dm" in
        gdm|gdm3) printf 'gdm3' ;;
        lightdm) printf 'lightdm' ;;
        sddm) printf 'sddm' ;;
        *) printf '%s' "${dm:-inconnu}" ;;
    esac
}

DM="$(detect_display_manager)"
DESKTOP="${XDG_CURRENT_DESKTOP:-${XDG_SESSION_DESKTOP:-${DESKTOP_SESSION:-}}}"
if [[ -z "$DESKTOP" ]]; then
    if pgrep -u "$PLAYER_USER" -x gnome-shell >/dev/null 2>&1; then DESKTOP=GNOME
    elif pgrep -u "$PLAYER_USER" -x xfce4-session >/dev/null 2>&1; then DESKTOP=XFCE
    elif pgrep -u "$PLAYER_USER" -x plasmashell >/dev/null 2>&1; then DESKTOP=KDE
    else DESKTOP=indéterminé
    fi
fi

check_report() {
    note "Compte graphique : $PLAYER_USER ($PLAYER_HOME)"
    note "Gestionnaire de connexion détecté : $DM"
    note "Environnement de bureau courant : $DESKTOP"
    if command -v chromium >/dev/null 2>&1 || command -v chromium-browser >/dev/null 2>&1 || command -v google-chrome >/dev/null 2>&1; then
        note "Navigateur Chromium : présent"
    else
        warn "Chromium n'est pas détecté dans le PATH."
    fi
    if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
        note "Session graphique : active"
    else
        note "Session graphique : non détectée depuis ce terminal"
    fi
    case "$DM" in
        gdm3)
            local gdm_config=/etc/gdm3/daemon.conf
            [[ -e "$gdm_config" ]] || gdm_config=/etc/gdm3/custom.conf
            if grep -Eiq '^\s*AutomaticLoginEnable\s*=\s*(true|yes)' "$gdm_config" 2>/dev/null && grep -Eiq "^\\s*AutomaticLogin\\s*=\\s*${PLAYER_USER}\\s*$" "$gdm_config" 2>/dev/null; then
                note "Ouverture automatique : configurée pour $PLAYER_USER"
            else
                warn "Ouverture automatique GDM à configurer pour $PLAYER_USER."
            fi
            ;;
        lightdm)
            if grep -Eiq "^autologin-user=${PLAYER_USER}$" /etc/lightdm/lightdm.conf.d/50-scoralyx-player.conf 2>/dev/null; then note "Ouverture automatique : configurée pour $PLAYER_USER"; else warn "Ouverture automatique LightDM à configurer pour $PLAYER_USER."; fi
            ;;
        sddm)
            if grep -Eiq "^User=${PLAYER_USER}$" /etc/sddm.conf.d/50-scoralyx-player.conf 2>/dev/null; then note "Ouverture automatique : configurée pour $PLAYER_USER"; else warn "Ouverture automatique SDDM à configurer pour $PLAYER_USER."; fi
            ;;
        *) warn "Ouverture automatique non configurée automatiquement pour ce gestionnaire ($DM)." ;;
    esac
    case "$DESKTOP" in
        *GNOME*|*gnome*)
            if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]] && command -v gsettings >/dev/null 2>&1 && [[ "$(id -un)" == "$PLAYER_USER" ]]; then
                local idle lock power
                idle="$(gsettings get org.gnome.desktop.session idle-delay 2>/dev/null || true)"
                lock="$(gsettings get org.gnome.desktop.screensaver lock-enabled 2>/dev/null || true)"
                power="$(gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 2>/dev/null || true)"
                if [[ "$idle" == "uint32 0" && "$lock" == "false" && "$power" == "'nothing'" ]]; then note "Veille et verrouillage GNOME : désactivés"; else warn "Réglages de veille GNOME à appliquer (idle=$idle, lock=$lock, sleep=$power)."; fi
            else
                note "Réglages GNOME : diagnostic détaillé disponible depuis la session graphique"
            fi
            ;;
        *)
            if [[ "$DESKTOP" == "indéterminé" ]]; then note "Environnement de bureau non détecté ; impossible de vérifier la veille depuis ce terminal."
            else warn "La désactivation automatique de la veille n'est prise en charge que pour GNOME (bureau détecté : $DESKTOP)."
            fi
            ;;
    esac
}

write_autologin() {
    local target="$1" user="$2" tmp
    as_root python3 - "$target" "$user" <<'PY'
from pathlib import Path
import os, stat, sys, tempfile, time

path = Path(sys.argv[1])
user = sys.argv[2]
path.parent.mkdir(parents=True, exist_ok=True)
old = path.read_text(encoding="utf-8") if path.exists() else ""
if path.exists():
    backup = path.with_name(path.name + ".scoralyx-backup-" + time.strftime("%Y%m%d%H%M%S"))
    backup.write_text(old, encoding="utf-8")

if path.parent.name == "gdm3":
    lines = old.splitlines()
    output, in_daemon, found = [], False, False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_daemon and not found:
                output += ["AutomaticLoginEnable=True", f"AutomaticLogin={user}"]
                found = True
            in_daemon = stripped.lower() == "[daemon]"
        if in_daemon and stripped.split("=", 1)[0].strip().lower() in {"automaticloginenable", "automaticlogin"}:
            continue
        output.append(line)
    if in_daemon and not found:
        output += ["AutomaticLoginEnable=True", f"AutomaticLogin={user}"]
        found = True
    if not found:
        if output and output[-1].strip(): output.append("")
        output += ["[daemon]", "AutomaticLoginEnable=True", f"AutomaticLogin={user}"]
    content = "\n".join(output).rstrip() + "\n"
else:
    if path.name == "50-scoralyx-player.conf":
        content = "[Autologin]\nUser=" + user + "\n"
    else:
        content = "[Seat:*]\nautologin-user=" + user + "\nautologin-user-timeout=0\n"

mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
with os.fdopen(fd, "w", encoding="utf-8") as f: f.write(content)
os.chmod(name, mode)
os.replace(name, path)
PY
}

install_autostart() {
    local helper="$1" desktop_dir="$PLAYER_HOME/.config/autostart"
    local group
    group="$(id -gn "$PLAYER_USER")"
    as_root install -d -o "$PLAYER_USER" -g "$group" -m 0755 "$desktop_dir" "$PLAYER_HOME/.local/share/scoralyx-player"
    as_root install -o "$PLAYER_USER" -g "$group" -m 0755 "$helper" "$PLAYER_HOME/.local/share/scoralyx-player/configure-digital-signage.sh"
    local installed="$PLAYER_HOME/.local/share/scoralyx-player/configure-digital-signage.sh"
    as_root tee "$desktop_dir/scoralyx-player-display-setup.desktop" >/dev/null <<EOF
[Desktop Entry]
Type=Application
Name=Scoralyx Player — réglages d’affichage
Comment=Désactiver la veille et le verrouillage de session pour l’affichage kiosque
Exec="$installed" --apply-session
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF
    as_root chown "$PLAYER_USER:$group" "$desktop_dir/scoralyx-player-display-setup.desktop"
}

apply_gnome_session() {
    command -v gsettings >/dev/null 2>&1 || { warn "gsettings est absent dans la session GNOME."; return; }
    local schema key value
    while IFS='|' read -r schema key value; do
        [[ -n "$schema" ]] || continue
        if gsettings list-schemas | grep -Fxq "$schema"; then
            gsettings set "$schema" "$key" "$value" || warn "Impossible d'appliquer $schema $key."
        else
            warn "Schéma GNOME absent : $schema."
        fi
    done <<'EOF'
org.gnome.desktop.session|idle-delay|uint32 0
org.gnome.desktop.screensaver|lock-enabled|false
org.gnome.desktop.screensaver|idle-activation-enabled|false
org.gnome.settings-daemon.plugins.power|sleep-inactive-ac-type|'nothing'
org.gnome.settings-daemon.plugins.power|sleep-inactive-battery-type|'nothing'
org.gnome.settings-daemon.plugins.power|idle-dim|false
EOF
    note "Réglages GNOME appliqués : veille et verrouillage désactivés."
}

case "$MODE" in
    check)
        check_report
        (( failures == 0 ))
        ;;
    apply-session)
        case "$DESKTOP" in
            *GNOME*|*gnome*) apply_gnome_session ;;
            *) warn "Environnement '$DESKTOP' non pris en charge pour la désactivation automatique de la veille ; aucun réglage n'a été modifié." ;;
        esac
        (( failures == 0 ))
        ;;
    configure)
        check_report
        failures=0
        printf '\nLa connexion automatique ouvre la session sans demander de mot de passe à chaque démarrage.\n'
        read -r -p "Configurer l’ouverture automatique et la désactivation de la veille pour $PLAYER_USER ? [O/n] " answer
        if [[ "$answer" =~ ^[nN]$ ]]; then
            note "Aucun réglage système n'a été modifié."
            exit 0
        fi
        if [[ $EUID -ne 0 ]]; then command -v sudo >/dev/null 2>&1 || { echo "sudo est requis pour configurer l’ouverture automatique." >&2; exit 1; }; fi
        case "$DM" in
            gdm3)
                target=/etc/gdm3/daemon.conf
                [[ -e "$target" ]] || target=/etc/gdm3/custom.conf
                write_autologin "$target" "$PLAYER_USER"
                note "Ouverture automatique configurée dans $target (effective au prochain démarrage)."
                ;;
            lightdm)
                write_autologin /etc/lightdm/lightdm.conf.d/50-scoralyx-player.conf "$PLAYER_USER"
                note "Ouverture automatique configurée pour LightDM (effective au prochain démarrage)."
                ;;
            sddm)
                write_autologin /etc/sddm.conf.d/50-scoralyx-player.conf "$PLAYER_USER"
                note "Ouverture automatique configurée pour SDDM (effective au prochain démarrage)."
                ;;
            *) warn "Gestionnaire '$DM' non pris en charge : ouverture automatique à configurer manuellement." ;;
        esac
        install_autostart "$SCRIPT_PATH"
        case "$DESKTOP" in
            *GNOME*|*gnome*)
                if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" && "$(id -un)" == "$PLAYER_USER" ]]; then apply_gnome_session
                else note "Les réglages GNOME seront appliqués à la prochaine ouverture de session graphique."; fi
                ;;
            *) warn "Le bureau détecté ('$DESKTOP') n'est pas pris en charge pour la désactivation automatique de la veille ; le script autonome devra être adapté à cet environnement." ;;
        esac
        note "Configuration Digital Signage terminée. Redémarrer le mini-PC pour valider l’ouverture automatique."
        (( failures == 0 ))
        ;;
esac
