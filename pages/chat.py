import datetime

import streamlit as st
from pydantic_ai import Agent
from pydantic_ai.messages import (
    UserPromptPart,
    TextPart,
)

from aww.config import Settings, create_model
from aww.chat import get_chat_agent


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
model = None
agent = None

with st.sidebar:
    model_name = st.selectbox("Model", settings.models.keys())
    if model_name in settings.models.keys():
        model = create_model(model_name)
        agent = get_chat_agent(model)

    show_tool_calls = st.checkbox("Show tool calls", value=False)


st.header("Chat")

chat_history = st.session_state.get("chat_history")

if chat_history:
    render_messages(chat_history, show_tool_calls)

if agent:
    prompt = st.chat_input("Chat")

    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner("Waiting for response..."):
            response = agent.run_sync(prompt, message_history=chat_history)
            render_messages((response.new_messages()), show_tool_calls)

            st.session_state["chat_history"] = response.all_messages()
