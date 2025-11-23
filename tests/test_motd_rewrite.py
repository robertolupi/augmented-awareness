import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner
from pydantic_ai.models import Model

from aww.cli import main
import aww.cli.rewrite_prompt  # Register command
from aww.obsidian import Vault
from aww.prompt_engineering import optimize_prompt


@pytest.fixture
def mock_vault():
    vault = MagicMock(spec=Vault)
    return vault


@pytest.fixture
def mock_model():
    model = MagicMock(spec=Model)
    model.model_name = "test-model"
    return model


def test_optimize_prompt(mock_model):
    current_prompt = "Original prompt"
    test_inputs = ["Input 1", "Input 2"]
    feedback = [{"comment": "Good job", "context": "Context"}]
    scores = ["Retro 1: 5"]

    with patch("aww.prompt_engineering.Agent") as MockAgent:
        mock_agent_instance = MockAgent.return_value
        
        # Mock run method (async)
        mock_result = MagicMock()
        mock_result.output = "Rewritten prompt"
        mock_agent_instance.run = AsyncMock(return_value=mock_result)

        with patch("aww.prompt_engineering.create_model", return_value=mock_model):
            result = optimize_prompt(
                critique_model_name="local",
                llm_model=mock_model,
                current_prompt=current_prompt,
                test_inputs=test_inputs,
                feedback=feedback,
                scores=scores,
            )

            assert result == "Rewritten prompt"
            assert mock_agent_instance.run.call_count == 2


def test_rewrite_prompt_motd(mock_vault, mock_model):
    runner = CliRunner()
    
    # Mock get_motd_context
    with patch("aww.cli.motd.get_motd_context", return_value=["Context 1"]):
        # Mock optimize_prompt
        with patch("aww.prompt_engineering.optimize_prompt", return_value="Optimized MOTD Prompt") as mock_optimize:
            # Mock Path.read_text and write_text
            with patch("pathlib.Path.read_text", return_value="Original MOTD Prompt"):
                with patch("pathlib.Path.write_text") as mock_write:
                    
                    result = runner.invoke(
                        main,
                        ["rewrite-prompt", "motd", "--feedback", "More energy"],
                        obj={"vault": mock_vault, "llm_model": mock_model},
                    )

                    assert result.exit_code == 0
                    assert "Optimized MOTD Prompt" in result.output
                    
                    mock_optimize.assert_called_once()
                    call_args = mock_optimize.call_args
                    assert call_args.kwargs["current_prompt"] == "Original MOTD Prompt"
                    assert call_args.kwargs["test_inputs"] == ["Context 1"]
                    assert call_args.kwargs["feedback"] == [{"comment": "More energy", "context": "CLI Feedback"}]
                    
                    mock_write.assert_called_once_with("Optimized MOTD Prompt")
