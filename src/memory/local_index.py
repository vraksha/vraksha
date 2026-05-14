"""
Local-First Persistent Memory Layer for Vraksha.

This module provides a hybrid storage solution combining:
1. Raw Filesystem Logs (Durable & Immutable)
2. SQLite FTS5 Index (High-Performance Keyword Retrieval)
3. In-Memory Hot Cache (Zero-Latency Short-Term Recall)

Architecture:
- I/O: Asynchronous background writes for non-critical logs.
- Retrieval: Diversified BM25 ranking with trust-based gating.
- Scalability: Streaming chunking for large file indexing.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from get_root import root

logger = logging.getLogger(__name__)

MEMORY_ROOT = root.project / "memory"
INDEX_DB = MEMORY_ROOT / "index" / "memory.sqlite3"
MAX_FILE_BYTES = 64 * 1024
MAX_CHUNK_CHARS = 1800
CHUNK_OVERLAP = 180
MAX_ESSENTIAL_CHARS = 18_000
MAX_HOT_CACHE = 16
MAX_RESULTS = 8
TOKEN_RE = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{1,}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def atomic_append(path: Path, text: str) -> None:
    """Synchronous fallback for critical atomic appends."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())


class AsyncJournalWriter:
    """
    Prevents blocking the main execution loop by offloading journal appends
    to a background worker. This ensures that even slow disk I/O doesn't 
    impact the agent's responsiveness.
    """
    def __init__(self):
        self._queue: asyncio.Queue[tuple[Path, str]] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None

    def start(self):
        """Initializes the background worker task if not already running."""
        if not self._worker_task:
            self._worker_task = asyncio.create_task(self._worker())

    async def _worker(self):
        """Continuous loop processing pending disk writes."""
        while True:
            try:
                path, text = await self._queue.get()
                # Use to_thread to keep the event loop free during blocking I/O
                await asyncio.to_thread(atomic_append, path, text)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory journal write failure: {e}", exc_info=True)

    def append(self, path: Path, text: str):
        """Queues a new line for the journal. Non-blocking."""
        self._queue.put_nowait((path, text))


# Global singleton for background logging
_journal_writer = AsyncJournalWriter()


def bounded_read_text(path: Path, max_bytes: int = MAX_FILE_BYTES) -> str:
    raw = path.read_bytes()[:max_bytes]
    text = raw.decode("utf-8", errors="replace")

    if path.stat().st_size > max_bytes:
        text += "\n...[truncated: indexed search holds the full file]"

    return text


def chunk_text_stream(path: Path, size: int = MAX_CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> Iterable[tuple[int, str]]:
    """Generative chunking to handle multi-GB files without memory spikes."""
    idx = 0
    buffer = ""

    with path.open("r", encoding="utf-8", errors="replace") as f:
        while True:
            chunk = f.read(size * 4) # Read ahead buffer

            if not chunk:
                break

            buffer += chunk

            while len(buffer) > size:
                boundary = max(buffer.rfind("\n\n", 0, size), buffer.rfind(". ", 0, size))
                end = boundary + 1 if boundary > size // 2 else size
                
                yield idx, buffer[:end].strip()
                buffer = buffer[end - overlap:]
                idx += 1

        if buffer.strip():
            yield idx, buffer.strip()


@dataclass(slots=True)
class MemoryRecord:
    source_id: str
    kind: str
    title: str
    content: str
    trust: float = 0.55
    pinned: bool = False
    valid_until: str | None = None
    metadata: dict[str, Any] | None = None


class LocalFirstMemory:
    """Local filesystem + SQLite FTS5 memory layer.

    Raw durable files stay under memory/. Retrieval uses a local SQLite FTS5
    index with trust/validity gates so prompt context is bounded and curated.
    """

    def __init__(self, db_path: Path = INDEX_DB, memory_root: Path = MEMORY_ROOT) -> None:
        self.db_path = Path(db_path)
        self.memory_root = Path(memory_root)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory_root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._hot_cache: list[MemoryRecord] = []
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._configure()
        self._ensure_schema()

    def _configure(self) -> None:
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA temp_store=MEMORY")
        self._conn.execute("PRAGMA mmap_size=268435456") # 256MB mmap for high-speed indexing
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        _journal_writer.start()

    def _ensure_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                  id INTEGER PRIMARY KEY,
                  doc_key TEXT NOT NULL UNIQUE,
                  source_id TEXT NOT NULL,
                  source_path TEXT,
                  kind TEXT NOT NULL,
                  title TEXT NOT NULL,
                  chunk_index INTEGER NOT NULL DEFAULT 0,
                  content TEXT NOT NULL,
                  content_hash TEXT NOT NULL,
                  trust REAL NOT NULL DEFAULT 0.55,
                  pinned INTEGER NOT NULL DEFAULT 0,
                  valid_until TEXT,
                  metadata_json TEXT NOT NULL DEFAULT '{}',
                  access_count INTEGER NOT NULL DEFAULT 0,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );

                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                  title, content, kind, source_id,
                  content='documents', content_rowid='id',
                  tokenize='unicode61 remove_diacritics 2'
                );

                CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                  INSERT INTO documents_fts(rowid, title, content, kind, source_id)
                  VALUES (new.id, new.title, new.content, new.kind, new.source_id);
                END;
                CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                  INSERT INTO documents_fts(documents_fts, rowid, title, content, kind, source_id)
                  VALUES('delete', old.id, old.title, old.content, old.kind, old.source_id);
                END;
                CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                  INSERT INTO documents_fts(documents_fts, rowid, title, content, kind, source_id)
                  VALUES('delete', old.id, old.title, old.content, old.kind, old.source_id);
                  INSERT INTO documents_fts(rowid, title, content, kind, source_id)
                  VALUES (new.id, new.title, new.content, new.kind, new.source_id);
                END;

                CREATE TABLE IF NOT EXISTS source_state (
                  source_path TEXT PRIMARY KEY,
                  mtime_ns INTEGER NOT NULL,
                  size_bytes INTEGER NOT NULL,
                  indexed_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_documents_gate
                  ON documents(kind, pinned, trust, valid_until, updated_at);
                CREATE INDEX IF NOT EXISTS idx_documents_source
                  ON documents(source_id, source_path, chunk_index);
                """
            )
            self._conn.commit()

    def core_files(self) -> list[tuple[Path, str, float, bool]]:
        return [
            (self.memory_root / "soul.md", "core", 0.99, True),
            (self.memory_root / "rules.md", "core", 0.99, True),
            (self.memory_root / "agent" / "memory.yaml", "summary", 0.75, False),
            (self.memory_root / "agent" / "projects.yaml", "project", 0.80, False),
            (self.memory_root / "agent" / "journal.md", "episode", 0.45, False),
            (self.memory_root / "agent" / "journal.jsonl", "episode", 0.45, False),
            (self.memory_root / "wiki" / "WIKI.md", "wiki", 0.70, False),
        ]

    async def bootstrap(self) -> None:
        for path, kind, trust, pinned in self.core_files():
            if path.exists():
                await self.index_file(path, kind=kind, trust=trust, pinned=pinned)

    def bootstrap_sync(self) -> None:
        for path, kind, trust, pinned in self.core_files():
            if path.exists():
                self._index_file_sync(path, kind, trust, pinned)

    async def index_file(self, path: Path, *, kind: str, trust: float, pinned: bool = False) -> None:
        await asyncio.to_thread(self._index_file_sync, Path(path), kind, trust, pinned)

    def _index_file_sync(self, path: Path, kind: str, trust: float, pinned: bool) -> None:
        stat = path.stat()
        with self._lock:
            state = self._conn.execute(
                "SELECT mtime_ns, size_bytes FROM source_state WHERE source_path = ?", (path.as_posix(),)
            ).fetchone()

        if state and int(state["mtime_ns"]) == stat.st_mtime_ns and int(state["size_bytes"]) == stat.st_size:
            return

        now = utc_now()
        rel = path.as_posix()

        try:
            rel = path.relative_to(self.memory_root.parent).as_posix()
        except ValueError:
            pass

        with self._lock:
            self._conn.execute("BEGIN") # Non-immediate to allow concurrent reads during indexing
            try:
                self._conn.execute("DELETE FROM documents WHERE source_path = ?", (path.as_posix(),))
                # Stream chunks instead of reading full text
                for idx, chunk in chunk_text_stream(path):
                    self._insert_record(
                        doc_key=f"file:{path.as_posix()}:{idx}",
                        source_id=rel,
                        source_path=path.as_posix(),
                        kind=kind,
                        title=path.name,
                        chunk_index=idx,
                        content=chunk,
                        trust=trust,
                        pinned=pinned,
                        valid_until=None,
                        metadata={"bytes": stat.st_size},
                        now=now,
                    )
                self._conn.execute(
                    "INSERT OR REPLACE INTO source_state(source_path, mtime_ns, size_bytes, indexed_at) VALUES (?, ?, ?, ?)",
                    (path.as_posix(), stat.st_mtime_ns, stat.st_size, now),
                )
                self._conn.commit()

            except Exception:
                self._conn.rollback()
                raise

    async def remember_many(self, records: list[MemoryRecord]) -> None:
        await asyncio.to_thread(self.remember_many_sync, records)

    def remember_many_sync(self, records: list[MemoryRecord]) -> None:
        now = utc_now()

        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")

            try:
                for record in records:
                    self._hot_cache.append(record)
                    # Inline helper for chunking string content
                    start = 0
                    idx = 0

                    while start < len(record.content):
                        end = min(len(record.content), start + MAX_CHUNK_CHARS)
                        chunk = record.content[start:end].strip()

                        if chunk:
                            self._insert_record(
                                doc_key=f"event:{record.source_id}:{sha256_text(record.content)}:{idx}",
                                source_id=record.source_id,
                                source_path=None,
                                kind=record.kind,
                                title=record.title,
                                chunk_index=idx,
                                content=chunk,
                                trust=record.trust,
                                pinned=record.pinned,
                                valid_until=record.valid_until,
                                metadata=record.metadata or {},
                                now=now,
                            )
                            idx += 1

                        start = max(0, end - CHUNK_OVERLAP) if end < len(record.content) else len(record.content)
                    
                    _journal_writer.append(self.memory_root / "agent" / "journal.jsonl", json.dumps({
                        "time": now, "kind": record.kind, "title": record.title,
                        "content": record.content, "trust": record.trust,
                    }, ensure_ascii=False) + "\n")
                
                self._conn.commit()
                del self._hot_cache[:-MAX_HOT_CACHE]

            except Exception:
                self._conn.rollback()
                raise

    def remember_sync(self, record: MemoryRecord) -> None:
        self.remember_many_sync([record])

    def _insert_record(self, **kw: Any) -> None:
        self._conn.execute(
            """
            INSERT INTO documents(
              doc_key, source_id, source_path, kind, title, chunk_index, content,
              content_hash, trust, pinned, valid_until, metadata_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(doc_key) DO UPDATE SET
              source_id=excluded.source_id,
              source_path=excluded.source_path,
              kind=excluded.kind,
              title=excluded.title,
              chunk_index=excluded.chunk_index,
              content=excluded.content,
              content_hash=excluded.content_hash,
              trust=excluded.trust,
              pinned=excluded.pinned,
              valid_until=excluded.valid_until,
              metadata_json=excluded.metadata_json,
              updated_at=excluded.updated_at
            """,
            (
                kw["doc_key"], kw["source_id"], kw["source_path"], kw["kind"], kw["title"],
                kw["chunk_index"], kw["content"], sha256_text(kw["content"]), float(kw["trust"]),
                int(bool(kw["pinned"])), kw["valid_until"], json.dumps(kw["metadata"], ensure_ascii=False),
                kw["now"], kw["now"],
            ),
        )

    async def search(self, query: str, *, limit: int = MAX_RESULTS, min_trust: float = 0.35, kinds: Sequence[str] | None = None) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self.search_sync, query, limit=limit, min_trust=min_trust, kinds=kinds)

    def search_sync(self, query: str, *, limit: int = MAX_RESULTS, min_trust: float = 0.35, kinds: Sequence[str] | None = None) -> list[dict[str, Any]]:
        self.bootstrap_sync()
        return self._search_sync(query, limit, min_trust, tuple(kinds or ()))

    def _search_sync(self, query: str, limit: int, min_trust: float, kinds: tuple[str, ...]) -> list[dict[str, Any]]:
        # Sanitize query: extract alphanumeric tokens and prevent FTS syntax injection
        tokens = TOKEN_RE.findall(query.lower())[:10]
        if not tokens:
            return []
            
        # Build FTS5 query using OR for maximum recall; BM25 will handle the ranking
        fts_query = " OR ".join(f'"{t}"' for t in tokens)
        
        params: list[Any] = [fts_query, min_trust, utc_now()]
        kind_clause = ""
        if kinds:
            kind_clause = " AND d.kind IN (" + ",".join("?" for _ in kinds) + ")"
            params.extend(kinds)
        
        # We fetch more than requested to allow for diversification/deduplication
        params.append(max(limit * 4, 32))

        with self._lock:
            try:
                rows = self._conn.execute(
                    f"""
                    SELECT d.id, d.doc_key, d.source_id, d.kind, d.title, d.content, d.trust,
                           d.pinned, d.valid_until, d.metadata_json, d.updated_at,
                           bm25(documents_fts) AS rank
                    FROM documents_fts
                    JOIN documents d ON d.id = documents_fts.rowid
                    WHERE documents_fts MATCH ?
                      AND (d.pinned = 1 OR d.trust >= ?)
                      AND (d.valid_until IS NULL OR d.valid_until > ?)
                      {kind_clause}
                    ORDER BY d.pinned DESC, d.trust DESC, rank ASC, d.updated_at DESC
                    LIMIT ?
                    """,
                    params,
                ).fetchall()

                selected = self._diversify(rows, limit)
                if selected:
                    # Update access statistics for future prioritization/caching logic
                    self._conn.executemany(
                        "UPDATE documents SET access_count = access_count + 1 WHERE id = ?", 
                        [(r["id"],) for r in selected]
                    )
                    self._conn.commit()
                return [self._row_to_dict(r) for r in selected]
            except sqlite3.Error as e:
                logger.error(f"Search failed: {e}")
                return []

    @staticmethod
    def _diversify(rows: Sequence[sqlite3.Row], limit: int) -> list[sqlite3.Row]:
        out: list[sqlite3.Row] = []
        seen_hashes: set[str] = set()
        per_source: dict[str, int] = {}

        for row in rows:
            content_hash = sha256_text(row["content"][:1000])

            if content_hash in seen_hashes:
                continue

            count = per_source.get(row["source_id"], 0)

            if count >= 2 and not row["pinned"]:
                continue

            seen_hashes.add(content_hash)
            per_source[row["source_id"]] = count + 1
            out.append(row)

            if len(out) >= limit:
                break

        return out

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "doc_key": row["doc_key"],
            "source": row["source_id"],
            "kind": row["kind"],
            "title": row["title"],
            "content": row["content"],
            "trust": float(row["trust"]),
            "pinned": bool(row["pinned"]),
            "valid_until": row["valid_until"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
            "updated_at": row["updated_at"],
            "rank": float(row["rank"] or 0.0),
        }

    async def essential_context(self, user_query: str = "") -> str:
        return await asyncio.to_thread(self.essential_context_sync, user_query)

    def essential_context_sync(self, user_query: str = "") -> str:
        self.bootstrap_sync()
        core_parts = []

        for path in [self.memory_root / "soul.md", self.memory_root / "rules.md"]:
            if path.exists():
                core_parts.append(f"From {path.name}:\n{bounded_read_text(path)}")

        hot = [f"- {r.kind}: {r.content[:500]}" for r in self._hot_cache[-MAX_HOT_CACHE:]]
        hits = self.search_sync(user_query, limit=6) if user_query else []
        retrieved = [f"- [{h['kind']} trust={h['trust']:.2f} source={h['source']}] {h['content']}" for h in hits]
        text = "\n\n".join(core_parts) if core_parts else "No essential memory found."

        if hot:
            text += "\n\nSession hot-cache:\n" + "\n".join(hot)

        if retrieved:
            text += "\n\nRetrieved memory:\n" + "\n".join(retrieved)

        return text[:MAX_ESSENTIAL_CHARS]


_default_memory: LocalFirstMemory | None = None
_default_lock = threading.RLock()


def get_memory() -> LocalFirstMemory:
    global _default_memory

    with _default_lock:
        if _default_memory is None:
            _default_memory = LocalFirstMemory()

        return _default_memory
