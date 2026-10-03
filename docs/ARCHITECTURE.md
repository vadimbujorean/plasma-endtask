# Architecture and safety

## Repository layout

```text
package/                  Source KPackage: metadata, QML and configuration
src/support.cpp           Local QML plugin, KDE type loading and helper launch
src/endtask-helper.cpp    Confirmation dialog and pidfd-based termination
src/check-runtime.cpp     KDE runtime and pidfd checks before installation
install.sh                Per-user build, compatibility checks and installation
uninstall.sh              Removal of the custom widget only
CMakeLists.txt            Portable build using Qt6 targets
LICENSE, LICENSES/        License texts
tests/                    Isolated tests, excluded from the installed widget
docs/                     Guides and schematic preview
.github/workflows/        GitHub Actions static checks
```

`package/` contains no binaries or bundled logos. CMake copies it into
`build/package/`, adds the licenses, and builds the plugin and helper under
`contents/ui/support/`. Installation uses `kpackagetool6`, not direct copies
into system directories. Reconfiguration removes retired artwork and stale
license copies from the generated package.

## Why this depends on Plasma 6.7

In this Task Manager implementation, QML resources and native KDE types are
embedded in `plasma/applets/org.kde.plasma.taskmanager.so` under Qt's plugin
path. The local plugin loads that system library and reuses `Backend` and
`SmartLauncherItem`. The QML interface is a separate copy with its own ID:

```text
local.plasma.icontasks.endtask
```

Layout JavaScript files use local imports and recognize the new ID without
changing the original widget. The End Task action loads
`contents/icons/end-task-white.svg`, extracted from the menu preview. Its color
is fixed white and does not depend on the icon theme. The path is resolved
relative to the package; no user-specific absolute paths are needed.

This project uses internal KDE APIs and does **not** promise compatibility
with every Plasma version. Its resource baseline is Plasma 6.7.5.
`install.sh` accepts only 6.7.x; `check-runtime` verifies the native resource
layout and tests the required `pidfd` syscalls without terminating anything.

## Termination flow

1. `ContextMenu.qml` collects the window's PID, or the PIDs of grouped child
   windows, rejecting invalid values and removing duplicates.
2. `ProcessController` filters the arguments again and starts the helper
   with `QProcess::startDetached`: no shell, `pkill` or `killall` is used.
3. The helper opens `pidfd` handles and checks process ownership, availability
   and protected names.
4. A separate dialog lists the processes. Closing the taskbar menu does not
   destroy the pending request. **Cancel** is the default button; Escape cancels.
5. Only after confirmation does the helper send SIGKILL through the handles
   and close them. Reusing a PID does not change the signal's destination.
6. KWin updates the window model naturally. No extra Close request is sent
   that might act on a different window after the model changes.

## Guarantees and limitations

- No sudo, privilege escalation or access to other users' processes.
- PID ≤ 1, the widget's host process and the helper itself are excluded.
- Processes named `plasmashell`, `kwin_wayland` and `kwin_x11` are excluded.
- Name checks are an additional safeguard, not an absolute sandbox. Renamed
  processes and other session components are not all automatically protected.
- Remote apps, sandboxed apps or clients without a valid PID may make the
  action unavailable.
- Signals target the selected processes, not their entire child-process trees.
- Windows sharing a PID share a process, so all of them can be affected.
- SIGKILL gives the app no opportunity to save, clean up or show its own prompt.

For testing, the helper offers `--check PID...`: it prints eligible candidates
without showing confirmation or sending termination signals. Normal termination
has no option to skip confirmation. Dialog automation belongs only to the test
suite and is not installed with the widget.

## Installation paths

```text
${XDG_DATA_HOME:-~/.local/share}/plasma/plasmoids/local.plasma.icontasks.endtask/
```

Upgrade backups:

```text
${XDG_STATE_HOME:-~/.local/state}/plasma-endtask/backups/
```

Panels and `plasma-org.kde.plasma.desktop-appletsrc` are not changed automatically.
Normal installation does not restart Plasma; `--restart` is an explicit choice.
