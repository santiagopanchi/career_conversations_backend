"""Pushover notification functions."""
import requests
from config import get_env


def push(text: str) -> None:
    """Send a push notification via Pushover."""
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": get_env("PUSHOVER_TOKEN"),
            "user": get_env("PUSHOVER_USER"),
            "message": text,
        }
    )

