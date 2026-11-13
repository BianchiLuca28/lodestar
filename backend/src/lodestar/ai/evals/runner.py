"""Run the parsing eval set and save the metrics per model and prompt version.

Usage: uv run python -m lodestar.ai.evals.runner [--dataset PATH] [--results DIR] [--compare]
       [--live [--config DIR] [--model NAME]]

Without --live the scripted fake answers (CI); with --live the real graph calls the LLM.
"""

import argparse
import json
import tempfile
import time
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from lodestar.ai.evals.metrics import score
from lodestar.ai.evals.predictor import Predictor, ScriptedPredictor
from lodestar.ai.evals.schema import Case, load_cases

REPO_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_DATASET = REPO_ROOT / "evals" / "datasets" / "parsing" / "cases.jsonl"
DEFAULT_RESULTS = REPO_ROOT / "evals" / "results"
DEFAULT_CONFIG = REPO_ROOT / "config.example"  # the eval cases use the fake persona


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
    started = time.perf_counter()
    pairs = [(c.expected, predictor.predict(c)) for c in cases]
    elapsed = time.perf_counter() - started
    metrics = score(pairs)
    metrics["seconds_per_case"] = elapsed / len(cases) if cases else 0.0  # addition to §6.5
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


def _live(config_dir: Path, model: str | None, examples: bool, work_dir: Path) -> Predictor:
    from lodestar.adapters.embeddings import OpenAICompatEmbedder
    from lodestar.adapters.llm import chat_model
    from lodestar.ai.evals.graph_predictor import GraphPredictor, fake_ledger_index
    from lodestar.ai.graphs.parse_message import ParseContext
    from lodestar.config.loader import load_config
    from lodestar.config.settings import Settings

    config = load_config(config_dir)
    name = model or config.settings.models.parse
    base_url = Settings.from_config(config).llm_base_url
    index = None
    if examples:
        embed = config.settings.models.embed
        embedder = OpenAICompatEmbedder(base_url, embed)
        index = fake_ledger_index(config_dir, work_dir, embedder, embed)
    ctx = ParseContext.from_config(config)
    return GraphPredictor(chat_model(base_url, name), name, ctx, index)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--compare", action="store_true", help="show before/after vs last result")
    parser.add_argument("--live", action="store_true", help="run the real parse graph")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--model", help="override models.parse")
    parser.add_argument(
        "--no-examples", action="store_true", help="parse without few-shot retrieval"
    )
    args = parser.parse_args()
    cases = load_cases(args.dataset)
    predictor: Predictor = ScriptedPredictor.from_cases(cases)
    with tempfile.TemporaryDirectory() as work_dir:
        if args.live:
            predictor = _live(args.config, args.model, not args.no_examples, Path(work_dir))
        path, table = run(cases, predictor, args.results, date.today(), compare=args.compare)
    print(table)
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
