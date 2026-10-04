# Plasma End Task

**An “End Task” action in the right-click menu of KDE Plasma's taskbar icons.**

A separate version of **Icons-Only Task Manager** with force-quit support and
a safety confirmation. **End Task appears immediately above Close**, using
the geometric stop icon shown in the preview. Its color follows the menu's
text palette: light on dark themes, dark on light themes, and the text color
of custom schemes. No third-party logos are bundled.

![Schematic dark-theme menu preview](docs/menu-preview.svg)

> **Compatibility:** Linux + KDE Plasma **6.7.x**. Tested on Plasma **6.7.5**,
> Qt **6.11.2**, **Wayland**, Arch Linux/CachyOS.
> Plasma 5 and Plasma 6.0–6.6 are **not supported** by this release.
> X11 and other Plasma 6.7 patch releases have not been verified.
>
> ⚠️ Force-quitting uses **SIGKILL**: unsaved data will be lost.
> **Close** still requests a normal, graceful shutdown.

## Features

- Adds **End Task** above **Close**, without replacing it.
- Shows process names and PIDs before proceeding; **Cancel** is the default button.
- Collects and deduplicates the PIDs of windows in grouped taskbar icons.
- Uses `pidfd` to avoid targeting a different process if a PID is reused.
- Excludes other users' processes, system PIDs and protected Plasma/KWin processes.
- Installs **for the current user only**, without changing files in `/usr`.
- Leaves your panel unchanged by default; optional automatic replacement preserves settings and pinned apps.
- Never changes or uninstalls the original KDE widget's files.
- Uses the preview's End Task symbol and adapts its color to the desktop text palette.
- Refreshes an open menu's icon when the application palette changes.

The action is shown for running apps with windows, not launcher-only entries.
It is disabled when a suitable PID is unavailable. The project's action,
confirmation dialog, scripts and documentation are in English; standard KDE
labels may follow your desktop's language settings.

## 1. Requirements

- Linux kernel **5.3 or later**, an accessible `/proc`, and working `pidfd` support.
- KDE Plasma Desktop **6.7.x**, including its native Task Manager library.
- Qt6 development files for **Core, Qml and Widgets**, Qt tools (`moc`),
  and the desktop's icon-rendering plugins.
- **KF6 IconThemes** development files for palette-aware SVG rendering.
- A C++17 compiler (GCC or Clang), CMake ≥ 3.21, and Make/Ninja.
- `kpackagetool6`, `plasmashell`, Bash; Git if cloning the repository.
- Python 3 for tests and the optional `--replace-task-manager` mode.
- An active `plasma-plasmashell.service` user service for automatic panel replacement.

### Arch Linux / CachyOS

On an up-to-date system already running the supported Plasma version:

```bash
sudo pacman -S --needed base-devel cmake git qt6-base qt6-declarative qt6-svg kiconthemes plasma-desktop plasma-workspace
```

Check your version first:

```bash
plasmashell --version
```

On other distributions, install the equivalent packages using your package
manager. **Installing Qt6 alone does not make Plasma 5 or 6.6 compatible.**
The installer rejects unsupported Plasma versions and checks KDE's native
resource layout and the kernel's `pidfd` support.

## 2. Download

### Using Git

```bash
git clone https://github.com/vadimbujorean/plasma-endtask.git
cd plasma-endtask
```

### Without Git

On the repository page, select **Code → Download ZIP**, extract the archive,
and open a terminal in the extracted directory. Do not run scripts from
inside an archive viewer.

## 3. Build and install

From the project directory, **as a regular user, without sudo**:

```bash
bash install.sh
```

The script checks Plasma, builds the C++ components, verifies the KDE runtime
and installs the widget for your user. It does not download dependencies or run
remote commands. By default, it does not restart Plasma or modify your panel.

To install and immediately reload Plasma **on systems using its systemd service**:

```bash
bash install.sh --restart
```

The panel may disappear briefly; your other applications stay open.
On other systems, log out and back in after updating the widget.

### Build without installing

```bash
bash install.sh --build-only
```

The compiled package is in `build/package/`. The GitHub source archive is
**not a precompiled `.plasmoid`**: build it on the destination system using
that system's Qt6 libraries.

## 4. Add it to your taskbar

### Automatic setup (skip the manual steps)

Instead of the normal install command, run:

```bash
bash install.sh --replace-task-manager
```

This installs the widget and replaces **all original Icons-Only Task Managers
in KDE panels** with **Icons-Only Task Manager — End Task**. It changes only
the plugin ID of each existing widget, preserving its widget ID, panel position,
settings and pinned apps. It does not add a second taskbar, change desktop widgets
or replace the non-icons-only Task Manager. KDE's original widget stays installed.

**Requires Python 3 and an active `plasma-plasmashell.service` user service.**
Plasma stops briefly to save its latest configuration, then the script backs up
`${XDG_CONFIG_HOME:-~/.config}/plasma-org.kde.plasma.desktop-appletsrc`, changes
the plugin IDs and starts Plasma again. Other applications stay open. The backup
path is printed and saved under:

```text
${XDG_STATE_HOME:-~/.local/state}/plasma-endtask/backups/before-panel-replacement-*/
```

If editing or starting Plasma fails, the script attempts to restore the backup
and start Plasma again. Keep the backup for recovery; see
[Troubleshooting](docs/TROUBLESHOOTING.md#automatic-panel-replacement).
The installed package is not rolled back if panel setup fails.

You can repeat the command safely: widgets already using End Task are not
changed. If no original icons-only task manager exists in any panel, nothing is
added; use the manual steps below. `--restart` is redundant in this mode, and
`--build-only` cannot be combined with it. On systems without the active service,
use manual setup instead.

### Manual setup (default)

1. Right-click the panel → **Enter Edit Mode**.
2. Select **Add Widgets**.
3. Search for **End Task**.
4. Add **Icons-Only Task Manager — End Task** to the panel.
5. Verify that it works, then optionally remove the previous icons-only task
   manager from the panel to avoid having two taskbars. **Do not uninstall
   the original KDE widget.**

When added manually, the new widget has separate settings and may require
pinning your apps again; the original widget keeps its own configuration.
Automatic replacement reuses the existing configuration instead.

Right-click a running app's icon → **End Task** → check the process names and
PIDs → confirm or cancel.

**Important:** termination targets processes, not just the selected window.
All windows belonging to the same process can close, including windows on
other desktops. Child processes are not automatically terminated as a tree.

## Update

```bash
git pull --ff-only
bash install.sh --restart
```

Without the systemd service, omit `--restart` and log out and back in instead.
Before upgrading an existing installation, the installer saves a copy under:

```text
${XDG_STATE_HOME:-~/.local/state}/plasma-endtask/backups/
```

The included copy of KDE's widget does not automatically track upstream
Plasma updates. Major Plasma/Qt changes may require a new project release
or a rebuild; compatibility is intentionally limited.

## Uninstall

First remove the custom widget from your panel and add KDE's original
**Icons-Only Task Manager** again. Then run:

```bash
bash uninstall.sh
```

The script asks for confirmation and removes **only**
`local.plasma.icontasks.endtask`. Source files, backups and the original
widget are not deleted.

## Tests and development

```bash
cmake -S . -B build-tests -DBUILD_TESTING=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build build-tests --parallel 2
ctest --test-dir build-tests --output-on-failure
```

Panel replacement tests use temporary configuration files and mocked systemd
commands: **your real panel and Plasma service are never modified by tests**.
Run them independently without KDE:

```bash
python3 tests/panel-replacement.py
```

Tests check automatic replacement, pinned-app/settings preservation, rollback,
installer flags, the source package, English metadata and preview, menu ordering,
the SVG's match to the preview, live dark/light/custom menu-icon recoloring,
QML compilation
and helper behavior on disposable
`sleep` processes. Cancellation and actual SIGKILL are tested only on those
processes: **no real user application is terminated**. Full tests require the
supported KDE runtime. GitHub CI runs static checks without starting KDE.

- [Architecture and safety](docs/ARCHITECTURE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Third-party credits and licenses](THIRD_PARTY_NOTICES.md)

## License

Code and widget: **GPL-2.0-or-later**. Original KDE notices are preserved;
see [LICENSE](LICENSE), [LICENSES/](LICENSES/) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
This is an independent project, not an official KDE product.
