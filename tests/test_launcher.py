import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import launch_demo as launcher


class LauncherChecks(unittest.TestCase):
    def run_launcher(self, root, **extra):
        output = io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(launcher, "PROJECT_ROOT", root))
            stack.enter_context(patch("launch_demo.os.chdir"))
            stack.enter_context(patch("launch_demo.importlib.import_module"))
            stack.enter_context(patch("dotenv.load_dotenv"))
            stack.enter_context(patch.dict(os.environ, {"GEMINI_API_KEY": "dummy-test-secret"}))
            stack.enter_context(contextlib.redirect_stdout(output))
            for target, value in extra.items():
                stack.enter_context(patch(target, **value))
            code = launcher.main()
        self.assertNotIn("dummy-test-secret", output.getvalue())
        return code, output.getvalue()

    def make_files(self, root):
        names=[".env","Agent.py","tools.py","manage.py","config/settings.py","dashboard/templates/dashboard/home.html","static/css/style.css","static/js/dashboard.js","static/js/dashboardTransform.js","static/js/mazarejoApi.js","static/vendor/marked.umd.js","static/vendor/purify.min.js","crop_resources.json","market_prices.json"]
        for name in names:
            path = root/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}", encoding="utf-8")

    def test_missing_env_and_key_fail_before_browser(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(launcher, "open_app") as browser:
            root = Path(folder)
            code, output = self.run_launcher(root)
            self.assertEqual(code, 1)
            self.assertIn(".env is missing", output)
            self.make_files(root)
            code, output = self.run_launcher(root, **{"launch_demo.os.environ.get": {"return_value": ""}})
            self.assertIn("GEMINI_API_KEY is missing", output)
            browser.assert_not_called()

    def test_broken_dependency_and_invalid_json_fail_before_browser(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(launcher, "open_app") as browser:
            root=Path(folder)
            self.make_files(root)
            code, output=self.run_launcher(root, **{"launch_demo.importlib.import_module":{"side_effect":ImportError("missing")}})
            self.assertEqual(code,1)
            self.assertIn("Missing or broken imports",output)
            self.assertIn("-m pip install -r",output)
            (root/"market_prices.json").write_text("invalid")
            code, output=self.run_launcher(root)
            self.assertIn("invalid: market_prices.json",output)
            browser.assert_not_called()

    def test_port_conflict_safely_reuses_only_this_project(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(launcher,"open_app") as browser:
            root=Path(folder)
            self.make_files(root)
            probe=Mock()
            probe.__enter__=Mock(return_value=probe)
            probe.__exit__=Mock(return_value=False)
            probe.bind.side_effect=OSError("busy")
            patches={"launch_demo.socket.socket":{"return_value":probe},"launch_demo.readiness":{"return_value":{"status":"ok","app":"mazarejo","project_id":"unrelated"}}}
            code, output=self.run_launcher(root,**patches)
            self.assertEqual(code,1)
            self.assertIn("no process was killed",output)
            browser.assert_not_called()
            patches["launch_demo.readiness"]={"return_value":{"status":"ok","app":"mazarejo","project_id":launcher.PROJECT_ID}}
            code, output=self.run_launcher(root,**patches)
            self.assertEqual(code,0)
            self.assertIn("reusing it safely",output)
            browser.assert_called_once_with(launcher.BASE_URL+"/ar/")


if __name__=="__main__":
    unittest.main()
