from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "plugins" / "cloudrepo-environment-direct"
sys.path.insert(0, str(ROOT / "tools"))
from build_release import build, package_files  # noqa: E402


class PackageTests(unittest.TestCase):
    def test_metadata_and_optional_connector_binding(self) -> None:
        portable = json.loads((PACKAGE / "plugin.json").read_text(encoding="utf-8"))
        native = json.loads((PACKAGE / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        app = json.loads((PACKAGE / ".app.json").read_text(encoding="utf-8"))
        self.assertEqual(portable["name"], "cloudrepo-environment-direct")
        self.assertEqual(portable["version"], "0.1.0")
        self.assertEqual(portable["author"]["name"], "Tungsteno74")
        self.assertEqual(native["interface"], portable["extensions"]["com.openai"]["interface"])
        self.assertFalse(app["apps"]["github"]["required"])
        self.assertEqual(app["apps"]["github"]["id"], "connector_76869538009648d5b282a4bb21c3d157")

    def test_two_skills_and_required_references_exist(self) -> None:
        skills = sorted(PACKAGE.glob("skills/*/SKILL.md"))
        self.assertEqual([path.parent.name for path in skills], ["cloudrepo-environment-direct", "github-actions-direct"])
        for path in skills:
            self.assertTrue(path.read_text(encoding="utf-8").startswith("---\nname:"))
        expected = {"runner-selection.md", "provider-contracts.md", "fallback-recommendations.md", "status-schema.md"}
        self.assertTrue(expected.issubset({path.name for path in (skills[0].parent / "references").iterdir()}))

    def test_archive_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            first = build(ROOT, output / "first")
            second = build(ROOT, output / "second")
            self.assertEqual(first["sha256"], second["sha256"])
            archive_path = output / "first" / str(first["archive"])
            self.assertEqual(hashlib.sha256(archive_path.read_bytes()).hexdigest(), first["sha256"])
            with zipfile.ZipFile(archive_path) as archive:
                names = archive.namelist()
                self.assertEqual(names, sorted(names))
                self.assertEqual(set(names), {path.relative_to(PACKAGE).as_posix() for path in package_files(PACKAGE)})
                self.assertIn("plugin.json", names)
                self.assertIn(".app.json", names)
                self.assertIsNone(archive.testzip())

    def test_offline_validation_has_no_provider_or_credential_files(self) -> None:
        self.assertFalse((PACKAGE / "mcp.json").exists())
        for path in package_files(PACKAGE):
            self.assertNotIn("ghp_", path.read_text(encoding="utf-8", errors="ignore"))
