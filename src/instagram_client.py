"""Instagram API wrapper built on top of *instagrapi*."""

import logging
from pathlib import Path
from typing import Iterator

from instagrapi import Client
from instagrapi.types import DirectMessage, DirectThread

logger = logging.getLogger(__name__)

_SESSION_FILE = Path("session.json")


class InstagramClient:
    """Thin wrapper around *instagrapi* Client that adds session persistence
    and a convenient message-polling interface."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._client = Client()
        self._logged_in = False

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self) -> None:
        """Login to Instagram, reusing a saved session when available."""
        if _SESSION_FILE.exists():
            try:
                self._client.load_settings(_SESSION_FILE)
                self._client.login(self._username, self._password)
                logger.info("Resumed existing Instagram session.")
            except Exception:
                logger.warning(
                    "Saved session is stale – logging in fresh.", exc_info=True
                )
                self._fresh_login()
        else:
            self._fresh_login()
        self._logged_in = True

    def _fresh_login(self) -> None:
        self._client.login(self._username, self._password)
        self._client.dump_settings(_SESSION_FILE)
        logger.info("Logged in and saved session to %s.", _SESSION_FILE)

    # ------------------------------------------------------------------
    # Inbox helpers
    # ------------------------------------------------------------------

    def get_pending_threads(self, amount: int = 20) -> list[DirectThread]:
        """Return the *amount* most-recent direct-message threads."""
        return self._client.direct_threads(amount=amount)

    def get_thread_messages(
        self, thread_id: str, amount: int = 20
    ) -> list[DirectMessage]:
        """Return up to *amount* messages from *thread_id*, newest first."""
        return self._client.direct_messages(thread_id, amount=amount)

    def iter_new_messages(
        self, thread: DirectThread, last_seen_ids: dict[str, str]
    ) -> Iterator[tuple[DirectMessage, str]]:
        """Yield *(message, sender_user_id)* tuples for messages not yet seen.

        Only messages from other users (not the bot itself) are yielded.

        Args:
            thread: The DirectThread to inspect.
            last_seen_ids: Mapping of thread_id -> last processed message id.
                           Updated in-place as messages are yielded.
        """
        messages = self.get_thread_messages(thread.id)
        bot_pk = str(self._client.user_id)
        last_id = last_seen_ids.get(thread.id)

        new_messages: list[tuple[DirectMessage, str]] = []
        for msg in messages:
            msg_id = str(msg.id)
            if msg_id == last_id:
                break
            sender_id = str(msg.user_id)
            if sender_id != bot_pk and msg.text:
                new_messages.append((msg, sender_id))

        # Process oldest first so context is maintained in order
        for msg, sender_id in reversed(new_messages):
            yield msg, sender_id

        if messages:
            last_seen_ids[thread.id] = str(messages[0].id)

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send_message(self, thread_id: str, text: str) -> None:
        """Send *text* to the direct-message thread identified by *thread_id*."""
        self._client.direct_send(text, thread_ids=[thread_id])
        logger.debug("Sent reply to thread %s.", thread_id)
