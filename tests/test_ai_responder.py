"""Unit tests for AIResponder."""

import pytest
from unittest.mock import MagicMock, patch

from src.ai_responder import AIResponder


def _make_responder(**kwargs) -> AIResponder:
    defaults = dict(
        api_key="test-key",
        model="gpt-4o-mini",
        system_prompt="You are a test bot.",
        max_history=4,
    )
    defaults.update(kwargs)
    with patch("src.ai_responder.OpenAI"):
        responder = AIResponder(**defaults)
    return responder


def _stub_completion(responder: AIResponder, reply_text: str) -> None:
    """Make the underlying OpenAI client return *reply_text*."""
    choice = MagicMock()
    choice.message.content = f"  {reply_text}  "  # include whitespace to test strip()
    completion = MagicMock()
    completion.choices = [choice]
    responder._client.chat.completions.create.return_value = completion


class TestGetReply:
    def test_returns_stripped_reply(self):
        responder = _make_responder()
        _stub_completion(responder, "Hello there!")

        reply = responder.get_reply("user_1", "Hi")

        assert reply == "Hello there!"

    def test_includes_system_prompt_in_messages(self):
        responder = _make_responder(system_prompt="Be terse.")
        _stub_completion(responder, "ok")

        responder.get_reply("user_1", "Tell me something")

        call_kwargs = responder._client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        assert messages[0] == {"role": "system", "content": "Be terse."}

    def test_user_message_included_in_messages(self):
        responder = _make_responder()
        _stub_completion(responder, "Sure")

        responder.get_reply("user_1", "What is Python?")

        call_kwargs = responder._client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert any("What is Python?" in m["content"] for m in user_msgs)

    def test_conversation_history_is_maintained(self):
        responder = _make_responder()

        _stub_completion(responder, "First reply")
        responder.get_reply("user_1", "First message")

        _stub_completion(responder, "Second reply")
        responder.get_reply("user_1", "Second message")

        call_kwargs = responder._client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        # system + user + assistant + user = 4 entries
        assert len(messages) == 4

    def test_histories_are_isolated_per_user(self):
        responder = _make_responder()

        _stub_completion(responder, "Reply to A")
        responder.get_reply("user_A", "Hello from A")

        _stub_completion(responder, "Reply to B")
        responder.get_reply("user_B", "Hello from B")

        # user_B history should only contain one user message
        call_kwargs = responder._client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        user_msgs = [m for m in messages if m["role"] == "user"]
        assert len(user_msgs) == 1
        assert "Hello from B" in user_msgs[0]["content"]

    def test_max_history_limits_context(self):
        """With max_history=2 only the last 2 turns (4 messages) should be kept."""
        responder = _make_responder(max_history=2)

        for i in range(5):
            _stub_completion(responder, f"Reply {i}")
            responder.get_reply("user_1", f"Message {i}")

        call_kwargs = responder._client.chat.completions.create.call_args
        messages = call_kwargs.kwargs["messages"]
        # system message + at most max_history*2 messages from history
        assert len(messages) <= 1 + 2 * 2

    def test_raises_on_api_error(self):
        responder = _make_responder()
        responder._client.chat.completions.create.side_effect = RuntimeError("API down")

        with pytest.raises(RuntimeError, match="API down"):
            responder.get_reply("user_1", "Hello")


class TestClearHistory:
    def test_clear_history_removes_user(self):
        responder = _make_responder()
        _stub_completion(responder, "Hi")
        responder.get_reply("user_1", "Hello")

        responder.clear_history("user_1")

        assert "user_1" not in responder._histories

    def test_clear_history_unknown_user_is_noop(self):
        responder = _make_responder()
        # Should not raise
        responder.clear_history("nonexistent_user")

    def test_clear_all_histories(self):
        responder = _make_responder()
        for uid in ["u1", "u2", "u3"]:
            _stub_completion(responder, "reply")
            responder.get_reply(uid, "msg")

        responder.clear_all_histories()

        assert len(responder._histories) == 0
