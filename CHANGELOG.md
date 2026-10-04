# Changelog

## Unreleased

- Add optional `install.sh --replace-task-manager` automatic panel setup.
- Preserve widget IDs, panel order, settings and pinned apps by changing only plugin IDs.
- Back up the synchronized panel configuration while Plasma is stopped, with recovery on failure.
- Document automatic setup, requirements and manual backup restoration.
- Test configuration changes, installer flags and rollback using mocked systemd commands.

## 1.3.0

- Make the End Task symbol follow the application's text palette instead of fixed white.
- Recolor the symbolic SVG through KF6 IconThemes and refresh it on live palette changes.
- Add KF6 IconThemes as an explicit build dependency.
- Test dark, light, custom and repeated palette changes on the same KDE menu item.
- Rename the bundled icon to `end-task.svg` and update theme documentation.

## 1.2.1

- Use the white geometric End Task icon extracted from the menu preview.
- Keep the End Task icon white instead of inheriting the theme's destructive color.
- Verify that the bundled SVG matches the preview and renders white in a KDE menu item.
- Update icon documentation and keep all artwork under GPL-2.0-or-later.

## 1.2.0

- Removed bundled branding and switched to the standard KDE stop icon.
- Translated all documentation, metadata, scripts and custom UI messages to English.
- Replaced the menu illustration with an English, unbranded schematic preview.
- Simplified licensing notices to the remaining GPL-2.0-or-later components.
- Added checks for English metadata/preview and the standard theme icon.
- Removed retired artwork and stale license copies from reused build directories.

## 1.1.0

- Initial source package.
- Separate widget based on Plasma 6.7.5's Task Manager.
- End Task action above Close.
- External confirmation, deduplicated grouped PIDs and pidfd-based termination.
- CMake build and per-user installation/uninstallation scripts.
- Compatibility checks, upgrade backups and optional Plasma reload.
- Usage, development and troubleshooting guides.
- Preserved upstream notices, isolated tests and static CI checks.
