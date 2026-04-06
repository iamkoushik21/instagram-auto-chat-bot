"""Unit tests for InstagramClient."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from src.instagram_client import InstagramClient


def _make_client() -> InstagramClient:
    with patch("src.instagram_client.Client"):
        client = InstagramClient("testuser", "testpass")
    return client


def _make_message(msg_id: str, user_id: str, text: str) -> MagicMock:
    msg = MagicMock()
    msg.id = msg_id
    msg.user_id = user_id
    msg.text = text
    return msg


def _make_thread(thread_id: str) -> MagicMock:
    thread = MagicMock()
    thread.id = thread_id
    return thread


class TestLogin:
    def test_fresh_login_saves_session(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("src.instagram_client.Client") as MockClient:
            client = InstagramClient("user", "pass")
            client.login()
            MockClient.return_value.login.assert_called_once_with("user", "pass")
            MockClient.return_value.dump_settings.assert_called_once()

    def test_login_sets_logged_in_flag(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("src.instagram_client.Client"):
            client = InstagramClient("user", "pass")
            client.login()
            assert client._logged_in is True


class TestGetPendingThreads:
    def test_delegates_to_instagrapi(self):
        client = _make_client()
        client._client.direct_threads.return_value = ["thread1"]

        result = client.get_pending_threads(amount=5)

        client._client.direct_threads.assert_called_once_with(amount=5)
        assert result == ["thread1"]


class TestGetThreadMessages:
    def test_delegates_to_instagrapi(self):
        client = _make_client()
        client._client.direct_messages.return_value = ["msg1"]

        result = client.get_thread_messages("thread_id", amount=10)

        client._client.direct_messages.assert_called_once_with("thread_id", amount=10)
        assert result == ["msg1"]


class TestIterNewMessages:
    def setup_method(self):
        self.client = _make_client()
        # Simulate bot's own user_id
        self.client._client.user_id = "bot_pk"

    def test_yields_new_message_from_other_user(self):
        msg = _make_message("msg_1", "other_user", "Hello bot!")
        self.client._client.direct_messages.return_value = [msg]
        thread = _make_thread("thread_1")
        last_seen: dict = {}

        results = list(self.client.iter_new_messages(thread, last_seen))

        assert len(results) == 1
        assert results[0][0].text == "Hello bot!"
        assert results[0][1] == "other_user"

    def test_skips_own_messages(self):
        msg = _make_message("msg_1", "bot_pk", "I said this")
        self.client._client.direct_messages.return_value = [msg]
        thread = _make_thread("thread_1")
        last_seen: dict = {}

        results = list(self.client.iter_new_messages(thread, last_seen))

        assert results == []

    def test_skips_already_seen_messages(self):
        msg = _make_message("msg_1", "other_user", "Old message")
        self.client._client.direct_messages.return_value = [msg]
        thread = _make_thread("thread_1")
        last_seen = {"thread_1": "msg_1"}

        results = list(self.client.iter_new_messages(thread, last_seen))

        assert results == []

    def test_updates_last_seen_id(self):
        msg = _make_message("msg_99", "other_user", "New!")
        self.client._client.direct_messages.return_value = [msg]
        thread = _make_thread("thread_1")
        last_seen: dict = {}

        list(self.client.iter_new_messages(thread, last_seen))

        assert last_seen["thread_1"] == "msg_99"

    def test_skips_messages_without_text(self):
        msg = _make_message("msg_1", "other_user", None)
        self.client._client.direct_messages.return_value = [msg]
        thread = _make_thread("thread_1")
        last_seen: dict = {}

        results = list(self.client.iter_new_messages(thread, last_seen))

        assert results == []

    def test_multiple_new_messages_returned_in_order(self):
        msgs = [
            _make_message("msg_3", "user_a", "Third"),
            _make_message("msg_2", "user_a", "Second"),
            _make_message("msg_1", "user_a", "First"),
        ]
        self.client._client.direct_messages.return_value = msgs
        thread = _make_thread("thread_1")
        last_seen: dict = {}

        results = list(self.client.iter_new_messages(thread, last_seen))

        # Should come back oldest-first
        texts = [r[0].text for r in results]
        assert texts == ["First", "Second", "Third"]


class TestSendMessage:
    def test_calls_direct_send(self):
        client = _make_client()

        client.send_message("thread_42", "Hello!")

        client._client.direct_send.assert_called_once_with(
            "Hello!", thread_ids=["thread_42"]
        )
