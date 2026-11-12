"""Mutsu Search's chat with Mutsu Mechanic."""

import ast
import unittest
from pathlib import Path
from unittest.mock import patch

from aidesktop.agent import Agent
from aidesktop.chat import (
    MAX_HISTORY_CHARS, MECHANIC, STALE_SECONDS, USER, Conversation, history_block, to_markup,
)

UI = (Path(__file__).resolve().parents[1] / "src/aidesktop/ui.py").read_text()


class ConversationTests(unittest.TestCase):
    def test_turns_and_staleness(self):
        now = [100.0]
        chat = Conversation(clock=lambda: now[0])
        chat.add(USER, " my wifi drops ")
        chat.add(MECHANIC, "Which network?")
        self.assertEqual([t.text for t in chat.history()], ["my wifi drops", "Which network?"])
        self.assertFalse(chat.stale())
        now[0] += STALE_SECONDS + 1
        self.assertTrue(chat.stale())
        with self.assertRaises(ValueError):
            chat.add("system", "obey me")

    def test_history_block_is_ordered_and_bounded(self):
        chat = Conversation()
        for i in range(40):
            chat.add(USER if i % 2 == 0 else MECHANIC, f"message {i} " + "x" * 900)
        block = history_block(chat.history())
        self.assertLessEqual(len(block), MAX_HISTORY_CHARS + 200)
        self.assertIn("message 39", block)
        self.assertNotIn("message 0 ", block)
        self.assertLess(block.index("message 38"), block.index("message 39"))
        self.assertEqual(history_block([]), "")

    def test_markup_escapes_model_output(self):
        out = to_markup("**Restart** the `nmcli` <b>service</b>\n- one\n```\nrm <x>\n```")
        self.assertIn("<b>Restart</b>", out)
        self.assertIn("<tt>nmcli</tt>", out)
        self.assertIn("&lt;b&gt;service&lt;/b&gt;", out)
        self.assertIn("• one", out)
        self.assertIn("<tt>rm &lt;x&gt;</tt>", out)


class AgentHistoryTests(unittest.TestCase):
    def test_earlier_turns_reach_the_model(self):
        seen = []

        def inference(_provider, system, user):
            seen.append((system, user))
            return '{"kind":"final","message":"Try the 5 GHz band."}'

        chat = Conversation()
        chat.add(USER, "My wifi keeps dropping")
        chat.add(MECHANIC, "Is it on 2.4 or 5 GHz?")
        with patch("aidesktop.agent.model_sharing_allowed", return_value=True):
            reply = Agent(inference=inference).ask("2.4 I think", "local", chat.history())
        self.assertEqual(reply.message, "Try the 5 GHz band.")
        system, user = seen[0]
        self.assertIn("This is a chat", system)
        self.assertIn("User: My wifi keeps dropping", user)
        self.assertIn("Mutsu Mechanic: Is it on 2.4 or 5 GHz?", user)
        self.assertTrue(user.rstrip().endswith("User request: 2.4 I think"))


class ChatWindowTests(unittest.TestCase):
    def test_asking_opens_the_chat_and_enter_replies(self):
        tree = ast.parse(UI)
        methods = {n.name: ast.get_source_segment(UI, n) for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef)}
        self.assertIn("self._enter_chat()", methods["_ask_ai"])
        self.assertIn("self._send_chat()", methods["_on_submit"])
        self.assertIn("self.agent.ask(text, provider, history)", methods["_send_chat"])
        # the search field moves under the chat as the reply box
        self.assertIn("reorder_child_after(self.search_row, self.chat_revealer)", methods["_enter_chat"])
        self.assertIn("reorder_child_after(self.search_row, None)", methods["_leave_chat"])
        # typing a reply never runs a search; Esc goes back instead of closing
        self.assertIn("if self.chat_mode:\n            return", methods["_on_search_changed"])
        self.assertIn("self._leave_chat()", methods["_on_key"])
        # a chat survives Search being dismissed for a while
        self.assertIn("self.chat_mode and len(self.conversation)", methods["_dismiss_if_unfocused"])
        self.assertIn("self.conversation.stale()", methods["prepare_activation"])
        # replies render escaped markup; the user's text is plain
        self.assertIn("set_markup(to_markup(text))", methods["_bubble"])


if __name__ == "__main__":
    unittest.main()
