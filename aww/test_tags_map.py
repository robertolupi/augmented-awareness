from aww.cli import tags as tags_cli


def test_normalize_tag():
    assert tags_cli.normalize_tag(" Mental-Health ") == "mental_health"
    assert tags_cli.normalize_tag("health/mental") == "health/mental"
    assert tags_cli.normalize_tag("time   blocking") == "time_blocking"
    assert tags_cli.normalize_tag("CreatorVsConsumer") == "creator_vs_consumer"
    assert tags_cli.normalize_tag("CalmButEmpty") == "calm_but_empty"


def test_suggest_canonical_tag():
    canonical = {"mental_health", "health/mental"}
    assert tags_cli.suggest_canonical_tag("Mental-Health", canonical) == "mental_health"
    assert tags_cli.suggest_canonical_tag("health/mental", canonical) == "health/mental"
    assert tags_cli.suggest_canonical_tag("unknown", canonical) is None
