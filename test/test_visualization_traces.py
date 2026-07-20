"""Tests for Python and Java simulation traces used by NiceGUI."""

import unittest

import nicegui_app


class VisualizationTraceTests(unittest.TestCase):
    def assert_valid_trace(self, trace, language):
        self.assertEqual(trace["language"], language)
        self.assertEqual(trace["challenge"], 1)
        self.assertEqual(trace["scene"]["floorCount"], 3)
        self.assertGreater(len(trace["frames"]), 100)
        first = trace["frames"][0]
        last = trace["frames"][-1]
        self.assertEqual(len(first["elevators"]), 1)
        self.assertIn("moving", first["elevators"][0])
        first_user = next(frame["users"][0] for frame in trace["frames"] if frame["users"])
        self.assertIn("riding", first_user)
        self.assertGreater(last["time"], first["time"])
        self.assertIn("transported", last["stats"])
        self.assertIn("passed", trace["result"])

    def test_python_trace(self):
        trace, _ = nicegui_app.generate_python_trace(nicegui_app.DEFAULT_CODE["python"], 1)
        self.assert_valid_trace(trace, "python")

    @unittest.skipUnless(nicegui_app.JAVA and nicegui_app.JAVAC, "Java JDK is unavailable")
    def test_java_trace(self):
        trace, _ = nicegui_app.generate_java_trace(nicegui_app.DEFAULT_CODE["java"], 1)
        self.assert_valid_trace(trace, "java")


if __name__ == "__main__":
    unittest.main()
