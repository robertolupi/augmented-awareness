from aww.chat import render_chat_system_prompt
from aww.obsidian import Page, Vault


def test_render_chat_system_prompt_includes_skills_and_scratchpad(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "focus.md").write_text(
        "---\ndescription: Stay focused on the next task.\n---\n# Focus\n"
    )
    (skills_dir / "ignored.md").write_text("---\nother: value\n---\n# Ignored\n")

    scratchpad_path = tmp_path / "aww-scratchpad.md"
    scratchpad_path.write_text("# Memory\nRemember this.\n")

    vault = Vault(tmp_path, "journal", "retrospectives", "retrospectives/queries")
    prompt = render_chat_system_prompt(vault, Page(scratchpad_path))

    assert "Available skills (loadable with `load_skill_tool`):" in prompt
    assert "- focus: Stay focused on the next task." in prompt
    assert "ignored" not in prompt
    assert "Use `python_eval_tool` when you need reliable arithmetic or date/time calculations." in prompt
    assert "The content of your memories in the [[aww-scratchpad]] page is:" in prompt
    assert "# Memory\nRemember this.\n" in prompt


def test_render_chat_system_prompt_omits_optional_sections_when_empty(tmp_path):
    vault = Vault(tmp_path, "journal", "retrospectives", "retrospectives/queries")

    prompt = render_chat_system_prompt(vault, None)

    assert "Available skills" not in prompt
    assert "aww-scratchpad" not in prompt
    assert "restricted\nsubset of Python expressions" in prompt
