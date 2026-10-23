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
        # The mock must explicitly grant model sharing. Real user consent
        # defaults OFF, even when Newelle itself is installed and healthy.
        with patch("aidesktop.agent.model_sharing_allowed", return_value=True):
            with patch("aidesktop.newelle_client.complete_newelle", return_value='{"kind":"final","message":"Ready to help."}') as inference:
                with patch("aidesktop.agent.run_tool") as run_tool:
                    response = Agent().ask("hello", "newelle")
        self.assertEqual(response.message, "Ready to help.")
        inference.assert_called_once()
        run_tool.assert_not_called()

    def test_newelle_model_is_never_called_without_user_consent(self):
        with patch("aidesktop.agent.model_sharing_allowed", return_value=False):
            with patch("aidesktop.newelle_client.complete_newelle") as inference:
                response = Agent().ask("hello", "newelle")
        self.assertIn("Model sharing is off", response.message)
        inference.assert_not_called()


if __name__ == "__main__":
    unittest.main()
