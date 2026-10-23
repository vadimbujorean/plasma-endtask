#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Panel config and installer tests using temporary files and mocked systemd only."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('panel_config', ROOT / 'scripts/panel-config.py')
config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)
SAMPLE = b'''# Preserve comments and non-UTF8 bytes: \xff
[Containments][1]
plugin=org.kde.panel
[Containments][1][General]
AppletOrder=7;8;9
[Containments][1][Applets][7]
immutability=1
plugin=org.kde.plasma.icontasks
[Containments][1][Applets][7][Configuration][General]
launchers=applications:org.kde.dolphin.desktop,applications:firefox.desktop
groupingStrategy=1
[Containments][1][Applets][8]
plugin=org.kde.plasma.digitalclock
[Containments][1][Applets][9]
plugin=local.plasma.icontasks.endtask
[Containments][2]
plugin=org.kde.plasma.folder
[Containments][2][Applets][10]
plugin=org.kde.plasma.icontasks
[Containments][3]
plugin=org.kde.panel
[Containments][3][Applets][11]
plugin=org.kde.plasma.icontasks
[Containments][3][Applets][12]
plugin=org.kde.plasma.taskmanager
[Containments][3][Applets][12][Applets][13]
plugin=org.kde.plasma.icontasks
'''


class ConfigTests(unittest.TestCase):
    def test_only_direct_panel_icon_tasks_change(self):
        updated, ids = config.replace_plugins(SAMPLE)
        self.assertEqual(ids, [('1', '7'), ('3', '11')])
        expected = SAMPLE.replace(
            b'[Applets][7]\nimmutability=1\nplugin=' + config.ORIGINAL,
            b'[Applets][7]\nimmutability=1\nplugin=' + config.CUSTOM,
        ).replace(b'[Applets][11]\nplugin=' + config.ORIGINAL,
                  b'[Applets][11]\nplugin=' + config.CUSTOM)
        self.assertEqual(updated, expected)
        self.assertEqual(config.replace_plugins(updated), (updated, []))

    def test_crlf_whitespace_and_no_final_newline(self):
        data = (b'[Containments][1]\r\nplugin=org.kde.panel\r\n'
                b'[Containments][1][Applets][7]\r\n  plugin = ' + config.ORIGINAL + b'  ')
        updated, ids = config.replace_plugins(data)
        self.assertEqual(updated, data.replace(config.ORIGINAL, config.CUSTOM))
        self.assertEqual(ids, [('1', '7')])

    def test_fail_closed(self):
        for data in (SAMPLE + b'[$i]\n', SAMPLE + b'[broken\n',
                     SAMPLE.replace(b'immutability=1', b'plugin=duplicate')):
            with self.subTest(data=data), self.assertRaises(ValueError):
                config.replace_plugins(data)

    def test_atomic_write_check_mode_permissions_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'appletsrc'
            path.write_bytes(SAMPLE)
            path.chmod(0o640)
            self.assertEqual(len(config.update_config(path, check_only=True)), 2)
            self.assertEqual(path.read_bytes(), SAMPLE)
            self.assertEqual(len(config.update_config(path)), 2)
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            self.assertEqual(config.update_config(path), [])
            link = Path(directory) / 'link'
            link.symlink_to(path)
            with self.assertRaises(ValueError):
                config.update_config(link)
            self.assertFalse(list(Path(directory).glob('.endtask-*')))


@unittest.skipIf(os.geteuid() == 0, 'Shell installers intentionally refuse root')
class ScriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bin = self.directory / 'bin'
        self.bin.mkdir()
        self.config_dir = self.directory / 'config'
        self.config_dir.mkdir()
        self.path = self.config_dir / 'plasma-org.kde.plasma.desktop-appletsrc'
        self.path.write_bytes(SAMPLE)
        self.state = self.directory / 'state'
        self.env = dict(os.environ, PATH=f'{self.bin}:{os.environ["PATH"]}',
                        XDG_CONFIG_HOME=str(self.config_dir), XDG_STATE_HOME=str(self.state),
                        XDG_DATA_HOME=str(self.directory / 'data'),
                        BUILD_DIR=str(self.directory / 'build'), FAKE_DIR=str(self.directory))
        self.executable('systemctl', f'''#!{sys.executable}
import os
from pathlib import Path
import sys
root = Path(os.environ['FAKE_DIR'])
command = sys.argv[2]
with (root / 'calls').open('a') as out:
    out.write(command + '\\n')
if command == 'is-active':
    sys.exit(1 if (root / 'inactive').exists() else 0)
if command == 'stop':
    if (root / 'fail-stop').exists():
        sys.exit(1)
    pending = root / 'pending-config'
    if pending.exists():
        (Path(os.environ['XDG_CONFIG_HOME']) / 'plasma-org.kde.plasma.desktop-appletsrc').write_bytes(pending.read_bytes())
        pending.unlink()
if command == 'start' and (root / 'fail-start-once').exists():
    (root / 'fail-start-once').unlink()
    sys.exit(1)
if command == 'start' and (root / 'signal-term-once').exists():
    import signal
    (root / 'signal-term-once').unlink()
    os.kill(os.getppid(), signal.SIGTERM)
''')
        self.executable('python3', f'''#!/usr/bin/env bash
if [[ "$2" != --check && -f "$FAKE_DIR/fail-apply" ]]; then exit 1; fi
exec '{sys.executable}' "$@"
''')
        self.executable('plasmashell', '#!/usr/bin/env bash\necho "plasmashell 6.7.5"\n')
        self.executable('cmake', '''#!/usr/bin/env bash
printf 'cmake\n' >> "$FAKE_DIR/build-calls"
mkdir -p "$BUILD_DIR/bin" "$BUILD_DIR/package"
printf '#!/usr/bin/env bash\nexit 0\n' > "$BUILD_DIR/bin/check-runtime"
chmod +x "$BUILD_DIR/bin/check-runtime"
''')
        self.executable('kpackagetool6', '''#!/usr/bin/env bash
printf 'kpackage\n' >> "$FAKE_DIR/build-calls"
''')

    def executable(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o755)

    def run_script(self, script='scripts/replace-task-manager.sh', *args):
        return subprocess.run(['bash', str(ROOT / script), *args], env=self.env,
                              capture_output=True, text=True, timeout=10)

    def calls(self):
        return (self.directory / 'calls').read_text().splitlines()

    def backups(self):
        return list(self.state.glob('plasma-endtask/backups/before-panel-replacement-*/plasma-org.kde.plasma.desktop-appletsrc'))

    def test_preflight_does_not_modify_or_stop(self):
        result = self.run_script('scripts/replace-task-manager.sh', '--check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.path.read_bytes(), SAMPLE)
        self.assertEqual(self.calls(), ['is-active'])
        self.assertEqual(self.backups(), [])

    def test_backup_is_after_shutdown_and_repeat_is_safe(self):
        latest = SAMPLE + b'# Last-minute saved setting\n'
        (self.directory / 'pending-config').write_bytes(latest)
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.backups()[0].read_bytes(), latest)
        self.assertEqual(self.path.read_bytes(), config.replace_plugins(latest)[0])
        self.assertEqual(self.calls(), ['is-active', 'stop', 'start'])
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('configuration unchanged', result.stdout)
        self.assertEqual(self.path.read_bytes(), config.replace_plugins(latest)[0])

    def test_no_original_no_widget_added(self):
        self.path.write_bytes(b'[Containments][1]\nplugin=org.kde.panel\n')
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No original', result.stdout)
        self.assertEqual(self.path.read_bytes(), self.backups()[0].read_bytes())

    def test_inactive_and_stop_failure_leave_config_alone(self):
        (self.directory / 'inactive').touch()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls(), ['is-active'])
        (self.directory / 'inactive').unlink()
        (self.directory / 'fail-stop').touch()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.path.read_bytes(), SAMPLE)
        self.assertEqual(self.calls()[-2:], ['stop', 'start'])
        self.assertEqual(self.backups(), [])

    def test_apply_failure_rolls_back_and_starts_plasma(self):
        (self.directory / 'fail-apply').touch()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.path.read_bytes(), SAMPLE)
        self.assertEqual(self.calls(), ['is-active', 'stop', 'stop', 'start'])

    def test_start_failure_rolls_back_and_retries(self):
        (self.directory / 'fail-start-once').touch()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.path.read_bytes(), SAMPLE)
        self.assertEqual(self.calls(), ['is-active', 'stop', 'start', 'stop', 'start'])

    def test_termination_rolls_back_and_starts_plasma(self):
        (self.directory / 'signal-term-once').touch()
        result = self.run_script()
        self.assertEqual(result.returncode, 143, result.stderr)
        self.assertEqual(self.path.read_bytes(), SAMPLE)
        self.assertEqual(self.calls(), ['is-active', 'stop', 'start', 'stop', 'start'])

    def test_default_install_does_not_touch_panel(self):
        result = self.run_script('install.sh')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.path.read_bytes(), SAMPLE)
        self.assertFalse((self.directory / 'calls').exists())

    def test_installer_supported_plasma_versions(self):
        for version in ('6.7.5', '6.8.0', '6.8.1'):
            with self.subTest(version=version):
                self.executable('plasmashell', f'#!/usr/bin/env bash\necho "plasmashell {version}"\n')
                result = self.run_script('install.sh', '--build-only')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('Package ready:', result.stdout)
        self.assertFalse((self.directory / 'calls').exists())
        self.assertEqual(self.path.read_bytes(), SAMPLE)

    def test_installer_unsupported_plasma_versions_do_not_build(self):
        for version in ('5.27.12', '6.6.5', '6.9.0', '6.80.1', '6.8.1.2', '6.8.1-dev', 'invalid'):
            with self.subTest(version=version):
                self.executable('plasmashell', f'#!/usr/bin/env bash\necho "plasmashell {version}"\n')
                result = self.run_script('install.sh', '--build-only')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('Unsupported version:', result.stderr)
                self.assertFalse((self.directory / 'build-calls').exists())
        self.assertFalse((self.directory / 'calls').exists())
        self.assertEqual(self.path.read_bytes(), SAMPLE)

    def test_opt_in_install_reloads_once_even_with_restart(self):
        result = self.run_script('install.sh', '--replace-task-manager', '--restart')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.path.read_bytes(), config.replace_plugins(SAMPLE)[0])
        self.assertEqual(self.calls(), ['is-active', 'is-active', 'stop', 'start'])
        self.assertNotIn('Enter Edit Mode', result.stdout)

    def test_bad_flags_and_failed_preflight_do_not_build(self):
        result = self.run_script('install.sh', '--build-only', '--replace-task-manager')
        self.assertEqual(result.returncode, 2, result.stderr)
        (self.directory / 'inactive').touch()
        result = self.run_script('install.sh', '--replace-task-manager')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.directory / 'build-calls').exists())
        self.assertEqual(self.path.read_bytes(), SAMPLE)


if __name__ == '__main__':
    unittest.main()
