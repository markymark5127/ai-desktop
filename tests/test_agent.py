import unittest

from aidesktop.agent import Agent, PendingAction, _parse_decision, _system_prompt
from aidesktop.search import AppResult
from unittest.mock import patch
from aidesktop.tools import ToolError


class AgentTests(unittest.TestCase):
    def setUp(self):
        # Existing action-planning tests explicitly opt into mock inference.
        self.sharing = patch("aidesktop.agent.model_sharing_allowed", return_value=True)
        self.sharing.start()
        self.addCleanup(self.sharing.stop)

    def test_model_sharing_off_never_calls_inference(self):
        from unittest.mock import Mock
        fake = Mock()
        with patch("aidesktop.agent.model_sharing_allowed", return_value=False):
            result = Agent(inference=fake).ask("Tell me about Bazzite", "newelle")
        self.assertIn("Model sharing is off", result.message)
        fake.assert_not_called()

    def test_offline_builtin_diagnostics_ignore_model_permission(self):
        with patch("aidesktop.agent.model_sharing_allowed", return_value=False):
            with patch("aidesktop.agent.run_tool", return_value="offline system status"):
                reply = Agent().ask("system info", "builtin")
        self.assertIn("offline system status", reply.message)

    def test_plain_text_answer_from_model_is_readable_but_cannot_execute(self):
        agent = Agent(inference=lambda *_: "You can check the audio output in Settings.")
        answer = agent.ask("Why is there no audio?", "local")
        self.assertIn("audio output", answer.message)
        self.assertIsNone(answer.pending)

    def test_malformed_action_json_never_executes(self):
        agent = Agent(inference=lambda *_: '{"kind":"tool","name":"run_shell",')
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

    def test_approved_action_records_history(self):
        action = PendingAction("set_audio_output", {"sink": "test"}, "Change output")
        with patch("aidesktop.agent.run_tool", return_value="done"):
            with patch("aidesktop.agent.record_action") as record:
                answer = Agent().approve(action)
        self.assertEqual(answer.message, "done")
        record.assert_called_once_with("set_audio_output", "succeeded")

    def test_failed_approved_action_records_history(self):
        action = PendingAction("set_audio_output", {"sink": "test"}, "Change output")
        with patch("aidesktop.agent.run_tool", side_effect=ToolError("bad sink")):
            with patch("aidesktop.agent.record_action") as record:
                answer = Agent().approve(action)
        self.assertIn("could not complete", answer.message)
        record.assert_called_once_with("set_audio_output", "failed")

    def test_learning_style_alters_explanation_not_approval_capabilities(self):
        quick = _system_prompt("simple")
        learned = _system_prompt("learn")
        self.assertIn("I'll focus on the next useful step", quick)
        self.assertIn("Mac comparisons", learned)
        self.assertIn('"requires_confirmation": true', quick)
        self.assertIn('"requires_confirmation": true', learned)
        self.assertIn('"name": "set_audio_output"', quick)
        self.assertIn('"name": "set_audio_output"', learned)

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
