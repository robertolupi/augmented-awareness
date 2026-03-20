from __future__ import annotations

import time
import uuid
from pathlib import Path

import pytest
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from aww.config import Settings
from aww.database import get_db_path
from aww.session_manager import SessionManager


@pytest.fixture
def session_manager(tmp_path: Path) -> SessionManager:
    settings = Settings(
        data_path=str(tmp_path / "data"),
        vault_path=str(Path.cwd() / "test_vault"),
    )
    return SessionManager(settings)


def test_session_manager_initializes_schema(session_manager: SessionManager):
    db_path = session_manager.db_path
    assert db_path == get_db_path(Settings(data_path=str(db_path.parent), vault_path=str(Path.cwd() / "test_vault")))
    assert db_path.exists()
    sessions = session_manager.list_sessions()
    assert sessions == []


def test_create_session_generates_uuid_and_persists(session_manager: SessionManager):
    session = session_manager.create_session(model="local", channel="streamlit")
    uuid.UUID(session.id)
    loaded = session_manager.load_session(session.id)
    assert loaded.title == session.title
    assert len(loaded.title) == 16
    assert loaded.channel == "streamlit"
    assert loaded.model == "local"
    assert loaded.messages == []


def test_create_session_uses_provided_ids(session_manager: SessionManager):
    session = session_manager.create_session(
        title="Telegram",
        model="gpt",
        channel="telegram",
        session_id="session-1",
        external_session_id="chat-42",
    )
    assert session.id == "session-1"
    assert session.external_session_id == "chat-42"
    loaded = session_manager.load_session_by_external_id("telegram", "chat-42")
    assert loaded is not None
    assert loaded.id == "session-1"


def test_duplicate_ids_are_rejected(session_manager: SessionManager):
    session_manager.create_session(channel="telegram", session_id="duplicate")
    with pytest.raises(ValueError, match="already exists"):
        session_manager.create_session(channel="streamlit", session_id="duplicate")


def test_duplicate_external_ids_are_rejected_per_channel(session_manager: SessionManager):
    session_manager.create_session(channel="telegram", external_session_id="123")
    with pytest.raises(ValueError, match="external ID"):
        session_manager.create_session(channel="telegram", external_session_id="123")
    other_channel = session_manager.create_session(channel="discord", external_session_id="123")
    assert other_channel.channel == "discord"


def test_save_session_round_trips_message_history(session_manager: SessionManager):
    session = session_manager.create_session(title="Thread")
    session.messages = [
        ModelRequest(parts=[UserPromptPart(content="Hello")]),
        ModelResponse(parts=[TextPart(content="Hi there")]),
    ]
    session_manager.save_session(session)
    loaded = session_manager.load_session(session.id)
    assert len(loaded.messages) == 2
    assert loaded.messages[0].parts[0].content == "Hello"
    assert loaded.messages[1].parts[0].content == "Hi there"


def test_latest_and_channel_filtered_listing(session_manager: SessionManager):
    first = session_manager.create_session(title="First", channel="telegram")
    time.sleep(0.01)
    second = session_manager.create_session(title="Second", channel="streamlit")
    latest = session_manager.get_latest_session()
    assert latest is not None
    assert latest.id == second.id
    telegram_sessions = session_manager.list_sessions(channel="telegram")
    assert [item.id for item in telegram_sessions] == [first.id]
    all_sessions = session_manager.list_sessions()
    assert [item.id for item in all_sessions] == [second.id, first.id]


def test_rename_and_delete_session(session_manager: SessionManager):
    session = session_manager.create_session(title="Old")
    renamed = session_manager.rename_session(session.id, "New")
    assert renamed.title == "New"
    assert session_manager.load_session(session.id).title == "New"
    session_manager.delete_session(session.id)
    assert session_manager.list_sessions() == []
    with pytest.raises(ValueError, match="not found"):
        session_manager.load_session(session.id)
