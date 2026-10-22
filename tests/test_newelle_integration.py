import unittest
from unittest.mock import patch

from aidesktop.agent import Agent
from aidesktop.providers import complete


class NewelleWiringTests(unittest.TestCase):
    def test_provider_selects_newelle_nonagent_client(self):
        with patch("aidesktop.newelle_client.complete_newelle", return_value='{"kind":"final","message":"ok"}') as mocked:
            response = complete("newelle", "system", "request")
        self.assertIn('"ok"', response)
        mocked.assert_called_once_with("system", "request")

    def test_agent_newelle_responds_without_any_system_action(self):
        with patch("aidesktop.newelle_client.complete_newelle", return_value='{"kind":"final","message":"Ready to help."}'):
            with patch("aidesktop.agent.run_tool") as run_tool:
                response = Agent().ask("hello", "newelle")
        self.assertEqual(response.message, "Ready to help.")
        run_tool.assert_not_called()


if __name__ == "__main__":
    unittest.main()
