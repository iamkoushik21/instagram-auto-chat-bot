"""AI-powered response generator using the OpenAI Chat Completions API."""

import logging
from collections import defaultdict, deque
from typing import Deque

from openai import OpenAI

logger = logging.getLogger(__name__)


class AIResponder:
    """Generates replies for incoming Instagram messages using OpenAI GPT."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        system_prompt: str = "You are a friendly and helpful Instagram assistant.",
        max_history: int = 10,
    ) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._system_prompt = system_prompt
        self._max_history = max_history
        # Per-user conversation history: user_id -> deque of {"role": ..., "content": ...}
        self._histories: dict[str, Deque[dict]] = defaultdict(
            lambda: deque(maxlen=self._max_history * 2)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_reply(self, user_id: str, incoming_text: str) -> str:
        """Return an AI-generated reply for *incoming_text* from *user_id*.

        Conversation history is maintained per *user_id* so that context is
        preserved across multiple turns.

        Args:
            user_id: Unique identifier for the conversation partner (Instagram user PK).
            incoming_text: The message text received from the user.

        Returns:
            The AI-generated reply string.
        """
        history = self._histories[user_id]
        history.append({"role": "user", "content": incoming_text})

        messages = [{"role": "system", "content": self._system_prompt}, *list(history)]

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
            reply = response.choices[0].message.content.strip()
        except Exception:
            logger.exception("OpenAI API call failed for user %s", user_id)
            raise

        history.append({"role": "assistant", "content": reply})
        return reply

    def clear_history(self, user_id: str) -> None:
        """Clear the conversation history for *user_id*."""
        self._histories.pop(user_id, None)

    def clear_all_histories(self) -> None:
        """Clear all stored conversation histories."""
        self._histories.clear()
