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


settings = Settings()
vault = obsidian.Vault.from_settings(settings)
index = Index.from_settings(settings)
deps = ChatDeps(vault=vault, index=index)

model = None
agent = None

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
    st.subheader("Save to Obsidian")
    chat_title = st.text_input("Chat Title", value="New Chat")

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
