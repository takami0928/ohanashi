from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .schemas import MemoryCard, Settings

try:
    import sqlite3 as sqlite_module  # type: ignore
except Exception:
    sqlite_module = None


DEFAULT_DATA = {
    "settings": {},
    "memories": [],
    "usage": {},
}


class BaseStorage:
    driver = "base"

    def get_settings(self) -> Settings:
        raise NotImplementedError

    def save_settings(self, partial: Dict[str, object]) -> Settings:
        raise NotImplementedError

    def list_memories(self, now_iso: Optional[str] = None) -> List[MemoryCard]:
        raise NotImplementedError

    def upsert_memory(self, card: MemoryCard) -> MemoryCard:
        raise NotImplementedError

    def delete_memory(self, card_id: str) -> None:
        raise NotImplementedError

    def record_usage(self, day: str, seconds: int, mode: str) -> None:
        raise NotImplementedError

    def get_usage_summary(self, today: str, days: int = 7) -> Dict[str, object]:
        raise NotImplementedError


class JsonStorage(BaseStorage):
    driver = "json-fallback"

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        if not self.path.exists():
            self._write(DEFAULT_DATA)

    def get_settings(self) -> Settings:
        data = self._read()
        return Settings(**{**Settings().__dict__, **data.get("settings", {})})

    def save_settings(self, partial: Dict[str, object]) -> Settings:
        with self.lock:
            data = self._read()
            merged = {**Settings().__dict__, **data.get("settings", {}), **partial}
            data["settings"] = merged
            self._write(data)
        return Settings(**merged)

    def list_memories(self, now_iso: Optional[str] = None) -> List[MemoryCard]:
        with self.lock:
            data = self._read()
            memories = [MemoryCard(**item) for item in data.get("memories", [])]
            filtered = _purge_expired(memories, now_iso)
            if len(filtered) != len(memories):
                data["memories"] = [card.__dict__ for card in filtered]
                self._write(data)
            return filtered

    def upsert_memory(self, card: MemoryCard) -> MemoryCard:
        with self.lock:
            data = self._read()
            memories = [MemoryCard(**item) for item in data.get("memories", [])]
            by_slot = {f"{item.category}:{item.key}": item for item in memories}
            existing = by_slot.get(f"{card.category}:{card.key}")
            if existing:
                card.id = existing.id
                card.created_at = existing.created_at
            by_slot[f"{card.category}:{card.key}"] = card
            data["memories"] = [item.__dict__ for item in by_slot.values()]
            self._write(data)
        return card

    def delete_memory(self, card_id: str) -> None:
        with self.lock:
            data = self._read()
            data["memories"] = [item for item in data.get("memories", []) if item["id"] != card_id]
            self._write(data)

    def record_usage(self, day: str, seconds: int, mode: str) -> None:
        with self.lock:
            data = self._read()
            usage = data.setdefault("usage", {})
            day_entry = usage.setdefault(day, {"seconds": 0, "modes": {}})
            day_entry["seconds"] += max(seconds, 0)
            day_entry["modes"][mode] = int(day_entry["modes"].get(mode, 0)) + 1
            self._write(data)

    def get_usage_summary(self, today: str, days: int = 7) -> Dict[str, object]:
        usage = self._read().get("usage", {})
        ordered_days = sorted(usage.keys())[-days:]
        last_days = [
            {"day": day, "seconds": usage[day]["seconds"], "modes": usage[day]["modes"]}
            for day in ordered_days
        ]
        today_seconds = int(usage.get(today, {}).get("seconds", 0))
        mode_totals: Dict[str, int] = {}
        for item in last_days:
            for mode, count in item["modes"].items():
                mode_totals[mode] = mode_totals.get(mode, 0) + int(count)
        return {
            "todaySeconds": today_seconds,
            "last7Days": last_days,
            "modeTotals": mode_totals,
        }

    def _read(self) -> Dict[str, object]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: Dict[str, object]) -> None:
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class SQLiteStorage(BaseStorage):
    driver = "sqlite"

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self._initialize()

    def get_settings(self) -> Settings:
        with self._connect() as conn:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
        data = {row[0]: json.loads(row[1]) for row in rows}
        return Settings(**{**Settings().__dict__, **data})

    def save_settings(self, partial: Dict[str, object]) -> Settings:
        merged = {**self.get_settings().__dict__, **partial}
        with self.lock, self._connect() as conn:
            for key, value in merged.items():
                conn.execute(
                    "INSERT INTO settings(key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, json.dumps(value, ensure_ascii=False)),
                )
            conn.commit()
        return Settings(**merged)

    def list_memories(self, now_iso: Optional[str] = None) -> List[MemoryCard]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, category, key, value, scope, created_at, updated_at, expires_at FROM memories"
            ).fetchall()
        cards = [
            MemoryCard(
                id=row[0],
                category=row[1],
                key=row[2],
                value=row[3],
                scope=row[4],
                created_at=row[5],
                updated_at=row[6],
                expires_at=row[7],
            )
            for row in rows
        ]
        valid_cards = _purge_expired(cards, now_iso)
        if len(valid_cards) != len(cards):
            valid_ids = {card.id for card in valid_cards}
            with self.lock, self._connect() as conn:
                if valid_ids:
                    conn.execute(
                        f"DELETE FROM memories WHERE id NOT IN ({','.join('?' for _ in valid_ids)})",
                        tuple(valid_ids),
                    )
                else:
                    conn.execute("DELETE FROM memories")
                conn.commit()
        return valid_cards

    def upsert_memory(self, card: MemoryCard) -> MemoryCard:
        with self.lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT id, created_at FROM memories WHERE category = ? AND key = ?",
                (card.category, card.key),
            ).fetchone()
            if existing:
                card.id = existing[0]
                card.created_at = existing[1]
            conn.execute(
                "INSERT INTO memories(id, category, key, value, scope, created_at, updated_at, expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET "
                "category = excluded.category, key = excluded.key, value = excluded.value, scope = excluded.scope, "
                "created_at = excluded.created_at, updated_at = excluded.updated_at, expires_at = excluded.expires_at",
                (
                    card.id,
                    card.category,
                    card.key,
                    card.value,
                    card.scope,
                    card.created_at,
                    card.updated_at,
                    card.expires_at,
                ),
            )
            conn.commit()
        return card

    def delete_memory(self, card_id: str) -> None:
        with self.lock, self._connect() as conn:
            conn.execute("DELETE FROM memories WHERE id = ?", (card_id,))
            conn.commit()

    def record_usage(self, day: str, seconds: int, mode: str) -> None:
        with self.lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO usage_days(day, seconds) VALUES (?, ?) "
                "ON CONFLICT(day) DO UPDATE SET seconds = seconds + excluded.seconds",
                (day, max(seconds, 0)),
            )
            conn.execute(
                "INSERT INTO mode_usage(day, mode, count) VALUES (?, ?, 1) "
                "ON CONFLICT(day, mode) DO UPDATE SET count = count + 1",
                (day, mode),
            )
            conn.commit()

    def get_usage_summary(self, today: str, days: int = 7) -> Dict[str, object]:
        with self._connect() as conn:
            usage_rows = conn.execute(
                "SELECT day, seconds FROM usage_days ORDER BY day DESC LIMIT ?",
                (days,),
            ).fetchall()
            mode_rows = conn.execute(
                "SELECT mode, SUM(count) FROM mode_usage "
                "WHERE day IN (SELECT day FROM usage_days ORDER BY day DESC LIMIT ?) GROUP BY mode",
                (days,),
            ).fetchall()
            detail_rows = conn.execute(
                "SELECT day, mode, count FROM mode_usage "
                "WHERE day IN (SELECT day FROM usage_days ORDER BY day DESC LIMIT ?)",
                (days,),
            ).fetchall()
        by_day_modes: Dict[str, Dict[str, int]] = {}
        for day, mode, count in detail_rows:
            by_day_modes.setdefault(day, {})[mode] = int(count)
        last_days = [
            {"day": row[0], "seconds": int(row[1]), "modes": by_day_modes.get(row[0], {})}
            for row in reversed(usage_rows)
        ]
        today_seconds = next((int(row[1]) for row in usage_rows if row[0] == today), 0)
        return {
            "todaySeconds": today_seconds,
            "last7Days": last_days,
            "modeTotals": {row[0]: int(row[1]) for row in mode_rows},
        }

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS memories ("
                "id TEXT PRIMARY KEY, category TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, "
                "scope TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, expires_at TEXT)"
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_slot ON memories(category, key)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS usage_days (day TEXT PRIMARY KEY, seconds INTEGER NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS mode_usage ("
                "day TEXT NOT NULL, mode TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(day, mode))"
            )
            conn.commit()

    def _connect(self):
        return sqlite_module.connect(str(self.path))


def create_storage(base_dir: Path, force_json: bool = False) -> BaseStorage:
    if sqlite_module is not None and not force_json:
        try:
            return SQLiteStorage(base_dir / "toy_brain.sqlite3")
        except Exception:
            pass
    return JsonStorage(base_dir / "toy_brain_state.json")


def _purge_expired(cards: List[MemoryCard], now_iso: Optional[str]) -> List[MemoryCard]:
    if not now_iso:
        return cards
    now = datetime.fromisoformat(now_iso)
    valid_cards = []
    for card in cards:
        if card.expires_at and datetime.fromisoformat(card.expires_at) < now:
            continue
        valid_cards.append(card)
    return valid_cards
