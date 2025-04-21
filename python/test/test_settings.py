import pathlib

from aww import settings

settings.CONFIG_FILE = pathlib.Path(__file__).parent / "config.toml"


def test_settings():
    st = settings.Settings()
    assert st.obsidian.vault == pathlib.Path("../../test_vault")
    assert st.llm.provider["local"].base_url == "http://localhost:1234/v1/"
    assert st.llm.model["local"].provider == "local"
    assert st.llm.model["local"].model == "gemma-3-4b-it"
