import pathlib

from aww import settings

settings.CONFIG_FILE = pathlib.Path(__file__).parent / "config.toml"


def test_settings():
    st = settings.Settings()
    assert st.obsidian.vault == pathlib.Path("vault")
    assert st.obsidian.tips.model_name == "local"
    assert "5 helpful, short and actionable tips" in st.obsidian.tips.system_prompt
    assert st.obsidian.tips.user_prompt == "What can I do differently?"
    assert st.llm.provider["local"].base_url == "http://localhost:1234/v1/"
    assert st.llm.model["local"].provider == "local"
    assert st.llm.model["local"].model == "gemma-3-4b-it"
