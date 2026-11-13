"""Telegram Bot API: the client and the parsing of raw updates (design §7, ADR 0019)."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, Protocol

import httpx

Kind = Literal["text", "photo", "document", "callback"]


@dataclass(frozen=True)
class ParsedUpdate:
    update_id: int
    kind: Kind
    user_id: int
    chat_id: int
    message_id: int | None
    text: str | None
    file_id: str | None
    sent_at: datetime


def _sent_at(message: dict[str, Any]) -> datetime:
    return datetime.fromtimestamp(int(message["date"]), tz=UTC)


def parse_update(update: dict[str, Any]) -> ParsedUpdate | None:
    """The fields Lodestar keeps from an update, or None for kinds it does not handle."""
    update_id = int(update["update_id"])
    if callback := update.get("callback_query"):
        message = callback.get("message") or {}
        return ParsedUpdate(
            update_id=update_id,
            kind="callback",
            user_id=int(callback["from"]["id"]),
            chat_id=int(message.get("chat", {}).get("id", callback["from"]["id"])),
            message_id=message.get("message_id"),
            text=callback.get("data"),
            file_id=None,
            sent_at=_sent_at(message) if "date" in message else datetime.now(UTC),
        )
    message = update.get("message")
    if not message or "from" not in message:
        return None
    kind: Kind
    if "text" in message:
        kind, file_id, text = "text", None, message["text"]
    elif message.get("photo"):
        kind, file_id, text = "photo", message["photo"][-1]["file_id"], message.get("caption")
    elif "document" in message:
        kind, file_id, text = "document", message["document"]["file_id"], message.get("caption")
    else:
        return None
    return ParsedUpdate(
        update_id=update_id,
        kind=kind,
        user_id=int(message["from"]["id"]),
        chat_id=int(message["chat"]["id"]),
        message_id=message.get("message_id"),
        text=text,
        file_id=file_id,
        sent_at=_sent_at(message),
    )


class TelegramClient(Protocol):
    def get_updates(self, offset: int | None, timeout: int) -> list[dict[str, Any]]: ...

    def send_message(self, chat_id: int, text: str) -> None: ...


class HttpTelegramClient:
    """Long polling over the Bot API; the PC opens no inbound port."""

    def __init__(self, token: str, base_url: str = "https://api.telegram.org") -> None:
        self._url = f"{base_url}/bot{token}"

    def _call(self, method: str, payload: dict[str, Any], timeout: float) -> Any:
        response = httpx.post(f"{self._url}/{method}", json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()["result"]

    def get_updates(self, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            payload["offset"] = offset
        result: list[dict[str, Any]] = self._call("getUpdates", payload, timeout + 10)
        return result

    def send_message(self, chat_id: int, text: str) -> None:
        self._call("sendMessage", {"chat_id": chat_id, "text": text}, 10)
