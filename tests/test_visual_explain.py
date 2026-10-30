"""Runtime checks for offline explanations; no model, GUI, or third-party deps."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "config/skills/visual-explain"
SPEC = importlib.util.spec_from_file_location("visual_renderer", SKILL / "scripts/render.py")
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)
EXAMPLE = json.loads((SKILL / "examples/workspace-delay.json").read_text())


class VisualExplainTests(unittest.TestCase):
    def setUp(self):
        self.model = copy.deepcopy(EXAMPLE)

    def test_example_is_valid(self):
        renderer.validate(self.model)

    def test_invalid_models_are_rejected(self):
        mutations = [
            lambda m: m["interfaces"][0].update(to="missing"),
            lambda m: m["entities"][0].update(sources=[]),
            lambda m: m["steps"][0]["interfaces"].update(missing="flowing"),
            lambda m: m["steps"][0]["interfaces"].update({"capture-api": "broken"}),
            lambda m: m["sources"][0].update(url="javascript:alert(1)"),
            lambda m: m["entities"][1].update(id=m["entities"][0]["id"]),
            lambda m: m["entities"][0].update(column=True),
        ]
        for mutate in mutations:
            model = copy.deepcopy(self.model)
            mutate(model)
            with self.subTest(model=model), self.assertRaises(ValueError):
                renderer.validate(model)

    def test_render_escapes_embedded_script_and_rejects_model_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model.json"
            self.model["title"] = '</script><script>globalThis.injected=true</script> & <tag>'
            model.write_text(json.dumps(self.model))
            result = subprocess.run([sys.executable, str(SKILL / "scripts/render.py"), str(model)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = model.with_name("index.html").read_text()
            payload = page.split('<script id="explanation-data" type="application/json">')[1].split('</script>')[0]
            self.assertNotIn("</script>", payload)
            self.assertEqual(json.loads(payload)["model"]["title"], self.model["title"])
            self.assertNotIn("__EXPLANATION_DATA__", page)
            original = model.read_bytes()
            result = subprocess.run([sys.executable, str(SKILL / "scripts/render.py"), str(model),
                                     "--output", str(model)], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(model.read_bytes(), original)

    def test_check_writes_no_page(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model.json"
            model.write_text(json.dumps(self.model))
            result = subprocess.run([sys.executable, str(SKILL / "scripts/render.py"), str(model),
                                     "--check", "--open"], capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(model.with_name("index.html").exists())

    @patch.object(renderer.sys, "platform", "linux")
    @patch.dict(os.environ, {}, clear=True)
    def test_headless_returns_manual_uri_without_spawning(self):
        with patch.object(renderer.subprocess, "Popen") as spawn:
            self.assertIn("No graphical session", renderer.open_browser(Path("/tmp/example.html")))
            spawn.assert_not_called()

    @patch.object(renderer.sys, "platform", "linux")
    @patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-1"}, clear=True)
    def test_opener_is_detached_and_not_a_shell(self):
        child = unittest.mock.Mock()
        child.wait.side_effect = subprocess.TimeoutExpired("xdg-open", 0.3)
        with patch.object(renderer.shutil, "which", return_value="/usr/bin/xdg-open"), \
                patch.object(renderer.subprocess, "Popen", return_value=child) as spawn:
            self.assertIn("launched", renderer.open_browser(Path("/tmp/a b.html")))
            args, kwargs = spawn.call_args
            self.assertEqual(args[0], ["xdg-open", "file:///tmp/a%20b.html"])
            self.assertTrue(kwargs["start_new_session"])
            self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)
            self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
            self.assertFalse(kwargs.get("shell", False))

    @patch.object(renderer.sys, "platform", "linux")
    @patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True)
    def test_gio_fallback_and_failed_opener(self):
        child = unittest.mock.Mock()
        child.wait.return_value = 3
        with patch.object(renderer.shutil, "which", side_effect=lambda cmd: cmd == "gio"), \
                patch.object(renderer.subprocess, "Popen", return_value=child) as spawn:
            self.assertIn("status 3", renderer.open_browser(Path("/tmp/example.html")))
            self.assertEqual(spawn.call_args.args[0][:2], ["gio", "open"])

    def test_install_preserves_config_and_backs_up_only_owned_files(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "opencode"
            config.mkdir()
            (config / "opencode.json").write_text('{"keep":"my v2 config"}')
            command = [sys.executable, str(ROOT / "scripts/install-visual-explain.py"),
                       "--config-dir", str(config)]
            subprocess.run(command, check=True, capture_output=True)
            self.assertEqual((config / "opencode.json").read_text(), '{"keep":"my v2 config"}')
            self.assertTrue((config / "skills/visual-explain/assets/page.html").is_file())
            (config / "commands/visual-explain.md").write_text("previous command")
            subprocess.run(command, check=True, capture_output=True)
            backups = list((config / "backups").glob("*/commands/visual-explain.md"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), "previous command")
            self.assertFalse(list((config / "backups").rglob("opencode.json")))


if __name__ == "__main__":
    unittest.main()
