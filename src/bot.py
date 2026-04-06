"""Main entry-point for the AI-powered Instagram chatbot.

Run with:
    python -m src.bot

The bot logs into Instagram, then continuously polls the DM inbox.
For every new incoming message it generates an AI reply via OpenAI and
sends it back to the sender.
"""

import logging
import time

import src.config as config
from src.ai_responder import AIResponder
from src.instagram_client import InstagramClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    """Start the chatbot polling loop."""
    ig = InstagramClient(config.INSTAGRAM_USERNAME, config.INSTAGRAM_PASSWORD)
    ai = AIResponder(
        api_key=config.OPENAI_API_KEY,
        model=config.OPENAI_MODEL,
        system_prompt=config.BOT_SYSTEM_PROMPT,
        max_history=config.MAX_HISTORY,
    )

    logger.info("Logging into Instagram as @%s …", config.INSTAGRAM_USERNAME)
    ig.login()
    logger.info("Login successful. Polling every %d seconds.", config.POLL_INTERVAL)

    # Maps thread_id -> id of the last message we have already handled
    last_seen_ids: dict[str, str] = {}

    while True:
        try:
            _process_inbox(ig, ai, last_seen_ids)
        except Exception:
            logger.exception("Error while processing inbox – will retry.")

        time.sleep(config.POLL_INTERVAL)


def _process_inbox(
    ig: InstagramClient,
    ai: AIResponder,
    last_seen_ids: dict[str, str],
) -> None:
    """Fetch recent threads and reply to any new messages."""
    threads = ig.get_pending_threads()
    for thread in threads:
        for msg, sender_id in ig.iter_new_messages(thread, last_seen_ids):
            logger.info(
                "New message in thread %s from user %s: %r",
                thread.id,
                sender_id,
                msg.text,
            )
            reply = ai.get_reply(user_id=sender_id, incoming_text=msg.text)
            ig.send_message(thread.id, reply)
            logger.info("Replied to user %s: %r", sender_id, reply)


if __name__ == "__main__":
    run()
