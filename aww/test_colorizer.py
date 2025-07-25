import pytest
from aww.colorizer import colorize_markdown, get_color_for_cluster


def test_get_color_for_cluster():
    """Tests the color generation logic."""
    assert get_color_for_cluster(-1) == ""
    assert get_color_for_cluster(0) == "#FFADAD"
    assert get_color_for_cluster(8) == "#FFADAD"  # Test wrap around


def test_colorize_markdown_with_markdown_present():
    """
    Tests that colorization works correctly when the sentence
    itself contains markdown syntax.
    """
    content = "A sentence with **bold** text."
    sentences = ["A sentence with **bold** text."]  # Sentence now contains markdown
    clusters = [0]
    color0 = get_color_for_cluster(0)
    expected = f'<span style="background-color: {color0};">{content}</span>'
    colorized = colorize_markdown(content, sentences, clusters)
    assert colorized == expected


def test_colorize_plain_text_correctly():
    """Tests if colorization works as expected on plain text without markdown."""
    content = "First sentence. Second sentence."
    sentences = ["First sentence.", "Second sentence."]
    clusters = [0, 1]
    color0 = get_color_for_cluster(0)
    color1 = get_color_for_cluster(1)
    expected = f'<span style="background-color: {color0};">First sentence.</span> <span style="background-color: {color1};">Second sentence.</span>'
    colorized = colorize_markdown(content, sentences, clusters)
    assert colorized == expected