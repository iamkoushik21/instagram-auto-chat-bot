"""Unit tests for the bot's _process_inbox helper."""

import pytest
from unittest.mock import MagicMock, call

from src.bot import _process_inbox


def _make_ig(threads):
    ig = MagicMock()
    ig.get_pending_threads.return_value = threads
    return ig


def _make_ai(reply="AI reply"):
    ai = MagicMock()
    ai.get_reply.return_value = reply
    return ai


class TestProcessInbox:
    def test_no_threads_no_actions(self):
        ig = _make_ig([])
        ai = _make_ai()
        last_seen: dict = {}

        _process_inbox(ig, ai, last_seen)

        ai.get_reply.assert_not_called()
        ig.send_message.assert_not_called()

    def test_reply_sent_for_new_message(self):
        msg = MagicMock()
        msg.text = "Hello!"

        thread = MagicMock()
        thread.id = "t1"

        ig = _make_ig([thread])
        # iter_new_messages yields (msg, sender_id)
        ig.iter_new_messages.return_value = iter([(msg, "sender_1")])
        ai = _make_ai("Hi there!")
        last_seen: dict = {}

        _process_inbox(ig, ai, last_seen)

        ai.get_reply.assert_called_once_with(user_id="sender_1", incoming_text="Hello!")
        ig.send_message.assert_called_once_with("t1", "Hi there!")

    def test_multiple_messages_all_replied(self):
        msg_a = MagicMock()
        msg_a.text = "A"
        msg_b = MagicMock()
        msg_b.text = "B"

        thread = MagicMock()
        thread.id = "t1"

        ig = _make_ig([thread])
        ig.iter_new_messages.return_value = iter(
            [(msg_a, "user_1"), (msg_b, "user_2")]
        )
        ai = _make_ai("reply")
        last_seen: dict = {}

        _process_inbox(ig, ai, last_seen)

        assert ai.get_reply.call_count == 2
        assert ig.send_message.call_count == 2
