#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
PLUGIN_ID=local.plasma.icontasks.endtask
PACKAGE_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/plasma/plasmoids"
YES=0
for argument in "$@"; do
    case "$argument" in
        --yes) YES=1 ;;
        --help|-h) printf 'Usage: bash uninstall.sh [--yes]\nFirst remove the custom widget from your panel and restore the original KDE widget.\n'; exit 0 ;;
        *) printf 'Unknown option: %s\n' "$argument" >&2; exit 2 ;;
    esac
done
if (( EUID == 0 )); then
    printf 'Run as a regular user, without sudo.\n' >&2
    exit 1
fi
if [[ ! -d "$PACKAGE_ROOT/$PLUGIN_ID" ]]; then
    printf 'The custom widget is not installed.\n'
    exit 0
fi
command -v kpackagetool6 >/dev/null || { printf 'kpackagetool6 is unavailable.\n' >&2; exit 1; }
if (( ! YES )); then
    printf '%s\n' 'First remove the custom widget from your panel and add the original KDE widget.'
    read -r -p 'Uninstall only the custom widget? [y/N] ' answer
    [[ "$answer" == y || "$answer" == Y ]] || exit 0
fi
kpackagetool6 --type Plasma/Applet --packageroot "$PACKAGE_ROOT" --remove "$PLUGIN_ID"
printf '%s\n' 'Custom widget removed. KDE widgets, source files and backups have not been deleted.'
