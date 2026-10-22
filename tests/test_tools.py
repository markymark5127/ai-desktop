import unittest

from aidesktop.tools import ToolError, run_tool


class ToolTests(unittest.TestCase):
    def test_rejects_arbitrary_shell(self):
        with self.assertRaises(ToolError):
            run_tool("shell", {"command": "rm -rf /"})

    def test_rejects_extra_arguments(self):
        with self.assertRaises(ToolError):
            run_tool("system_snapshot", {"payload": "unexpected"})

    def test_system_snapshot(self):
        result = run_tool("system_snapshot", {})
        self.assertIn("OS:", result)

    def test_mutation_requires_exact_arguments(self):
        with self.assertRaises(ToolError):
            run_tool("set_audio_output", {"sink": "a", "command": "extra"})


if __name__ == "__main__":
    unittest.main()
