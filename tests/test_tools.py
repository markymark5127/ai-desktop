import unittest
from unittest.mock import patch

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

    def test_unknown_app_refuses_launch(self):
        with patch("aidesktop.tools.resolve_app_id", return_value=False):
            with patch("aidesktop.tools.subprocess.Popen") as popen:
                with self.assertRaises(ToolError):
                    run_tool("launch_application", {"desktop_id": "unknown.desktop"})
                popen.assert_not_called()

    def test_mutation_requires_exact_arguments(self):
        with self.assertRaises(ToolError):
            run_tool("set_audio_output", {"sink": "a", "command": "extra"})




class DiskSpaceTests(unittest.TestCase):
    def test_image_based_root_reporting_zero_is_skipped(self):
        from collections import namedtuple
        from aidesktop.tools import disk_space
        Usage = namedtuple("Usage", "total used free")
        sizes = {"/var": Usage(500 * 1024 ** 3, 100 * 1024 ** 3, 400 * 1024 ** 3), "/": Usage(0, 0, 0)}
        path, usage = disk_space(paths=("/", "/var"), usage=lambda p: sizes[p])
        self.assertEqual(path, "/var")
        self.assertEqual(usage.free // 1024 ** 3, 400)

    def test_unreadable_everywhere(self):
        from aidesktop.tools import disk_space

        def fail(_path):
            raise OSError("nope")
        self.assertEqual(disk_space(paths=("/x",), usage=fail), (None, None))


if __name__ == "__main__":
    unittest.main()
