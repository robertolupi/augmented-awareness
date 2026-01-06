import asyncio
import datetime

from pydantic_ai.models.test import TestModel

from aww import retro, retro_gen
from aww.obsidian import Level
from aww.retro_gen import RecursiveRetrospectiveGenerator
from aww.test_retro import tmp_vault  # keep


class RecursiveRetrospectiveGeneratorForTesting(
    retro_gen.RecursiveRetrospectiveGenerator
):
    def __init__(self, sel: retro.Selection):
        model = TestModel()
        super().__init__(model, sel)
        self.saved_nodes = {}

    async def save_retro_page(self, node, output, sources, levels, retro_frontmatter):
        await super().save_retro_page(node, output, sources, levels, retro_frontmatter)
        self.saved_nodes[node.retro_page] = (node, sources, levels)


def test_recursive_retrospective_generator(tmp_vault):
    sel = retro.Selection(tmp_vault, datetime.date(2025, 4, 1), Level.yearly)
    g = RecursiveRetrospectiveGeneratorForTesting(sel)
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

    node, sources, levels = g.saved_nodes[yearly]
    assert node.retro_page == yearly
    assert levels == set(Level)
    source_pages = set(s.retro_page for s in sources)
    # 2025 has 53 ISO weeks
    assert len(source_pages) == 365 + 53 + 12


def test_recursive_retrospective_generator_rename_on_disk(tmp_vault):
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

    g = RecursiveRetrospectiveGenerator(model, sel)

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
