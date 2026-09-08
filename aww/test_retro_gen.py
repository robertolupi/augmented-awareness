import asyncio
import datetime

from pydantic_ai.models.test import TestModel

from aww import retro, retro_gen
from aww.obsidian import Level
from aww.retro_gen import RecursiveGenerator
from aww.test_retro import tmp_vault  # keep


class RecursiveGeneratorForTesting(
    retro_gen.RecursiveGenerator
):
    def __init__(self, sel: retro.Selection):
        model = TestModel()
        super().__init__(model, sel)
        self.saved_nodes = {}

    async def save_page(self, target_page, output, sources, levels, frontmatter, source_page=None):
        await super().save_page(target_page, output, sources, levels, frontmatter, source_page)
        self.saved_nodes[target_page] = (target_page, sources, levels)


def test_recursive_generator(tmp_vault):
    sel = retro.Selection(tmp_vault, datetime.date(2025, 4, 1), Level.yearly)
    g = RecursiveGeneratorForTesting(sel)
    asyncio.run(
        g.run(
            context_levels=list(Level),
            cache_policies=[
                retro.NoRootCachePolicy(),
                retro.NoLevelsCachePolicy(list(Level)),
            ],
        )
    )
    d = sel.dates[0]
    yearly = tmp_vault.retrospective_page(d, Level.yearly)

    march30 = datetime.date(2025, 3, 30)
    april1 = datetime.date(2025, 4, 1)
    d1 = tmp_vault.retrospective_page(march30, Level.daily)
    d2 = tmp_vault.retrospective_page(april1, Level.daily)
    w1 = tmp_vault.retrospective_page(march30, Level.weekly)
    w2 = tmp_vault.retrospective_page(april1, Level.weekly)
    march = tmp_vault.retrospective_page(march30, Level.monthly)
    april = tmp_vault.retrospective_page(april1, Level.monthly)

    sources_with_content = set(g.saved_nodes.keys())
    assert sources_with_content == {d1, d2, w1, w2, march, april, yearly}

    page, sources, levels = g.saved_nodes[yearly]
    assert page == yearly
    assert levels == set(Level)
    source_pages = set(s.retro_page for s in sources)
    # 2025 has 53 ISO weeks
    assert len(source_pages) == 365 + 53 + 12


def test_recursive_generator_rename_on_disk(tmp_vault):
    day = datetime.date(2025, 1, 1)
    sel = retro.Selection(tmp_vault, day, Level.daily)
    model = TestModel()

    # Create a fake journal file for the day
    journal_path = (
        tmp_vault.path
        / tmp_vault.journal_dir
        / f"{day.strftime('%Y')}/{day.strftime('%m')}/{day.strftime('%Y-%m-%d')}.md"
    )
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("w") as f:
        f.write("# Test Journal Entry")

    g = RecursiveGenerator(model, sel)

    # Run the generator twice
    asyncio.run(
        g.run(
            context_levels=list(Level),
            cache_policies=[
                retro.NoRootCachePolicy(),
                retro.NoLevelsCachePolicy(list(Level)),
            ],
        )
    )
    asyncio.run(
        g.run(
            context_levels=list(Level),
            cache_policies=[
                retro.NoRootCachePolicy(),
                retro.NoLevelsCachePolicy(list(Level)),
            ],
        )
    )

    retro_page = tmp_vault.retrospective_page(day, Level.daily)
    renamed_page_path = retro_page.path.with_suffix(".1.md")

    assert retro_page.path.exists()
    assert renamed_page_path.exists()


def test_retro_prompt_includes_canonical_tags(tmp_vault, monkeypatch):
    monkeypatch.setenv(
        "AWW_TAGS",
        '{"work":"Career/work tasks and outcomes","mental_health":"Mood and care"}',
    )
    sel = retro.Selection(tmp_vault, datetime.date(2025, 4, 1), Level.daily)
    model = TestModel()
    g = RecursiveGenerator(model, sel)

    prompt = g.prompts[Level.daily]
    assert "#work" in prompt
    assert "Career/work tasks and outcomes" in prompt
    assert "#mental_health" in prompt


def test_page_content_ignores_journal_headers(tmp_vault):
    day = datetime.date(2025, 1, 1)
    journal_page = tmp_vault.page(day, Level.daily)
    journal_page.path.parent.mkdir(parents=True, exist_ok=True)
    journal_page.path.write_text(
        "# Journal\n\n## Gratitude\n- Coffee\n\n## Log\nDid things.\n"
    )

    daily_node = retro.Node(
        dates={day},
        level=Level.daily,
        retro_page=tmp_vault.retrospective_page(day, Level.daily),
        page=journal_page,
        sources=set(),
    )

    content = asyncio.run(retro_gen.page_content(daily_node, ["Gratitude"]))
    assert "Did things." in content
    assert "Gratitude" not in content
    assert "Coffee" not in content

    # Non-daily pages are not filtered
    weekly_node = retro.Node(
        dates={day},
        level=Level.weekly,
        retro_page=tmp_vault.retrospective_page(day, Level.weekly),
        page=journal_page,
        sources=set(),
    )
    content = asyncio.run(retro_gen.page_content(weekly_node, ["Gratitude"]))
    assert "Gratitude" in content


def test_recursive_generator_skips_missing_daily(tmp_vault, capsys):
    missing_day = datetime.date(2025, 1, 15)
    sel = retro.Selection(tmp_vault, missing_day, Level.daily)
    model = TestModel()
    g = RecursiveGenerator(model, sel)

    result = asyncio.run(
        g.run(
            context_levels=list(Level),
            cache_policies=[
                retro.NoRootCachePolicy(),
                retro.NoLevelsCachePolicy(list(Level)),
            ],
        )
    )

    assert result is None
    captured = capsys.readouterr()
    assert f"Missing daily journal file for {missing_day}" in captured.out
    retro_page = tmp_vault.retrospective_page(missing_day, Level.daily)
    assert not retro_page.path.exists()



def test_follow_links_disabled_by_default(tmp_vault):
    sel = retro.Selection(tmp_vault, datetime.date(2025, 4, 1), Level.daily)
    g = RecursiveGenerator(TestModel(), sel)
    assert "read_pages_tool" not in g.agents[Level.daily]._function_toolset.tools
    assert "wiki links" not in g.prompts[Level.daily]
    assert g.deps is None


def test_follow_links_registers_read_pages_tool(tmp_vault, monkeypatch):
    monkeypatch.setenv("AWW_FOLLOW_LINKS", "true")
    sel = retro.Selection(tmp_vault, datetime.date(2025, 4, 1), Level.daily)
    g = RecursiveGenerator(TestModel(), sel)
    assert "read_pages_tool" in g.agents[Level.daily]._function_toolset.tools
    assert "wiki links" in g.prompts[Level.daily]
    assert g.deps.vault is tmp_vault


def test_recursive_generator_follows_wiki_links(tmp_vault, monkeypatch):
    from pydantic_ai.messages import (
        ModelResponse,
        TextPart,
        ToolCallPart,
        ToolReturnPart,
        UserPromptPart,
    )
    from pydantic_ai.models.function import FunctionModel

    monkeypatch.setenv("AWW_FOLLOW_LINKS", "true")
    day = datetime.date(2025, 1, 1)

    journal_page = tmp_vault.page(day, Level.daily)
    journal_page.path.parent.mkdir(parents=True, exist_ok=True)
    journal_page.path.write_text(
        "# Journal\n\nI created a [[Personal Values Charter]] with ChatGPT.\n"
    )
    charter = tmp_vault.path / "Personal Values Charter.md"
    charter.write_text("# Personal Values Charter\n\nI value integrity and curiosity.\n")

    tool_returns = []
    user_prompts = []

    def fake_model(messages, info):
        for m in messages:
            for p in getattr(m, "parts", []):
                if isinstance(p, ToolReturnPart) and p.tool_name == "read_pages_tool":
                    tool_returns.append(p.content)
                    return ModelResponse(parts=[TextPart("Summary after reading.")])
                if isinstance(p, UserPromptPart):
                    user_prompts.append(str(p.content))
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name="read_pages_tool",
                    args={"pages": ["Personal Values Charter"]},
                )
            ]
        )

    sel = retro.Selection(tmp_vault, day, Level.daily)
    g = RecursiveGenerator(FunctionModel(fake_model), sel)
    result = asyncio.run(
        g.run(
            context_levels=list(Level),
            cache_policies=[
                retro.NoRootCachePolicy(),
                retro.NoLevelsCachePolicy(list(Level)),
            ],
        )
    )

    assert result is not None
    assert tool_returns, "agent never called read_pages_tool"
    assert "I value integrity and curiosity." in tool_returns[0]
    assert any(
        "Linked pages referenced in the input: [[Personal Values Charter]]" in p
        for p in user_prompts
    )
    assert tmp_vault.retrospective_page(day, Level.daily).path.exists()
