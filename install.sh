#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
set -euo pipefail
PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
BUILD_DIR=${BUILD_DIR:-"$PROJECT_DIR/build"}
PLUGIN_ID=local.plasma.icontasks.endtask
PACKAGE_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/plasma/plasmoids"
BUILD_ONLY=0
RESTART=0
REPLACE_TASK_MANAGER=0

usage() {
    printf '%s\n' 'Usage: bash install.sh [--build-only] [--restart] [--replace-task-manager] [--help]' \
        '  --build-only            Build without installing or changing Plasma.' \
        '  --restart               Reload Plasma after installation (requires its systemd service).' \
        '  --replace-task-manager  Back up and replace original icons-only task managers in panels;' \
        '                          preserves settings/pins, reloads Plasma, requires Python 3 + systemd.' \
        'Optional variable: BUILD_DIR=/path/to/build-directory'
}
for argument in "$@"; do
    case "$argument" in
        --build-only) BUILD_ONLY=1 ;;
        --restart) RESTART=1 ;;
        --replace-task-manager) REPLACE_TASK_MANAGER=1 ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Unknown option: %s\n' "$argument" >&2; usage; exit 2 ;;
    esac
done
if (( BUILD_ONLY && REPLACE_TASK_MANAGER )); then
    printf '%s\n' '--build-only cannot be combined with --replace-task-manager.' >&2
    exit 2
fi
if (( EUID == 0 )); then
    printf 'Run this script as a regular user, without sudo.\n' >&2
    exit 1
fi
for command in cmake plasmashell kpackagetool6; do
    if ! command -v "$command" >/dev/null 2>&1; then
        printf 'Missing command: %s. See the requirements in README.md.\n' "$command" >&2
        exit 1
    fi
done
version=$(plasmashell --version 2>/dev/null)
if [[ ! "$version" =~ (^|[[:space:]])6\.(7|8)\.[0-9]+([[:space:]]|$) ]]; then
    printf 'Unsupported version: %s\nThis release requires Plasma 6.7.x or 6.8.x (verified on 6.7.5 and 6.8.1).\n' "$version" >&2
    exit 1
fi
if [[ "${XDG_SESSION_TYPE:-}" == x11 ]]; then
    printf 'Warning: this release was tested on Wayland, not X11.\n' >&2
fi
if (( REPLACE_TASK_MANAGER )); then
    # Fail before building/installing if automatic panel setup is unavailable.
    bash "$PROJECT_DIR/scripts/replace-task-manager.sh" --check
fi
cmake -S "$PROJECT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build "$BUILD_DIR" --parallel "${JOBS:-2}"
"$BUILD_DIR/bin/check-runtime"
if (( BUILD_ONLY )); then
    printf '\nPackage ready: %s/package\nThe installed widget has not been changed.\n' "$BUILD_DIR"
    exit 0
fi
mkdir -p "$PACKAGE_ROOT"
if [[ -d "$PACKAGE_ROOT/$PLUGIN_ID" ]]; then
    backup_root="${XDG_STATE_HOME:-$HOME/.local/state}/plasma-endtask/backups"
    mkdir -p "$backup_root"
    backup=$(mktemp -d "$backup_root/before-update-XXXXXX")
    cp -a -- "$PACKAGE_ROOT/$PLUGIN_ID" "$backup/"
    printf 'Previous widget backup: %s\n' "$backup"
    kpackagetool6 --type Plasma/Applet --packageroot "$PACKAGE_ROOT" --upgrade "$BUILD_DIR/package"
else
    kpackagetool6 --type Plasma/Applet --packageroot "$PACKAGE_ROOT" --install "$BUILD_DIR/package"
fi
printf '\nInstalled: %s/%s\n' "$PACKAGE_ROOT" "$PLUGIN_ID"
if (( REPLACE_TASK_MANAGER )); then
    bash "$PROJECT_DIR/scripts/replace-task-manager.sh"
else
    printf '%s\n' 'Enter Edit Mode → Add Widgets → search for “End Task”.' \
        'The original widget and your running applications are unchanged.' \
        'After an update, log out and back in, or use --restart.'
fi
if (( RESTART && ! REPLACE_TASK_MANAGER )); then
    if command -v systemctl >/dev/null 2>&1 && systemctl --user is-active --quiet plasma-plasmashell.service; then
        printf 'Reloading Plasma. Your applications will stay open.\n'
        systemctl --user restart plasma-plasmashell.service
    else
        printf 'The plasma-plasmashell service is not active: log out and back in to reload the widget.\n' >&2
    fi
fi
