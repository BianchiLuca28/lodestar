"""What the eval runner calls: a message in, proposed lines out.

The real LangGraph parser implements `Predictor` in v0.2.
"""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Protocol

from lodestar.ai.evals.schema import Case, Line


class Predictor(Protocol):
    model: str
    prompt_version: str

    def predict(self, message: str, sent_at: datetime) -> list[Line]: ...


class ScriptedPredictor:
    """Returns preset answers by message; unknown messages yield no lines."""

    def __init__(
        self,
        answers: Mapping[str, Sequence[Line]],
        model: str = "fake",
        prompt_version: str = "v0",
    ) -> None:
        self._answers = answers
        self.model = model
        self.prompt_version = prompt_version

    @classmethod
    def from_cases(cls, cases: Sequence[Case]) -> "ScriptedPredictor":
        """A perfect predictor: answers every case with its expected lines."""
        return cls({c.message: c.expected for c in cases})

    def predict(self, message: str, sent_at: datetime) -> list[Line]:
        return list(self._answers.get(message, []))
