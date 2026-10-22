import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aidesktop.history import history_file, record_action, recent_actions


class HistoryTests(unittest.TestCase):
    def test_private_log_records_only_tool_name_status_and_time(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {'XDG_STATE_HOME': directory}):
                self.assertEqual(recent_actions(), [])
                record_action('set_audio_output', 'succeeded')
                record_action('launch_application', 'failed')
                events = recent_actions()
                self.assertEqual([row['status'] for row in events], ['succeeded', 'failed'])
                self.assertEqual(set(events[0]), {'timestamp', 'tool', 'status'})
                self.assertEqual(stat.S_IMODE(history_file().stat().st_mode), 0o600)
                self.assertEqual(history_file().parent, Path(directory) / 'ai-desktop')

    def test_bad_tool_and_status_rejected(self):
        with self.assertRaises(ValueError):
            record_action('../bad', 'succeeded')
        with self.assertRaises(ValueError):
            record_action('audio_outputs', 'unknown')


if __name__ == '__main__':
    unittest.main()
