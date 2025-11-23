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


def test_rewrite_prompt_logic_with_feedback(mock_vault, mock_model):
    date = datetime.date(2023, 10, 27)
    level = Level.daily
    context_levels = [Level.daily]
    current_prompt = "Original prompt"
    external_feedback = ["Make it shorter", "More emoji"]

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
                        external_feedback=external_feedback,
                    )

                    assert result == "Rewritten prompt"
                    
                    # Verify that the feedback was passed to the agent
                    # The agent is called twice: once for generation, once for critique
                    # We want to check the call arguments for the critique step (the second call)
                    assert mock_agent_instance.run.call_count == 2
                    
                    # Get the arguments of the second call
                    call_args = mock_agent_instance.run.call_args_list[1]
                    user_prompt = call_args.kwargs['user_prompt']
                    
                    # Check if feedback is present in the user_prompt
                    # user_prompt is a list of strings
                    feedback_str = ""
                    for item in user_prompt:
                        if "Human Feedback:" in item:
                            feedback_str = item
                            break
                    
                    assert "Make it shorter" in feedback_str
                    assert "More emoji" in feedback_str
