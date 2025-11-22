import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_ai.models import Model

from aww.obsidian import Level, Vault
from aww.prompt_engineering import rewrite_prompt_logic


@pytest.fixture
def mock_vault():
    vault = MagicMock(spec=Vault)
    return vault


@pytest.fixture
def mock_model():
    model = MagicMock(spec=Model)
    model.model_name = "test-model"
    return model


def test_rewrite_prompt_logic(mock_vault, mock_model):
    date = datetime.date(2023, 10, 27)
    level = Level.daily
    context_levels = [Level.daily]
    current_prompt = "Original prompt"

    # Mock Selection and Node
    with patch("aww.prompt_engineering.retro.Selection") as MockSelection:
        mock_sel = MockSelection.return_value
        mock_node = MagicMock()
        mock_sel.root = mock_node
        mock_node.sources = []
        mock_node.level = Level.daily
        mock_node.retro_page.content.return_value = "Some content"
        mock_node.retro_page.feedback.return_value = []
        mock_node.retro_page.feedback_score.return_value = None

        # Mock Agent
        with patch("aww.prompt_engineering.Agent") as MockAgent:
            mock_agent_instance = MockAgent.return_value
            
            # Mock run method (async)
            mock_result = MagicMock()
            mock_result.output = "Rewritten prompt"
            mock_agent_instance.run = AsyncMock(return_value=mock_result)

            # Mock create_model
            with patch("aww.prompt_engineering.create_model", return_value=mock_model):
                # Mock page_content
                with patch("aww.retro_gen.page_content", new_callable=AsyncMock) as mock_page_content:
                    mock_page_content.return_value = "Page content"

                    result = rewrite_prompt_logic(
                        critique_model_name="local",
                        llm_model=mock_model,
                        vault=mock_vault,
                        date=date,
                        level=level,
                        context_levels=context_levels,
                        current_prompt=current_prompt,
                    )

                    assert result == "Rewritten prompt"
                    assert mock_agent_instance.run.call_count == 2  # Once for gen, once for critique
