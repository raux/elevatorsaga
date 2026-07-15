"""Integration checks for the local Python/Java strategy runner."""

import re
import unittest
from pathlib import Path

from multilang_server import JAVA, JAVAC, execute_strategy, run_java_strategy, run_python_strategy


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = (ROOT / "index.html").read_text(encoding="utf-8")


def editor_template(template_id):
    match = re.search(
        r'<script type="text/plain" id="' + re.escape(template_id) + r'">\s*(.*?)\s*</script>',
        INDEX_HTML,
        re.DOTALL,
    )
    if not match:
        raise AssertionError(f"Missing editor template: {template_id}")
    return match.group(1)


class MultiLanguageRunnerTests(unittest.TestCase):
    def test_rejects_unsupported_language(self):
        status, result = execute_strategy(
            {"language": "ruby", "challenge": 1, "code": "puts 'hello'"}
        )
        self.assertEqual(status, 400)
        self.assertFalse(result["ok"])

    def test_default_python_strategy_completes(self):
        result = run_python_strategy(editor_template("default-python-implementation"), 1)
        self.assertTrue(result["ok"], result)
        self.assertIn("stats", result)

    @unittest.skipUnless(JAVA and JAVAC, "Java JDK is not available")
    def test_default_java_strategy_compiles_and_completes(self):
        result = run_java_strategy(editor_template("default-java-implementation"), 1)
        self.assertTrue(result["ok"], result)
        self.assertIn("stats", result)


if __name__ == "__main__":
    unittest.main()
