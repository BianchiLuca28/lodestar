from datetime import UTC, datetime

from lodestar.adapters.telegram import parse_update

USER = 42


def message(**extra: object) -> dict[str, object]:
    return {
        "message_id": 7,
        "from": {"id": USER},
        "chat": {"id": 1000},
        "date": 1773512400,  # 2026-03-14 18:20 UTC
        **extra,
    }


def test_text_message() -> None:
    parsed = parse_update({"update_id": 5, "message": message(text="pizza 12€")})
    assert parsed is not None
    assert (parsed.update_id, parsed.kind, parsed.user_id, parsed.chat_id) == (
        5,
        "text",
        USER,
        1000,
    )
    assert parsed.text == "pizza 12€"
    assert parsed.sent_at == datetime(2026, 3, 14, 18, 20, tzinfo=UTC)


def test_photo_keeps_the_largest_size_and_caption() -> None:
    photo = [{"file_id": "small"}, {"file_id": "big"}]
    parsed = parse_update({"update_id": 6, "message": message(photo=photo, caption="scontrino")})
    assert parsed is not None
    assert (parsed.kind, parsed.file_id, parsed.text) == ("photo", "big", "scontrino")


def test_document() -> None:
    parsed = parse_update({"update_id": 7, "message": message(document={"file_id": "doc"})})
    assert parsed is not None
    assert (parsed.kind, parsed.file_id) == ("document", "doc")


def test_button_press() -> None:
    callback = {"id": "cb", "from": {"id": USER}, "data": "approve:3", "message": message()}
    parsed = parse_update({"update_id": 8, "callback_query": callback})
    assert parsed is not None
    assert (parsed.kind, parsed.text, parsed.chat_id) == ("callback", "approve:3", 1000)


def test_other_update_types_are_ignored() -> None:
    assert parse_update({"update_id": 9, "edited_message": message(text="x")}) is None
    assert parse_update({"update_id": 10, "message": message(sticker={"file_id": "s"})}) is None
