"""Reject shells that would silently omit native Duo behavior or contain game data."""
import hashlib
import importlib.util
import json
import plistlib
import tempfile
import unittest
import zipfile
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / "ios/tools/duo_shell.py"
SPEC = importlib.util.spec_from_file_location("duo_shell", MODULE)
duo_shell = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(duo_shell)


class DuoShellTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "shell.zip"
        self.output = Path(self.temp.name) / "duo.zip"
        self.root = "Payload/DmIOS.app/"
        self.binary = b"inert test fixture UIHingeInteraction reservedRegionsOfKind:options: hingeChanged:"
        self.info = {
            "CFBundleExecutable": "DmIOS",
            "UILaunchScreen": {},
            "UISupportedInterfaceOrientations": ["UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight"],
            "UISupportedInterfaceOrientations~ipad": ["UIInterfaceOrientationLandscapeLeft", "UIInterfaceOrientationLandscapeRight", "UIInterfaceOrientationPortrait", "UIInterfaceOrientationPortraitUpsideDown"],
        }

    def archive(self, extra=None):
        with zipfile.ZipFile(self.source, "w") as archive:
            archive.writestr(self.root + "Info.plist", plistlib.dumps(self.info))
            archive.writestr(self.root + "DmIOS", self.binary)
            for name, data in (extra or {}).items():
                archive.writestr(name, data)

    def test_stamp_preserves_binary_and_records_exact_hash(self):
        self.archive()
        proof = duo_shell.stamp(self.source, self.output, "27.1")
        self.assertEqual(proof["binary_sha256"], hashlib.sha256(self.binary).hexdigest())
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read(self.root + "DmIOS"), self.binary)
            self.assertEqual(json.loads(archive.read(self.root + "dm/duo_build.json")), proof)

    def test_rejects_old_sdk_even_when_binary_has_symbols(self):
        self.archive()
        with self.assertRaisesRegex(ValueError, "27.1 SDK"):
            duo_shell.stamp(self.source, self.output, "27.0")

    def test_rejects_geometry_only_fallback(self):
        self.binary = b"inert geometry fallback fixture"
        self.archive()
        with self.assertRaisesRegex(ValueError, "Native hinge code was not compiled"):
            duo_shell.stamp(self.source, self.output, "27.1")

    def test_rejects_fullscreen_compatibility(self):
        self.info["UIRequiresFullScreen"] = True
        self.archive()
        with self.assertRaisesRegex(ValueError, "Legacy fullscreen"):
            duo_shell.stamp(self.source, self.output, "27.1")

    def test_rejects_game_content(self):
        self.archive({self.root + "romfs/game.dat": b"inert fixture"})
        with self.assertRaisesRegex(ValueError, "game content"):
            duo_shell.stamp(self.source, self.output, "27.1")


if __name__ == "__main__":
    unittest.main()
