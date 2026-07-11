import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CespManifestTests(unittest.TestCase):
    def test_every_manifest_sound_exists_and_matches_its_sha256(self):
        manifest = json.loads((ROOT / "openpeon.json").read_text(encoding="utf-8"))

        for category in manifest["categories"].values():
            for sound in category["sounds"]:
                sound_path = ROOT / sound["file"]
                self.assertTrue(sound_path.is_file(), sound_path)
                self.assertEqual(
                    hashlib.sha256(sound_path.read_bytes()).hexdigest(),
                    sound["sha256"],
                    sound_path,
                )


if __name__ == "__main__":
    unittest.main()
