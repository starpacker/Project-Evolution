"""
Evolution SQLite 数据库管理器
管理日程、技能树、人物档案、训练记录、心智模型、每日反思等结构化数据。

v0.2.1: 增强连接管理（健康检查、自动重连）、输入验证。
"""

import atexit
import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("evolution.db")


class DatabaseManager:
    """线程安全的 SQLite 数据库管理器"""

    _instance = None
    _lock = threading.Lock()

    # Allowed column names for upsert_person kwargs (防止 SQL 注入)
    _PERSON_COLUMNS = frozenset({
        "relationship", "likes", "dislikes", "important_dates",
        "interaction_frequency", "emotional_impact", "notes",
    })

    def __new__(cls, db_path: Optional[str] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if self._initialized:
            return
        from evolution.config.settings import DB_PATH

        self.db_path = str(db_path or DB_PATH)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_tables()
        self._initialized = True
        atexit.register(self.close)

    @contextmanager
    def _get_conn(self):
        """每线程一个连接，带健康检查和自动重连"""
        conn = getattr(self._local, "conn", None)

        # Health check: verify existing connection is still usable
        if conn is not None:
            try:
                conn.execute("SELECT 1")
            except (sqlite3.OperationalError, sqlite3.ProgrammingError):
                logger.warning("[DB] Stale connection detected, reconnecting")
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
                self._local.conn = None

        if conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path, timeout=30.0,
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn.execute("PRAGMA busy_timeout=5000")

        try:
            yield self._local.conn
            self._local.conn.commit()
        except sqlite3.OperationalError as e:
            logger.error(f"[DB] Operational error: {e}")
            self._local.conn.rollback()
            raise
        except Exception:
            self._local.conn.rollback()
            raise

    def _init_tables(self):
        """初始化所有表"""
        with self._get_conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    due_date TEXT,
                    remind_at TEXT,
                    priority TEXT DEFAULT 'medium' CHECK(priority IN ('high','medium','low')),
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','done','overdue','cancelled')),
                    category TEXT CHECK(category IN ('professional','physical','personal','relationship')),
                    context TEXT,
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    updated_at TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL CHECK(category IN ('professional','thinking','language','physical','emotional')),
                    level INTEGER DEFAULT 1 CHECK(level BETWEEN 1 AND 10),
                    xp INTEGER DEFAULT 0,
                    last_trained TEXT,
                    weakness TEXT,
                    target_level INTEGER DEFAULT 5,
                    preferred_modality TEXT,
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    relationship TEXT,
                    likes TEXT,
                    dislikes TEXT,
                    important_dates TEXT,
                    last_mentioned TEXT,
                    mention_count INTEGER DEFAULT 0,
                    interaction_frequency TEXT DEFAULT 'low',
                    emotional_impact TEXT DEFAULT 'neutral',
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    updated_at TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS training_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_id INTEGER,
                    modality TEXT CHECK(modality IN ('T1','T2','T3','T4','T5','T6','T7')),
                    topic TEXT,
                    rating TEXT,
                    insight TEXT,
                    trained_at TEXT DEFAULT (datetime('now','localtime')),
                    FOREIGN KEY (skill_id) REFERENCES skills(id)
                );

                CREATE TABLE IF NOT EXISTS mental_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    source_domain TEXT,
                    description TEXT,
                    applications TEXT,
                    learned_date TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS daily_reflections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    report_json TEXT NOT NULL,
                    primary_emotion TEXT,
                    emotional_intensity REAL,
                    tomorrow_suggestion TEXT,
                    evening_message TEXT,
                    created_at TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
                    content TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_schedule_status ON schedule(status);
                CREATE INDEX IF NOT EXISTS idx_schedule_due ON schedule(due_date);
                CREATE INDEX IF NOT EXISTS idx_conv_date ON conversation_logs(date);
                CREATE INDEX IF NOT EXISTS idx_persons_name ON persons(name);
                CREATE INDEX IF NOT EXISTS idx_reflections_date ON daily_reflections(date);
            """
            )

    # ──────────────────────────────────────────
    # 日程 CRUD
    # ──────────────────────────────────────────
    def add_schedule(
        self,
        content: str,
        due_date: Optional[str] = None,
        remind_at: Optional[str] = None,
        priority: str = "medium",
        category: Optional[str] = None,
        context: Optional[str] = None,
    ) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO schedule (content, due_date, remind_at, priority, category, context) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (content, due_date, remind_at, priority, category, context),
            )
            return cur.lastrowid

    def get_schedule_by_date(self, date: str) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM schedule WHERE date(due_date) = ? AND status = 'pending' ORDER BY priority DESC, due_date ASC",
                (date,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_pending_schedules(self) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM schedule WHERE status = 'pending' ORDER BY due_date ASC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_overdue_schedules(self) -> List[Dict]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM schedule WHERE status = 'pending' AND due_date < ? ORDER BY due_date ASC",
                (now,),
            ).fetchall()
            return [dict(r) for r in rows]

    def complete_schedule(self, schedule_id: int) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE schedule SET status = 'done', updated_at = datetime('now','localtime') WHERE id = ?",
                (schedule_id,),
            )
            return cur.rowcount > 0

    def cancel_schedule(self, schedule_id: int) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE schedule SET status = 'cancelled', updated_at = datetime('now','localtime') WHERE id = ?",
                (schedule_id,),
            )
            return cur.rowcount > 0

    def delete_schedule(self, schedule_id: int) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute("DELETE FROM schedule WHERE id = ?", (schedule_id,))
            return cur.rowcount > 0

    # ──────────────────────────────────────────
    # 技能树 CRUD
    # ──────────────────────────────────────────
    def add_skill(
        self,
        name: str,
        category: str,
        level: int = 1,
        target_level: int = 5,
        weakness: Optional[str] = None,
    ) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO skills (name, category, level, target_level, weakness) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, category, level, target_level, weakness),
            )
            return cur.lastrowid

    def get_skill(self, name: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM skills WHERE name = ?", (name,)
            ).fetchone()
            return dict(row) if row else None

    def list_skills(self, category: Optional[str] = None) -> List[Dict]:
        with self._get_conn() as conn:
            if category:
                rows = conn.execute(
                    "SELECT * FROM skills WHERE category = ? ORDER BY level DESC",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM skills ORDER BY category, level DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def update_skill_level(self, name: str, new_level: int, xp_delta: int = 0) -> bool:
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE skills SET level = ?, xp = xp + ?, last_trained = datetime('now','localtime') WHERE name = ?",
                (new_level, xp_delta, name),
            )
            return cur.rowcount > 0

    def get_stale_skills(self, days: int = 14) -> List[Dict]:
        """获取超过 N 天未训练的技能"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM skills WHERE last_trained IS NULL OR "
                "julianday('now','localtime') - julianday(last_trained) > ?",
                (days,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ──────────────────────────────────────────
    # 人物档案 CRUD
    # ──────────────────────────────────────────
    def upsert_person(self, name: str, **kwargs) -> int:
        with self._get_conn() as conn:
            existing = conn.execute(
                "SELECT id FROM persons WHERE name = ?", (name,)
            ).fetchone()
            if existing:
                set_clauses = []
                values = []
                for k, v in kwargs.items():
                    if v is not None and k in self._PERSON_COLUMNS:
                        set_clauses.append(f"{k} = ?")
                        values.append(v)
                set_clauses.append("mention_count = mention_count + 1")
                set_clauses.append("last_mentioned = datetime('now','localtime')")
                set_clauses.append("updated_at = datetime('now','localtime')")
                values.append(existing["id"])
                conn.execute(
                    f"UPDATE persons SET {', '.join(set_clauses)} WHERE id = ?",
                    values,
                )
                return existing["id"]
            else:
                cur = conn.execute(
                    "INSERT INTO persons (name, relationship, last_mentioned, mention_count) "
                    "VALUES (?, ?, datetime('now','localtime'), 1)",
                    (name, kwargs.get("relationship", "unknown")),
                )
                return cur.lastrowid

    def get_person(self, name: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM persons WHERE name = ?", (name,)
            ).fetchone()
            return dict(row) if row else None

    def list_persons(self) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM persons ORDER BY mention_count DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_top_mentioned_persons(self, limit: int = 5) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM persons ORDER BY mention_count DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ──────────────────────────────────────────
    # 训练记录
    # ──────────────────────────────────────────
    def add_training_log(
        self,
        skill_name: str,
        modality: str,
        topic: str,
        rating: str,
        insight: Optional[str] = None,
    ) -> int:
        with self._get_conn() as conn:
            skill = conn.execute(
                "SELECT id FROM skills WHERE name = ?", (skill_name,)
            ).fetchone()
            skill_id = skill["id"] if skill else None
            cur = conn.execute(
                "INSERT INTO training_logs (skill_id, modality, topic, rating, insight) "
                "VALUES (?, ?, ?, ?, ?)",
                (skill_id, modality, topic, rating, insight),
            )
            return cur.lastrowid

    def get_training_logs(
        self, skill_name: Optional[str] = None, limit: int = 20
    ) -> List[Dict]:
        with self._get_conn() as conn:
            if skill_name:
                rows = conn.execute(
                    "SELECT tl.*, s.name as skill_name FROM training_logs tl "
                    "LEFT JOIN skills s ON tl.skill_id = s.id "
                    "WHERE s.name = ? ORDER BY tl.trained_at DESC LIMIT ?",
                    (skill_name, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT tl.*, s.name as skill_name FROM training_logs tl "
                    "LEFT JOIN skills s ON tl.skill_id = s.id "
                    "ORDER BY tl.trained_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    # ──────────────────────────────────────────
    # 心智模型
    # ──────────────────────────────────────────
    def add_mental_model(
        self,
        name: str,
        source_domain: str,
        description: str,
        applications: Optional[List[str]] = None,
    ) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO mental_models (name, source_domain, description, applications) "
                "VALUES (?, ?, ?, ?)",
                (name, source_domain, description, json.dumps(applications or [], ensure_ascii=False)),
            )
            return cur.lastrowid

    def list_mental_models(self) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM mental_models ORDER BY learned_date DESC"
            ).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                try:
                    d["applications"] = json.loads(d.get("applications", "[]"))
                except (json.JSONDecodeError, TypeError):
                    d["applications"] = []
                result.append(d)
            return result

    # ──────────────────────────────────────────
    # 每日反思
    # ──────────────────────────────────────────
    def save_reflection(
        self, date: str, report_json: str, primary_emotion: str,
        emotional_intensity: float, tomorrow_suggestion: str,
        evening_message: str,
    ) -> int:
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT OR REPLACE INTO daily_reflections "
                "(date, report_json, primary_emotion, emotional_intensity, "
                "tomorrow_suggestion, evening_message) VALUES (?, ?, ?, ?, ?, ?)",
                (date, report_json, primary_emotion, emotional_intensity,
                 tomorrow_suggestion, evening_message),
            )
            return cur.lastrowid

    def get_reflection(self, date: str) -> Optional[Dict]:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM daily_reflections WHERE date = ?", (date,)
            ).fetchone()
            return dict(row) if row else None

    def get_reflections_range(self, start_date: str, end_date: str) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM daily_reflections WHERE date BETWEEN ? AND ? ORDER BY date ASC",
                (start_date, end_date),
            ).fetchall()
            return [dict(r) for r in rows]

    # ──────────────────────────────────────────
    # 对话日志
    # ──────────────────────────────────────────
    def log_conversation(self, role: str, content: str) -> int:
        now = datetime.now()
        with self._get_conn() as conn:
            cur = conn.execute(
                "INSERT INTO conversation_logs (date, timestamp, role, content) VALUES (?, ?, ?, ?)",
                (now.strftime("%Y-%m-%d"), now.isoformat(), role, content),
            )
            return cur.lastrowid

    def get_conversations_by_date(self, date: str) -> List[Dict]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM conversation_logs WHERE date = ? ORDER BY timestamp ASC",
                (date,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_conversation_count_by_date(self, date: str) -> int:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM conversation_logs WHERE date = ?",
                (date,),
            ).fetchone()
            return row["cnt"] if row else 0

    # ──────────────────────────────────────────
    # 统计
    # ──────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        with self._get_conn() as conn:
            stats = {}
            stats["total_schedules"] = conn.execute(
                "SELECT COUNT(*) FROM schedule"
            ).fetchone()[0]
            stats["pending_schedules"] = conn.execute(
                "SELECT COUNT(*) FROM schedule WHERE status='pending'"
            ).fetchone()[0]
            stats["total_skills"] = conn.execute(
                "SELECT COUNT(*) FROM skills"
            ).fetchone()[0]
            stats["total_persons"] = conn.execute(
                "SELECT COUNT(*) FROM persons"
            ).fetchone()[0]
            stats["total_trainings"] = conn.execute(
                "SELECT COUNT(*) FROM training_logs"
            ).fetchone()[0]
            stats["total_reflections"] = conn.execute(
                "SELECT COUNT(*) FROM daily_reflections"
            ).fetchone()[0]
            stats["total_conversations"] = conn.execute(
                "SELECT COUNT(*) FROM conversation_logs"
            ).fetchone()[0]
            stats["total_mental_models"] = conn.execute(
                "SELECT COUNT(*) FROM mental_models"
            ).fetchone()[0]
            return stats

    def close(self):
        """Close the thread-local database connection (if any)."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            self._local.conn = None

    def reset_singleton(self):
        """仅用于测试：重置单例"""
        with DatabaseManager._lock:
            self.close()
            DatabaseManager._instance = None
            self._initialized = False
