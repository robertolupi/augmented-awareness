import datetime

import streamlit as st
from pydantic_ai import Agent
from pydantic_ai.messages import (
    UserPromptPart,
    TextPart,
)

from aww.config import Settings, create_model

settings = Settings()
model = None
agent = None

with st.sidebar:
    model_name = st.selectbox("Model", settings.models.keys())
    if model_name in settings.models.keys():
        model = create_model(model_name)
        agent = Agent(model)

        @agent.tool_plain
        def current_date_time() -> datetime.datetime:
            """Get the current date and time, in the local timezone."""
            return datetime.datetime.now()


st.header("Chat")

chat_history = st.session_state.get("chat_history")

if chat_history:
    for message in chat_history:
        for part in message.parts:
            match part:
                case UserPromptPart(content):
                    with st.chat_message("user"):
                        st.write(content)
                case TextPart(content):
                    with st.chat_message("ai"):
                        st.write(content)
                case _:
                    with st.chat_message("assistant"):
                        st.write(part)


if agent:
    prompt = st.chat_input("Chat")

    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner("Waiting for response..."):
            response = agent.run_sync(prompt, message_history=chat_history)
            with st.chat_message("ai"):
                st.write(response.output)

            st.session_state["chat_history"] = response.all_messages()
