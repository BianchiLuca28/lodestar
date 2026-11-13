"""Turn pending inbound messages into drafts with the parse graph (design §6.1)."""

import logging
from datetime import UTC, datetime

from langchain_core.language_models import BaseChatModel

from lodestar.adapters.db.drafts_repo import DraftRepository
from lodestar.adapters.db.examples_index import ExampleIndex
from lodestar.adapters.db.inbound_repo import InboundRepository
from lodestar.ai.graphs.parse_message import ParseContext, Retriever, parse_message

log = logging.getLogger(__name__)

PARSED_KINDS = ("text", "photo")  # a photo's caption is parsed; receipts themselves come in v0.4


def parse_pending(
    model: BaseChatModel,
    ctx: ParseContext,
    inbound: InboundRepository,
    drafts: DraftRepository,
    retriever: Retriever | None = None,
) -> int:
    """Draft every pending message; stop at the first model failure and retry next time."""
    created = 0
    for message in inbound.pending():
        assert message.id is not None
        if message.kind not in PARSED_KINDS or not message.text:
            continue  # button presses and bare files are handled elsewhere
        sent_at = message.sent_at if message.sent_at.tzinfo else message.sent_at.replace(tzinfo=UTC)
        try:
            result = parse_message(model, ctx, message.text, sent_at, retriever)
        except Exception:
            log.exception("parsing failed; message %s stays pending", message.id)
            break
        drafts.create(
            result.lines,
            source="telegram",
            origin_text=message.text,
            review_note=result.review_note,
            inbound_message_id=message.id,
        )
        inbound.mark_processed(message.id, datetime.now(UTC))
        created += 1
    return created


def safe_sync(index: ExampleIndex) -> int:
    """Embed new transactions into the example index; a down embedder only delays it."""
    try:
        return index.sync()
    except Exception:
        log.warning("example index sync failed; retrying later", exc_info=True)
        return 0
