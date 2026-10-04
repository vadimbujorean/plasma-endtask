#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Change only task-manager plugin entries; the caller must stop Plasma first."""
import argparse
import os
from pathlib import Path
import re
import stat
import tempfile

ORIGINAL = b'org.kde.plasma.icontasks'
CUSTOM = b'local.plasma.icontasks.endtask'
HEADER = re.compile(rb'(?:\[[^\[\]\r\n]+\])+')
PLUGIN = re.compile(rb'([ \t]*plugin[ \t]*=[ \t]*)([^ \t\r\n]+)([ \t]*(?:\r?\n)?)')


def replace_plugins(data):
    """Preserve all bytes except plugin IDs in direct applets of KDE panels."""
    if b'[$i]' in data:
        raise ValueError('Immutable KConfig entries found; use manual widget setup instead.')
    lines = data.splitlines(keepends=True)
    group = ()
    plugins = {}
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(b'['):
            if not HEADER.fullmatch(stripped):
                raise ValueError('Unrecognized KConfig group header; configuration was not changed.')
            group = tuple(re.findall(rb'\[([^\[\]]+)\]', stripped))
            continue
        match = PLUGIN.fullmatch(line)
        if match:
            if group in plugins:
                raise ValueError('Duplicate plugin entry; configuration was not changed.')
            plugins[group] = (index, match)
    panels = {
        group[1] for group, (_, match) in plugins.items()
        if len(group) == 2 and group[0] == b'Containments' and match[2] == b'org.kde.panel'
    }
    replaced = []
    for group, (index, match) in plugins.items():
        if (len(group) == 4 and group[0] == b'Containments' and group[1] in panels
                and group[2] == b'Applets' and group[1].isdigit() and group[3].isdigit()
                and match[2] == ORIGINAL):
            lines[index] = match[1] + CUSTOM + match[3]
            replaced.append((group[1].decode('ascii'), group[3].decode('ascii')))
    return b''.join(lines), replaced


def update_config(path, check_only=False):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError('Panel configuration must be a regular file owned by the current user (not a symlink).')
    data = path.read_bytes()
    updated, replaced = replace_plugins(data)
    if not check_only and replaced:
        # Write atomically in the same directory; do not rewrite unrelated settings.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.endtask-', delete=False) as stream:
                temporary = Path(stream.name)
                os.fchmod(stream.fileno(), stat.S_IMODE(info.st_mode))
                stream.write(updated)
                stream.flush()
                os.fsync(stream.fileno())
            current = path.lstat()
            if (current.st_ino != info.st_ino or current.st_mtime_ns != info.st_mtime_ns
                    or path.read_bytes() != data):
                raise ValueError('Panel configuration changed concurrently; refusing to overwrite it.')
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return replaced


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate without writing anything.')
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    try:
        replaced = update_config(args.config, args.check)
    except (OSError, ValueError) as error:
        parser.exit(1, f'Panel replacement failed: {error}\n')
    if not args.check:
        for panel, applet in replaced:
            print(f'Replaced Icons-Only Task Manager: panel {panel}, widget {applet}.')
        if not replaced:
            print('No original Icons-Only Task Manager found in panels; configuration unchanged.')


if __name__ == '__main__':
    main()
