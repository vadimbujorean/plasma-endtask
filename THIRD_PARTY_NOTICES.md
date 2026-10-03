# Third-party notices

## KDE Icons-Only Task Manager

The QML, JavaScript and configuration files under `package/contents/` are
derived from KDE Plasma Desktop's Task Manager. Baseline: Plasma Desktop
6.7.5 resources. The files retain their original SPDX notices and copyrights,
including those of Eike Hein, Kai Uwe Broulik and the other authors listed
in individual files.

License: **GPL-2.0-or-later**. Local code uses the same license.
The GPL v2 text is included in `LICENSE` and `LICENSES/GPL-2.0-or-later.txt`.

Original sources:
https://invent.kde.org/plasma/plasma-desktop/-/tree/Plasma/6.7/applets/taskmanager

Main changes: a separate widget ID, icons-only behavior, local JavaScript
imports, an End Task action and a local support module. The native KDE library
is loaded from the user's system, not copied or redistributed in this repository.

## Icons and preview

The End Task icon in `package/contents/icons/end-task.svg` is extracted from
this project's schematic preview in `docs/menu-preview.svg`. Both use simple
geometric shapes and are licensed under GPL-2.0-or-later. The icon uses the
system's KF6 IconThemes library to follow the application text palette; that
library is a system dependency and is not bundled. No third-party logos are
bundled. Close requests the standard `window-close` icon from the user's desktop
theme; that theme's files are not redistributed here.

This is an independent project. It does not imply affiliation with or
endorsement by KDE. Trademarks remain the property of their respective owners.
