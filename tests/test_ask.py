import datetime
from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai.models import Model

from aww.ask import ask_question
from aww.obsidian import Level, Vault


@pytest.fixture
def mock_vault():
    vault = MagicMock(spec=Vault)
    return vault


@pytest.fixture
def mock_model():
    model = MagicMock(spec=Model)
    return model


def test_ask_question(mock_vault, mock_model):
    date = datetime.date(2023, 10, 27)
    level = Level.daily
    prompt = "What happened?"
    context_levels = [Level.daily]

    # Mock Selection and Node
    with patch("aww.ask.retro.Selection") as MockSelection:
        mock_sel = MockSelection.return_value
        mock_node = MagicMock()
        mock_sel.root = mock_node
        mock_node.sources = []
        mock_node.level = Level.daily
        mock_node.retro_page.content.return_value = "Some content"
        mock_node.retro_page.name = "2023-10-27"

        # Mock Agent
        with patch("aww.ask.Agent") as MockAgent:
            mock_agent = MockAgent.return_value
            mock_result = MagicMock()
            mock_result.output = "Nothing happened."
            mock_agent.run_sync.return_value = mock_result

            result = ask_question(
                vault=mock_vault,
                llm_model=mock_model,
                date=date,
                level=level,
                prompt=prompt,
                context_levels=context_levels,
            )

            assert result == "Nothing happened."
            MockAgent.assert_called_once()
            mock_agent.run_sync.assert_called_once()
