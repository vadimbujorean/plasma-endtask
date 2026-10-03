# Troubleshooting

## Unsupported version

Check `plasmashell --version`. This release uses Plasma 6.7 resources/APIs;
it does not support Plasma 5 or Plasma 6.0–6.6. Do not bypass the check by
editing metadata alone: native types or the QML layout may be different.

## Missing Qt6, compiler or CMake

Install the development dependencies listed in the README. Package names
vary by distribution. You need Qt6 Core/Qml/Widgets, Qt6 tools (`moc`), the
desktop's icon-rendering plugins, a C++17 compiler and CMake ≥ 3.21.

## Non-fatal build warnings

Qt6's warning about the deprecation of `QQmlExtensionPlugin::baseUrl()` is not
an error: the function is available in the verified Qt6 version.
`Could NOT find WrapVulkanHeaders` also does not prevent this widget from building.
A nonzero installer exit status or an actual CMake/C++ error needs investigation.

## Native Task Manager unavailable

`plasma-desktop` and its Qt libraries must come from the same compatible
installation. `check-runtime` prints the plugin path it uses. Check for
custom `QT_PLUGIN_PATH` settings or alternative Qt installations; do not mix
libraries from incompatible distributions or versions.

## The widget does not appear in Add Widgets

Check the installation:

```bash
kpackagetool6 --type Plasma/Applet --show local.plasma.icontasks.endtask
```

Search for **End Task** in **Add Widgets**. If necessary, log out and back in.
On systems with the matching systemd service, reload the desktop/panel with:

```bash
systemctl --user restart plasma-plasmashell.service
```

This does not close ordinary applications. If you use a custom `XDG_DATA_HOME`,
check the path printed by `install.sh`. Do not install using sudo or another user.

## The menu still shows an older version

Make sure you are using the widget with **End Task in its name**, not KDE's
original widget. Plasma caches QML and loaded libraries: reload Plasma or log
out and back in after an update. Do not rebuild a library directly into the
installed location while it is in use.

## Two taskbars or missing pinned apps

Adding the new widget does not remove the original. After verifying the new
widget, you can remove the original from the panel and pin apps in the new one.
The widgets have separate settings. This project does not automatically copy
or delete panel configuration.

## Missing icon

End Task uses the bundled `contents/icons/end-task-white.svg`; Close uses the
`window-close` theme icon. Check that the SVG exists in the installed package
and that Qt's SVG plugin is installed (on Arch: `qt6-svg`), then reinstall and
reload Plasma. The End Task symbol is intentionally fixed white; it can have
low contrast on very light menus. Only the Close icon follows the icon theme.

## Disabled action or no eligible process

The window must expose a valid PID through KDE's model. Some remote apps,
sandboxed apps and special windows may not provide one. Launcher-only entries
do not show the action. The app may have exited between the click and the
confirmation. Plasma and KWin are deliberately excluded.

## Multiple windows close together

This is expected: SIGKILL targets a process, not a single window. Windows in
the same process share its fate, including windows on other desktops. A group
may contain several PIDs, all of which are listed in the confirmation.

## A standalone test cannot see windows

On Wayland, KWin limits PlasmaWindowManagement to authorized clients.
An arbitrary test program may see zero windows; the panel widget runs inside
`plasmashell`, which is authorized. Do not weaken KWin's security rules just
to make a test pass.

## The widget breaks after a Plasma update

Restore KDE's original task manager in the panel. This project uses internal
APIs and does not automatically track upstream changes. Rebuild on a supported
version or wait for a compatible project release. When reporting a bug, include
Plasma/Qt versions, distribution, Wayland/X11 and the error message, without
personal data.
