"""Run the parsing eval set and save the metrics per model and prompt version.

Usage: uv run python -m lodestar.ai.evals.runner [--dataset PATH] [--results DIR] [--compare]
"""

import argparse
import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from lodestar.ai.evals.metrics import score
from lodestar.ai.evals.predictor import Predictor, ScriptedPredictor
from lodestar.ai.evals.schema import Case, load_cases

REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_DATASET = REPO_ROOT / "evals" / "datasets" / "parsing" / "cases.jsonl"
DEFAULT_RESULTS = REPO_ROOT / "evals" / "results"


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ".-" else "-" for ch in text)


def _previous(results_dir: Path, exclude: Path) -> dict[str, float] | None:
    files = sorted(p for p in results_dir.glob("*.json") if p != exclude)
    if not files:
        return None
    metrics: dict[str, float] = json.loads(files[-1].read_text("utf-8"))["metrics"]
    return metrics


def _table(after: dict[str, float], before: dict[str, float] | None) -> str:
    if before is None:
        rows = ["| Metric | Value |", "| --- | --- |"]
        rows += [f"| {k} | {v:.3f} |" for k, v in after.items()]
    else:
        rows = ["| Metric | Before | After |", "| --- | --- | --- |"]
        rows += [
            f"| {k} | {before[k]:.3f} | {v:.3f} |" if k in before else f"| {k} | – | {v:.3f} |"
            for k, v in after.items()
        ]
    return "\n".join(rows)


def run(
    cases: Sequence[Case],
    predictor: Predictor,
    results_dir: Path,
    today: date,
    compare: bool = False,
) -> tuple[Path, str]:
    pairs = [(c.expected, predictor.predict(c.message, c.sent_at)) for c in cases]
    metrics = score(pairs)
    results_dir.mkdir(parents=True, exist_ok=True)
    name = f"{today.isoformat()}_{_slug(predictor.model)}_{_slug(predictor.prompt_version)}.json"
    path = results_dir / name
    before = _previous(results_dir, exclude=path) if compare else None
    payload = {
        "date": today.isoformat(),
        "model": predictor.model,
        "prompt_version": predictor.prompt_version,
        "cases": len(cases),
        "metrics": metrics,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path, _table(metrics, before)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--compare", action="store_true", help="show before/after vs last result")
    args = parser.parse_args()
    cases = load_cases(args.dataset)
    # Until the v0.2 parser exists, the only predictor is the scripted fake.
    predictor = ScriptedPredictor.from_cases(cases)
    path, table = run(cases, predictor, args.results, date.today(), compare=args.compare)
    print(table)
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
