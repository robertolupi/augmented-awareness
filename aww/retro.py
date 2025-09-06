import calendar
from dataclasses import dataclass
import datetime
from typing import Dict, Callable, Sequence, Protocol

from aww.obsidian import Level, Page, Vault


@dataclass
class Node:
    """
    Represents a node in the retrospective dependency tree.
    Holds references to dates, level, associated pages, sources, and cache usage.
    """

    dates: set[datetime.date]
    level: Level
    retro_page: Page
    page: Page
    sources: set["Node"]
    use_cache: bool = True

    def __eq__(self, other):
        """Equality based on retro_page."""
        return isinstance(other, Node) and (self.retro_page == other.retro_page)

    def __hash__(self):
        """Hash based on retro_page."""
        return hash(self.retro_page)

    def __lt__(self, other):
        """Order nodes by retro_page name for sorting."""
        if not isinstance(other, Node):
            return NotImplemented
        return self.retro_page.name < other.retro_page.name


# Type alias for a mapping from Page to Node in the retrospective tree.
Tree = Dict[Page, Node]


def build_retrospective_tree(vault: Vault, dates: list[datetime.date]) -> Tree:
    """
    Build a dependency tree of retrospectives for the given dates and vault.
    Each node represents a retrospective at a given level and date, with sources for lower levels.
    """
    tree = {}
    for d in dates:
        for l in Level:
            retro_page = vault.retrospective_page(d, l)
            if retro_page not in tree:
                r = Node(
                    dates=set(),
                    level=l,
                    retro_page=retro_page,
                    page=vault.page(d, l),
                    sources=set(),
                )
                tree[retro_page] = r
            else:
                r = tree[retro_page]
            r.dates.add(d)
            for i in Level:
                if i == l:
                    break
                prev_retro_page = vault.retrospective_page(d, i)
                r.sources.add(tree[prev_retro_page])
    return tree


class CachePolicy:
    def __call__(self, node: Node, tree: Tree):
        raise NotImplementedError("Subclass responsibility")


class NoRootCachePolicy(CachePolicy):
    """Cache policy that disables cache for the root node."""

    def __call__(self, node: Node, tree: Tree):
        """Disable cache for the given node (root)."""
        node.use_cache = False


class NoLevelsCachePolicy(CachePolicy):
    """Cache policy that disables cache for nodes at specified levels."""

    def __init__(self, levels: Sequence[Level]):
        """Initialize with a sequence of levels for which cache should be disabled."""
        self.levels = set(levels)

    def __call__(self, node: Node, tree: Tree):
        """Disable cache for sources of the node if their level is in the specified levels."""
        for source in node.sources:
            if source.level in self.levels:
                source.use_cache = False


class ModificationTimeCachePolicy(CachePolicy):
    """Cache policy that disables cache if the source page is newer than the retro page."""

    def __call__(self, node: Node, tree: Tree):
        """Disable cache for nodes where the source page modification time is newer than the retro page."""
        for n in tree.values():
            if not n.page or not n.retro_page:
                continue
            if n.page.mtime_ns() > n.retro_page.mtime_ns():
                n.use_cache = False


class TooOldCachePolicy(CachePolicy):
    """Cache policy that disables cache for retro pages older than a given datetime limit."""

    def __init__(self, limit: datetime.datetime):
        """Initialize with a datetime limit; retro pages older than this will not use cache."""
        self.limit = limit

    def __call__(self, node: Node, tree: Tree):
        """Disable cache for nodes whose retro page modification time is older than the limit."""
        limit_ns = self.limit.timestamp() * 1e9
        for n in tree.values():
            if not n.retro_page:
                continue
            if n.retro_page.mtime_ns() < limit_ns:
                n.use_cache = False


class Selection:
    """A selection of retrospectives."""

    vault: Vault
    dates: list[datetime.date]
    tree: Tree
    root: Node

    def __init__(
        self, vault: Vault, date: datetime.date | datetime.datetime, level: Level
    ):
        self.vault = vault
        # Accept both datetime.date and datetime.datetime
        if isinstance(date, datetime.datetime):
            d = date.date()
        elif isinstance(date, datetime.date):
            d = date
        else:
            raise TypeError("date must be datetime.date or datetime.datetime")
        match level:
            case Level.daily:
                dates = [d]
            case Level.weekly:
                dates = whole_week(d)
            case Level.monthly:
                dates = whole_month(d)
            case Level.yearly:
                dates = whole_year(d)
            case _:
                raise ValueError("Invalid selection level")
        self.tree = build_retrospective_tree(self.vault, dates)
        self.dates = dates
        root_retro = self.vault.retrospective_page(d, level)
        self.root = self.tree[root_retro]

    def apply_cache_policy(self, cache_policy: CachePolicy):
        cache_policy(self.root, self.tree)


def whole_year(the_date: datetime.date) -> list[datetime.date]:
    year = the_date.year
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    dates = [
        start_date + datetime.timedelta(days=i)
        for i in range((end_date - start_date).days + 1)
    ]
    return dates


def whole_month(the_date: datetime.date) -> list[datetime.date]:
    year = the_date.year
    month = the_date.month
    num_days = calendar.monthrange(year, month)[1]
    dates = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
    return dates


def whole_week(the_date: datetime.date) -> list[datetime.date]:
    """Returns the weekly dates (Mon to Friday) for the week that contains the given date."""
    monday = the_date - datetime.timedelta(days=the_date.weekday())
    return [monday + datetime.timedelta(days=i) for i in range(7)]
