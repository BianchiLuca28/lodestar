"""The real parser behind the eval runner (`make eval ARGS=--live`)."""

from datetime import datetime

from langchain_core.language_models import BaseChatModel

from lodestar.ai.evals.schema import Line
from lodestar.ai.graphs.parse_message import PROMPT_VERSION, ParseContext, parse_message


class GraphPredictor:
    def __init__(self, model: BaseChatModel, model_name: str, ctx: ParseContext) -> None:
        self._model = model
        self._ctx = ctx
        self.model = model_name
        self.prompt_version = f"parse-v{PROMPT_VERSION}"

    def predict(self, message: str, sent_at: datetime) -> list[Line]:
        result = parse_message(self._model, self._ctx, message, sent_at)
        return [
            Line(
                date=line.date,
                amount=line.amount,
                from_account=line.from_account,
                to_account=line.to_account,
                category=line.category,
                subcategory=line.subcategory,
                note=line.note,
                tag=line.tag,
            )
            for line in result.lines
        ]
