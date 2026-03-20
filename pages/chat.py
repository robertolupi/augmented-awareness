import os

import streamlit as st
from pydantic_ai import Agent
from pydantic_ai.messages import (
    TextPart,
    UserPromptPart,
)

from aww import obsidian
from aww.chat import get_chat_agent
from aww.config import Settings, create_model
from aww.deps import ChatDeps
from aww.rag import Index
from aww.session_manager import ChatSessionSummary, SessionManager

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def render_messages(messages, show_tool_calls):
    for message in messages:
        for part in message.parts:
            match part:
                case UserPromptPart(content):
                    with st.chat_message("user"):
                        st.write(content)
                case TextPart(content):
                    with st.chat_message("ai"):
                        st.write(content)
                case _:
                    if show_tool_calls:
                        with st.chat_message("assistant"):
                            st.write(part)


def format_session_label(session: ChatSessionSummary) -> str:
    external = (
        f" | ext:{session.external_session_id}" if session.external_session_id else ""
    )
    return f"{session.title} [{session.channel}]{external}"


def load_session_into_state(manager: SessionManager, session_id: str) -> None:
    session = manager.load_session(session_id)
    st.session_state["active_chat_session_id"] = session.id
    st.session_state["chat_title"] = session.title
    st.session_state["chat_history"] = session.messages


def ensure_active_session(manager: SessionManager, model_name: str) -> None:
    active_session_id = st.session_state.get("active_chat_session_id")
    if (
        active_session_id
        and "chat_history" in st.session_state
        and "chat_title" in st.session_state
    ):
        return
    if active_session_id:
        try:
            load_session_into_state(manager, active_session_id)
            return
        except ValueError:
            pass

    session = manager.get_latest_session()
    if session is None:
        session = manager.create_session(model=model_name, channel="streamlit")
    st.session_state["active_chat_session_id"] = session.id
    st.session_state["chat_title"] = session.title
    st.session_state["chat_history"] = session.messages


def save_active_session(manager: SessionManager, model_name: str) -> None:
    session = manager.load_session(st.session_state["active_chat_session_id"])
    session.title = st.session_state.get("chat_title", session.title)
    session.model = model_name
    session.messages = st.session_state.get("chat_history", [])
    manager.save_session(session)


settings = Settings()
vault = obsidian.Vault.from_settings(settings)
index = Index.from_settings(settings)
deps = ChatDeps(vault=vault, index=index)
session_manager = SessionManager(settings)

model = None
agent = None
ensure_active_session(session_manager, settings.model)

with st.sidebar:
    model_name = st.selectbox(
        "Model",
        settings.models.keys(),
        index=list(settings.models.keys()).index(settings.model),
    )
    if model_name in settings.models.keys():
        model = create_model(model_name)
        agent = get_chat_agent(model, vault)

    show_tool_calls = st.checkbox("Show tool calls", value=False)

    st.divider()
    st.subheader("Sessions")
    all_sessions = session_manager.list_sessions()
    channels = ["All"] + sorted({session.channel for session in all_sessions})
    selected_channel = st.selectbox(
        "Channel Filter",
        channels,
        key="chat_channel_filter",
    )
    filtered_sessions = (
        all_sessions
        if selected_channel == "All"
        else [item for item in all_sessions if item.channel == selected_channel]
    )
    active_session_id = st.session_state["active_chat_session_id"]
    if filtered_sessions:
        if active_session_id not in {item.id for item in filtered_sessions}:
            st.session_state["active_chat_session_id"] = filtered_sessions[0].id
            load_session_into_state(session_manager, filtered_sessions[0].id)
            active_session_id = filtered_sessions[0].id
        selected_session_id = st.selectbox(
            "Session",
            [item.id for item in filtered_sessions],
            format_func=lambda session_id: format_session_label(
                next(item for item in filtered_sessions if item.id == session_id)
            ),
            index=[item.id for item in filtered_sessions].index(active_session_id),
        )
        if selected_session_id != active_session_id:
            load_session_into_state(session_manager, selected_session_id)
            st.rerun()
    else:
        selected_session_id = None

    col_new, col_delete = st.columns(2)
    if col_new.button("New Session"):
        new_session = session_manager.create_session(model=model_name, channel="streamlit")
        load_session_into_state(session_manager, new_session.id)
        st.rerun()
    if col_delete.button("Delete Session", disabled=selected_session_id is None):
        session_manager.delete_session(st.session_state["active_chat_session_id"])
        st.session_state.pop("active_chat_session_id", None)
        st.session_state.pop("chat_history", None)
        st.session_state.pop("chat_title", None)
        ensure_active_session(session_manager, model_name)
        st.rerun()

    st.subheader("Rename Session")
    chat_title = st.text_input("Session Title", key="chat_title")
    current_session = session_manager.load_session(st.session_state["active_chat_session_id"])
    if chat_title != current_session.title:
        session_manager.rename_session(current_session.id, chat_title)

    st.subheader("Save to Obsidian")
    if st.button("Save to Obsidian", disabled=not st.session_state.get("chat_history")):
        history = st.session_state.get("chat_history", [])
        if history:
            from datetime import date
            today = date.today().isoformat()
            filename = f"{today} {chat_title}.md"
            chats_dir = vault.path / "Chats"
            chats_dir.mkdir(parents=True, exist_ok=True)
            filepath = chats_dir / filename

            # Format history as markdown
            md_lines = [f"# {chat_title}\n"]
            for msg in history:
                for part in msg.parts:
                    match part:
                        case UserPromptPart(content):
                            md_lines.append(f"### User\n{content}\n")
                        case TextPart(content):
                            md_lines.append(f"### AI\n{content}\n")
            
            try:
                filepath.write_text("\n".join(md_lines))
                st.success(f"Saved to {filepath}")
            except Exception as e:
                st.error(f"Failed to save: {e}")


st.title("Chat")

chat_history = st.session_state.get("chat_history")

if chat_history:
    render_messages(chat_history, show_tool_calls)

if agent:
    prompt = st.chat_input("Chat")

    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner("Waiting for response..."):
            response = agent.run_sync(prompt, message_history=chat_history, deps=deps)
            render_messages((response.new_messages()), show_tool_calls)

            st.session_state["chat_history"] = response.all_messages()
            save_active_session(session_manager, model_name)
