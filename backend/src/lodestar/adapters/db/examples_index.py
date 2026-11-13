"""Few-shot example index: past transactions embedded and searched with sqlite-vec (design §6.1).

Each transaction with a note is embedded once per embedding model; `sync` fills the gaps, so it
runs at startup, after each poll and after every approval. Search is an exact cosine scan with
`vec_distance_cosine`, plenty for a personal ledger.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import sqlite_vec  # type: ignore[import-untyped]

from lodestar.adapters.embeddings import Embedder

BATCH = 64
CANDIDATES = 4  # fetch k × this many, then drop near-identical examples


@dataclass(frozen=True)
class Example:
    note: str
    category: str
    subcategory: str | None
    from_account: str | None
    to_account: str | None


class ExampleIndex:
    def __init__(self, db: Path, embedder: Embedder, model: str) -> None:
        self._db = db
        self._embedder = embedder
        self._model = model

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db)
        try:
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def sync(self) -> int:
        """Embed every transaction with a note that has no vector for the current model."""
        with self._connect() as conn:
            conn.execute("DELETE FROM transaction_embeddings WHERE model != ?", (self._model,))
            rows = conn.execute(
                "SELECT t.id, t.note FROM transactions t"
                " LEFT JOIN transaction_embeddings e ON e.transaction_id = t.id"
                " WHERE e.transaction_id IS NULL AND trim(coalesce(t.note, '')) != ''"
                " ORDER BY t.id"
            ).fetchall()
            for start in range(0, len(rows), BATCH):
                batch = rows[start : start + BATCH]
                vectors = self._embedder.embed([note for _, note in batch])
                conn.executemany(
                    "INSERT INTO transaction_embeddings (transaction_id, model, text, embedding)"
                    " VALUES (?, ?, ?, ?)",
                    [
                        (tx_id, self._model, note, sqlite_vec.serialize_float32(vector))
                        for (tx_id, note), vector in zip(batch, vectors, strict=True)
                    ],
                )
                conn.commit()  # a later failure keeps what was already embedded
            return len(rows)

    def nearest(self, text: str, k: int = 5) -> list[Example]:
        """The k past transactions whose note is closest to `text`, one per distinct mapping."""
        [vector] = self._embedder.embed([text])
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT t.note, t.category, t.subcategory, t.from_account, t.to_account"
                " FROM transaction_embeddings e JOIN transactions t ON t.id = e.transaction_id"
                " WHERE e.model = ?"
                " ORDER BY vec_distance_cosine(e.embedding, ?), t.date DESC LIMIT ?",
                (self._model, sqlite_vec.serialize_float32(vector), k * CANDIDATES),
            ).fetchall()
        examples: list[Example] = []
        seen: set[tuple[str, ...]] = set()
        for note, category, subcategory, from_account, to_account in rows:
            key = (note.strip().lower(), category, subcategory or "")
            if key in seen:
                continue
            seen.add(key)
            examples.append(Example(note, category, subcategory, from_account, to_account))
            if len(examples) == k:
                break
        return examples
