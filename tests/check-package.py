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
assert 'icon: "process-stop"' in menu
assert 'tasks.processController.requestTermination(pids)' in menu
assert 'function terminationPids()' in menu
assert metadata['KPlugin']['Name'] == 'Icons-Only Task Manager — End Task'
assert not (package / 'contents/icons').exists(), 'No bundled artwork should remain'
preview = ET.parse(root / 'docs/menu-preview.svg').getroot()
ns = {'svg': 'http://www.w3.org/2000/svg'}
assert [node.text for node in preview.findall('svg:text', ns)] == ['End Task', 'Close']
ET.parse(package / 'contents/config/main.xml')
for path in package.rglob('*'):
    if not path.is_file():
        continue
    data = path.read_bytes()
    assert not data.startswith(b'\x7fELF'), f'Binary in source package: {path}'
    assert b'/home/' not in data, f'User-specific absolute path: {path}'
assert (root / 'LICENSE').is_file()
assert (root / 'LICENSES/GPL-2.0-or-later.txt').is_file()
print('PASS: English metadata/preview, menu order, theme icon, licenses, source-only package')
