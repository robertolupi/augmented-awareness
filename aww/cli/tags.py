import datetime
import difflib
import re

import click

from aww import database, retro
from aww.cli import main
from aww.obsidian import Level


@main.group()
def tags():
    """Manage tags."""
    pass


@tags.command()
@click.option(
    "-l",
    "--level",
    type=click.Choice(Level, case_sensitive=False),
    default="daily",
    help="Selection level for collection.",
)
@click.option(
    "-d",
    "--date",
    type=click.DateTime(),
    default=datetime.date.today().isoformat(),
    help="Reference date for collection.",
)
@click.pass_context
def collect(ctx, level, date):
    """Collect tags from the vault for a given period."""
    vault = ctx.obj["vault"]
    settings = ctx.obj["settings"]
    db_path = database.get_db_path(settings)
    database.init_db(db_path)

    level = Level(level)
    sel = retro.Selection(vault, date.date(), level)

    for node in sel.tree.values():
        # Source date for the record: use the representative date (min of dates)
        source_date = min(node.dates).isoformat()

        # Process journal page
        if node.page and node.page.path.exists():
            database.save_page_tags(
                db_path,
                source_date,
                "journal",
                node.level.value,
                node.page.path,
                None,
                None,
                node.page.tags(),
            )

        # Process retrospective page
        if node.retro_page and node.retro_page.path.exists():
            fm = node.retro_page.frontmatter()
            sys_hash = fm.get("sys_prompt_hash")
            user_hash = fm.get("user_prompt_hash")
            database.save_page_tags(
                db_path,
                source_date,
                "retrospective",
                node.level.value,
                node.retro_page.path,
                sys_hash,
                user_hash,
                node.retro_page.tags(),
            )

    click.echo(f"Tags collected in {db_path}")


@tags.command(name="list")
@click.argument("period", type=click.DateTime(), nargs=2, required=False)
@click.option(
    "-l",
    "--level",
    type=click.Choice(Level, case_sensitive=False),
    help="Filter by level.",
)
@click.option(
    "--output",
    type=click.Choice(["frequency", "references"]),
    default="frequency",
    help="Output format: frequency count or page references.",
)
@click.pass_context
def list_tags(ctx, period, level, output):
    """List all tags in a given period (two dates)."""
    settings = ctx.obj["settings"]
    db_path = database.get_db_path(settings)
    if not db_path.exists():
        click.echo("Database not found. Run 'collect' first.")
        return

    start_date = None
    end_date = None
    if period:
        start_date = period[0].date().isoformat()
        end_date = period[1].date().isoformat()

    if output == "frequency":
        results = database.get_tags_frequency(
            db_path, start_date, end_date, level
        )
        if not results:
            click.echo("No tags found for the given criteria.")
            return

        for name, freq in results:
            click.echo(f"{freq:4d} {name}")
    else:
        results = database.get_tags_references(
            db_path, start_date, end_date, level
        )
        if not results:
            click.echo("No tags found for the given criteria.")
            return

        current_tag = None
        for tag_name, s_date, kind, lvl, path in results:
            if tag_name != current_tag:
                if current_tag is not None:
                    click.echo("")
                click.echo(f"#{tag_name}:")
                current_tag = tag_name
            click.echo(f"  - {s_date} [{kind}/{lvl}] {path}")


def normalize_tag(tag: str) -> str:
    tag = tag.strip()
    tag = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", tag)
    tag = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", tag)
    tag = tag.lower()
    tag = re.sub(r"\s+", "_", tag)
    tag = tag.replace("-", "_")
    tag = re.sub(r"_+", "_", tag)
    return tag


def suggest_canonical_tag(tag: str, canonical_tags: set[str]) -> str | None:
    normalized = normalize_tag(tag)
    if normalized in canonical_tags:
        return normalized
    return None


@tags.command()
@click.option(
    "--min-count",
    type=int,
    default=10,
    show_default=True,
    help="Skip consolidation for tags with frequency >= min-count.",
)
@click.option(
    "--dry-run/--apply",
    default=True,
    show_default=True,
    help="Report-only mode; apply is currently a no-op.",
)
@click.pass_context
def map(ctx, min_count, dry_run):
    """Suggest canonical tag mappings based on existing tags."""
    settings = ctx.obj["settings"]
    db_path = database.get_db_path(settings)
    if not db_path.exists():
        click.echo("Database not found. Run 'collect' first.")
        return

    canonical_tags = {
        normalize_tag(tag) for tag in (settings.tags or {}).keys() if tag.strip()
    }
    if not canonical_tags:
        click.echo("No canonical tags configured in aww.toml.")
        return

    results = database.get_tags_frequency(db_path)
    if not results:
        click.echo("No tags found. Run 'collect' first.")
        return

    suggested = []
    unmapped = []
    skipped = []
    already_canonical = []

    for tag_name, freq in results:
        if min_count is not None and freq >= min_count:
            skipped.append((tag_name, freq))
            continue

        normalized = normalize_tag(tag_name)
        if normalized == tag_name:
            continue
        if normalized in canonical_tags and tag_name == normalized:
            already_canonical.append((tag_name, freq))
            continue

        if canonical := suggest_canonical_tag(tag_name, canonical_tags):
            suggested.append((tag_name, canonical, freq))
        else:
            close = difflib.get_close_matches(
                normalized, sorted(canonical_tags), n=3, cutoff=0.8
            )
            unmapped.append((tag_name, normalized, freq, close))

    click.echo("Suggested canonical mappings (auto):")
    if suggested:
        for tag_name, canonical, freq in suggested:
            click.echo(f"  {freq:4d} {tag_name} -> {canonical}")
    else:
        click.echo("  (none)")

    click.echo("\nUnmapped tags (review):")
    if unmapped:
        for tag_name, normalized, freq, close in unmapped:
            if close:
                click.echo(
                    f"  {freq:4d} {tag_name} (normalized: {normalized})"
                    f" close: {', '.join(close)}"
                )
            else:
                click.echo(f"  {freq:4d} {tag_name} (normalized: {normalized})")
    else:
        click.echo("  (none)")

    click.echo("\nAlready canonical (skipped):")
    if already_canonical:
        for tag_name, freq in already_canonical:
            click.echo(f"  {freq:4d} {tag_name}")
    else:
        click.echo("  (none)")

    click.echo("\nSkipped due to min-count:")
    if skipped:
        for tag_name, freq in skipped:
            click.echo(f"  {freq:4d} {tag_name}")
    else:
        click.echo("  (none)")

    if not dry_run:
        click.echo("\nApply mode is not implemented; no changes were made.")
