#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/plasma-org.kde.plasma.desktop-appletsrc"
SERVICE=plasma-plasmashell.service
CHECK_ONLY=0
case "${1:-}" in
    --check) CHECK_ONLY=1 ;;
    '') ;;
    *) printf 'Usage: bash scripts/replace-task-manager.sh [--check]\n' >&2; exit 2 ;;
esac
(( $# <= 1 )) || exit 2
if (( EUID == 0 )); then
    printf 'Run as a regular user, without sudo.\n' >&2
    exit 1
fi
for command in python3 systemctl; do
    command -v "$command" >/dev/null 2>&1 || {
        printf 'Automatic replacement requires %s. Use manual widget setup instead.\n' "$command" >&2
        exit 1
    }
done
if ! systemctl --user is-active --quiet "$SERVICE"; then
    printf 'Automatic replacement requires an active %s user service. Use manual widget setup instead.\n' "$SERVICE" >&2
    exit 1
fi
python3 "$SCRIPT_DIR/panel-config.py" --check "$CONFIG"
(( ! CHECK_ONLY )) || exit 0

backup_root="${XDG_STATE_HOME:-$HOME/.local/state}/plasma-endtask/backups"
mkdir -p -- "$backup_root"
backup=$(mktemp -d "$backup_root/before-panel-replacement-XXXXXX")
stop_requested=0
backup_ready=0
recover() {
    local status=$?
    trap - EXIT INT TERM
    if (( stop_requested )); then
        if (( backup_ready )); then
            # A failed start may have partially launched Plasma. Stop it again
            # before restoring the synchronized configuration.
            if systemctl --user stop "$SERVICE"; then
                cp -a -- "$backup/plasma-org.kde.plasma.desktop-appletsrc" "$CONFIG" || {
                    printf 'Could not restore panel configuration. Backup: %s\n' "$backup" >&2
                }
            else
                printf 'Could not stop Plasma for rollback. Restore the backup manually: %s\n' "$backup" >&2
            fi
        fi
        systemctl --user start "$SERVICE" || printf 'Could not start Plasma. Run: systemctl --user start %s\n' "$SERVICE" >&2
    fi
    exit "$status"
}
trap recover EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
printf 'Temporarily stopping Plasma to preserve widget settings and pinned apps. Other applications stay open.\n'
stop_requested=1
systemctl --user stop "$SERVICE"
# Plasma saves its current in-memory layout on shutdown: back up that version,
# not a potentially stale file copied while the shell was still running.
cp -a -- "$CONFIG" "$backup/plasma-org.kde.plasma.desktop-appletsrc"
backup_ready=1
printf 'Panel configuration backup: %s/plasma-org.kde.plasma.desktop-appletsrc\n' "$backup"
python3 "$SCRIPT_DIR/panel-config.py" "$CONFIG"
systemctl --user start "$SERVICE"
stop_requested=0
trap - EXIT INT TERM
printf 'Plasma reloaded. Original KDE widget files have not been changed or uninstalled.\n'
