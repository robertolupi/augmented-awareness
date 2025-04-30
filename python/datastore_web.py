import streamlit as st

from sqlmodel import create_engine, Session, select

from aww.datastore import Event
from aww import context


@st.cache_resource
def get_session():
    context.initialize()
    engine = create_engine(context.settings.sqlite_url)
    return Session(engine)


start_date = st.date_input("Start")
end_date = st.date_input("End")

with get_session() as session:
    events = session.exec(
        select(Event).where(start_date <= Event.date, Event.date <= end_date)
    ).all()

for e in events:
    st.text(e)
