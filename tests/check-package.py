#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Static checks; usable without KDE or Qt."""
import json
import re
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
package = root / 'package'
metadata = json.loads((package / 'metadata.json').read_text())
assert metadata['KPlugin']['Id'] == 'local.plasma.icontasks.endtask'
version = re.search(r'project\(PlasmaEndTask VERSION ([0-9.]+)', (root / 'CMakeLists.txt').read_text())
assert version and metadata['KPlugin']['Version'] == version.group(1), 'CMake/metadata version mismatch'
assert metadata['KPlugin']['License'] == 'GPL-2.0-or-later'
menu = (package / 'contents/ui/ContextMenu.qml').read_text()
assert menu.index('id: terminateTaskItem') < menu.index('id: closeWindowItem')
assert 'text: "End Task"' in menu
assert 'icon: decodeURIComponent(Qt.resolvedUrl("../icons/end-task-white.svg").toString().replace("file://", ""))' in menu
assert 'tasks.processController.requestTermination(pids)' in menu
assert 'function terminationPids()' in menu
assert metadata['KPlugin']['Name'] == 'Icons-Only Task Manager — End Task'
icon_dir = package / 'contents/icons'
assert {path.name for path in icon_dir.iterdir()} == {'end-task-white.svg'}
icon = ET.parse(icon_dir / 'end-task-white.svg').getroot()
preview = ET.parse(root / 'docs/menu-preview.svg').getroot()
ns = {'svg': 'http://www.w3.org/2000/svg'}
assert [node.text for node in preview.findall('svg:text', ns)] == ['End Task', 'Close']
icon_paths = icon.findall('svg:path', ns)
preview_paths = preview.findall('svg:path', ns)[:2]
assert len(icon_paths) == len(preview_paths) == 2
for actual, expected in zip(icon_paths, preview_paths):
    for attribute in ('d', 'stroke', 'stroke-width', 'stroke-linecap'):
        assert actual.get(attribute) == expected.get(attribute), f'Preview mismatch: {attribute}'
    assert actual.get('stroke') == '#fff'
    assert actual.get('fill') == 'none'
assert icon.get('viewBox') == '18 18 24 24'
ET.parse(package / 'contents/config/main.xml')
for path in package.rglob('*'):
    if not path.is_file():
        continue
    data = path.read_bytes()
    assert not data.startswith(b'\x7fELF'), f'Binary in source package: {path}'
    assert b'/home/' not in data, f'User-specific absolute path: {path}'
assert (root / 'LICENSE').is_file()
assert (root / 'LICENSES/GPL-2.0-or-later.txt').is_file()
print('PASS: English metadata, menu order, white icon matches preview, licenses, source-only package')
