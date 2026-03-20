from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

from aww.database import get_db_path, init_db


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_title() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


@dataclass(slots=True)
class ChatSession:
    id: str
    channel: str
    title: str
    model: str | None
    messages: list[ModelMessage]
    created_at: str
    updated_at: str
    external_session_id: str | None = None


@dataclass(slots=True)
class ChatSessionSummary:
    id: str
    channel: str
    title: str
    model: str | None
    created_at: str
    updated_at: str
    external_session_id: str | None = None


class SessionManager:
    def __init__(self, settings):
        self.db_path = get_db_path(settings)
        init_db(self.db_path)

    def list_sessions(self, channel: str | None = None) -> list[ChatSessionSummary]:
        query = """
            SELECT id, channel, external_session_id, title, model, created_at, updated_at
            FROM chat_sessions
        """
        params: tuple[str, ...] = ()
        if channel is not None:
            query += " WHERE channel = ?"
            params = (channel,)
        query += " ORDER BY updated_at DESC, created_at DESC, id ASC"
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            ChatSessionSummary(
                id=row[0],
                channel=row[1],
                external_session_id=row[2],
                title=row[3],
                model=row[4],
                created_at=row[5],
                updated_at=row[6],
            )
            for row in rows
        ]

    def get_latest_session(self, channel: str | None = None) -> ChatSession | None:
        query = """
            SELECT id, channel, external_session_id, title, model, messages_json, created_at, updated_at
            FROM chat_sessions
        """
        params: tuple[str, ...] = ()
        if channel is not None:
            query += " WHERE channel = ?"
            params = (channel,)
        query += " ORDER BY updated_at DESC, created_at DESC, id ASC LIMIT 1"
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(query, params).fetchone()
        return self._row_to_session(row) if row else None

    def create_session(
        self,
        title: str | None = None,
        model: str | None = None,
        channel: str = "streamlit",
        session_id: str | None = None,
        external_session_id: str | None = None,
    ) -> ChatSession:
        session_id = self._normalize_id(session_id) if session_id is not None else str(uuid.uuid4())
        if not channel.strip():
            raise ValueError("channel must not be empty")
        if external_session_id is not None:
            external_session_id = self._normalize_id(external_session_id)
        timestamp = _utc_now()
        session = ChatSession(
            id=session_id,
            channel=channel,
            external_session_id=external_session_id,
            title=title or _default_title(),
            model=model,
            messages=[],
            created_at=timestamp,
            updated_at=timestamp,
        )
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO chat_sessions (
                        id, channel, external_session_id, title, model, messages_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session.id,
                        session.channel,
                        session.external_session_id,
                        session.title,
                        session.model,
                        self._dump_messages(session.messages),
                        session.created_at,
                        session.updated_at,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError(self._integrity_message(session.id, channel, external_session_id)) from exc
        return session

    def load_session(self, session_id: str) -> ChatSession:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT id, channel, external_session_id, title, model, messages_json, created_at, updated_at
                FROM chat_sessions
                WHERE id = ?
                """,
                (self._normalize_id(session_id),),
            ).fetchone()
        if row is None:
            raise ValueError(f"Session '{session_id}' not found")
        return self._row_to_session(row)

    def load_session_by_external_id(
        self, channel: str, external_session_id: str
    ) -> ChatSession | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT id, channel, external_session_id, title, model, messages_json, created_at, updated_at
                FROM chat_sessions
                WHERE channel = ? AND external_session_id = ?
                """,
                (channel, self._normalize_id(external_session_id)),
            ).fetchone()
        return self._row_to_session(row) if row else None

    def save_session(self, session: ChatSession) -> None:
        session_id = self._normalize_id(session.id)
        external_session_id = (
            self._normalize_id(session.external_session_id)
            if session.external_session_id is not None
            else None
        )
        updated_at = _utc_now()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    UPDATE chat_sessions
                    SET channel = ?, external_session_id = ?, title = ?, model = ?, messages_json = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        session.channel,
                        external_session_id,
                        session.title,
                        session.model,
                        self._dump_messages(session.messages),
                        updated_at,
                        session_id,
                    ),
                )
                if cursor.rowcount == 0:
                    raise ValueError(f"Session '{session.id}' not found")
        except sqlite3.IntegrityError as exc:
            raise ValueError(self._integrity_message(session_id, session.channel, external_session_id)) from exc
        session.id = session_id
        session.external_session_id = external_session_id
        session.updated_at = updated_at

    def rename_session(self, session_id: str, title: str) -> ChatSession:
        session = self.load_session(session_id)
        session.title = title
        self.save_session(session)
        return session

    def delete_session(self, session_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM chat_sessions WHERE id = ?",
                (self._normalize_id(session_id),),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Session '{session_id}' not found")

    def _row_to_session(self, row: tuple) -> ChatSession:
        return ChatSession(
            id=row[0],
            channel=row[1],
            external_session_id=row[2],
            title=row[3],
            model=row[4],
            messages=self._load_messages(row[5]),
            created_at=row[6],
            updated_at=row[7],
        )

    def _dump_messages(self, messages: list[ModelMessage]) -> str:
        return ModelMessagesTypeAdapter.dump_json(messages).decode("utf-8")

    def _load_messages(self, messages_json: str) -> list[ModelMessage]:
        return list(ModelMessagesTypeAdapter.validate_json(messages_json))

    def _normalize_id(self, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("session IDs must not be empty")
        return normalized

    def _integrity_message(
        self, session_id: str, channel: str, external_session_id: str | None
    ) -> str:
        if self._session_id_exists(session_id):
            return f"Session '{session_id}' already exists"
        if external_session_id is not None and self.load_session_by_external_id(channel, external_session_id):
            return (
                f"Session for channel '{channel}' with external ID "
                f"'{external_session_id}' already exists"
            )
        return "Session could not be persisted because of a uniqueness constraint"

    def _session_id_exists(self, session_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT 1 FROM chat_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        return row is not None
