from __future__ import annotations

import ast
import base64
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/site_behavior_telemetry_v2.py"


def _telemetry_js() -> str:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "BEHAVIOR_TELEMETRY_JS":
                    return ast.literal_eval(node.value)
    raise AssertionError("BEHAVIOR_TELEMETRY_JS not found")


class BehaviorTelemetryTests(unittest.TestCase):
    def test_v2_collector_is_wired_after_base_analytics(self) -> None:
        main = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("from site_behavior_telemetry_v2 import mount_behavior_telemetry", main)
        self.assertIn("mount_behavior_telemetry(PAGE, CMS_ARTICLE_META or ARTICLE_META)", main)
        self.assertLess(
            main.index('inject_analytics(PAGE, source="streamlit")'),
            main.index("mount_behavior_telemetry(PAGE, CMS_ARTICLE_META or ARTICLE_META)"),
        )

    def test_collector_is_session_scoped_and_does_not_trigger_python_reruns(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        js = _telemetry_js()
        self.assertIn("st.components.v2.component", source)
        self.assertIn("sessionStorage", js)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("document.cookie", js)
        self.assertNotIn("setStateValue", js)
        self.assertNotIn("setTriggerValue", js)
        self.assertIn("section_attention", js)
        self.assertIn("element_attention", js)
        self.assertIn("cta_hesitation", js)
        self.assertIn("scroll_abandonment", js)
        self.assertIn("dead_click", js)
        self.assertIn("rage_click", js)
        self.assertIn("first_interaction", js)
        self.assertIn("fcp_ms", js)
        self.assertIn("inp_ms", js)

    def test_click_coordinates_are_only_used_in_memory(self) -> None:
        js = _telemetry_js()
        self.assertIn("event.clientX", js)
        self.assertIn("event.clientY", js)
        self.assertNotIn("client_x", js)
        self.assertNotIn("client_y", js)
        self.assertNotIn("click_x", js)
        self.assertNotIn("click_y", js)

    @unittest.skipUnless(shutil.which("node"), "Node required for Components-v2 syntax validation")
    def test_components_v2_javascript_is_valid_es_module(self) -> None:
        payload = base64.b64encode(_telemetry_js().encode("utf-8")).decode("ascii")
        script = f"await import('data:text/javascript;base64,{payload}'); console.log('v2 telemetry syntax passed');"
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            capture_output=True,
            text=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("syntax passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
