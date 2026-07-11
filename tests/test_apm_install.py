import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
_configured_apm = os.environ.get("APM_BIN", "apm")
APM_BIN = (
    str((REPO_ROOT / _configured_apm).resolve())
    if "/" in _configured_apm and not Path(_configured_apm).is_absolute()
    else _configured_apm
)


class ApmInstallTests(unittest.TestCase):
    def test_apm_deploys_codex_hooks_and_pack_assets(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            install_root = Path(temporary_directory)
            (install_root / ".codex").mkdir()
            package_source = install_root / "package-source"
            shutil.copytree(
                REPO_ROOT,
                package_source,
                ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"),
            )

            result = subprocess.run(
                [
                    APM_BIN,
                    "install",
                    str(package_source),
                    "--target",
                    "codex",
                    "--root",
                    str(install_root),
                ],
                cwd=install_root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            hooks_path = install_root / ".codex/hooks.json"
            self.assertTrue(hooks_path.is_file(), "APM must write Codex hooks.json")
            hooks = json.loads(hooks_path.read_text())
            self.assertIn("Stop", hooks["hooks"])
            self.assertTrue(any((install_root / ".codex/hooks").rglob("guppi_player.py")))
            self.assertTrue(any((install_root / "apm_modules").rglob("openpeon.json")))
            self.assertTrue(any((install_root / "apm_modules").rglob("*.wav")))

    def test_apm_global_install_deploys_a_runnable_codex_hook(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            home_directory = temporary_root / "home"
            package_source = temporary_root / "package-source"
            shutil.copytree(
                REPO_ROOT,
                package_source,
                ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"),
            )
            environment = {**os.environ, "HOME": str(home_directory)}

            result = subprocess.run(
                [APM_BIN, "install", str(package_source), "--target", "codex", "--global"],
                cwd=temporary_root,
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            hooks_path = home_directory / ".codex" / "hooks.json"
            self.assertTrue(hooks_path.is_file())
            deployed_player = next((home_directory / ".codex" / "hooks").rglob("guppi_player.py"))
            spec = importlib.util.spec_from_file_location("deployed_guppi", deployed_player)
            player = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(player)
            manifest = player.locate_manifest(
                {}, deployed_player, home_directory / ".apm" / "apm_modules"
            )

            self.assertIsNotNone(manifest)
            self.assertTrue(manifest.is_file())


if __name__ == "__main__":
    unittest.main()
