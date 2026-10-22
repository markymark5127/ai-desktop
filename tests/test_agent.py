import unittest

from aidesktop.agent import Agent, PendingAction, _parse_decision
from aidesktop.search import AppResult
from unittest.mock import patch


class AgentTests(unittest.TestCase):
    def test_invalid_json_cannot_execute(self):
        agent = Agent(inference=lambda *_: "not json")
        self.assertIn("invalid", agent.ask("fix everything", "local").message.lower())

    def test_unknown_tool_cannot_execute(self):
        agent = Agent(inference=lambda *_: '{"kind":"tool","name":"run_shell","arguments":{}}')
        self.assertIn("not permitted", agent.ask("do something", "local").message)

    def test_change_requires_approval(self):
        agent = Agent(inference=lambda *_: (
            '{"kind":"tool","name":"set_audio_output","arguments":{"sink":"test"}}'
        ))
        answer = agent.ask("change audio output", "local")
        self.assertIsInstance(answer.pending, PendingAction)
        self.assertEqual(answer.pending.name, "set_audio_output")

    def test_builtin_open_friendly_name_requires_approval(self):
        with patch("aidesktop.agent.search_applications", return_value=[
            AppResult("steam.desktop", "Steam")
        ]):
            result = Agent().ask("open Steam", "builtin")
        self.assertEqual(result.pending.name, "launch_application")
        self.assertEqual(result.pending.arguments["desktop_id"], "steam.desktop")

    def test_builtin_open_unknown_app(self):
        with patch("aidesktop.agent.search_applications", return_value=[]):
            result = Agent().ask("open SomeNonexistentApp", "builtin")
        self.assertIsNone(result.pending)
        self.assertIn("No installed application", result.message)

    def test_final_response(self):
        agent = Agent(inference=lambda *_: '{"kind":"final","message":"I cannot verify that."}')
        self.assertEqual(agent.ask("help", "local").message, "I cannot verify that.")

    def test_code_fence_json(self):
        fence = chr(96) * 3
        response = fence + 'json\n{"kind":"final","message":"ok"}\n' + fence
        self.assertEqual(
            _parse_decision(response),
            {"kind": "final", "message": "ok"},
        )


if __name__ == "__main__":
    unittest.main()
