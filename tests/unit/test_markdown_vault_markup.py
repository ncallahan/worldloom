"""Direct tests for Markdown-vault markup helpers."""

from __future__ import annotations

import pytest

from worldloom.adapters.markdown_vault.markup import (
    code_span,
    display_text,
    frontmatter,
    link,
    safe_text,
    text_field,
    yaml_value,
)


def test_yaml_value_serialises_bool_none_numbers_quotes_newlines_and_unicode():
    assert yaml_value(True) == "true"
    assert yaml_value(False) == "false"
    assert yaml_value(None) == "null"
    assert yaml_value(12) == "12"
    assert yaml_value(1.5) == "1.5"
    assert yaml_value('quote " and newline\n café') == '"quote \\" and newline\\n café"'


def test_frontmatter_renders_list_values():
    assert frontmatter([("enabled", True), ("aliases", ["North", "South"]), ("nothing", None)]) == (
        "---\n"
        "enabled: true\n"
        "aliases:\n"
        '  - "North"\n'
        '  - "South"\n'
        "nothing: null\n"
        "---"
    )


def test_safe_text_chooses_fence_longer_than_embedded_backticks():
    tick = chr(96)
    value = {"text": "before " + tick * 2 + " inside"}
    rendered = safe_text(value, "entity test:000000000001.attributes['text']")
    assert rendered.startswith(tick * 3)
    assert rendered.endswith(tick * 3)
    assert '"text":"before ' + tick * 2 + ' inside"' in rendered


def test_safe_text_nonserialisable_value_names_source_path():
    path = "entity test:000000000001.attributes['bad']"
    with pytest.raises(ValueError, match="Value at entity test:000000000001.attributes"):
        safe_text({1, 2}, path)


def test_display_text_escapes_wikilink_delimiters():
    assert display_text("a|b[c]") == "a\\|b\\[c\\]"


def test_code_span_handles_empty_edge_backticks_and_multiline():
    tick = chr(96)
    assert code_span("") == tick + "  " + tick
    assert code_span(tick + "edge") == tick * 2 + " " + tick + "edge " + tick * 2
    assert code_span("one\r\ntwo") == tick + "one two" + tick
    assert code_span("x" + tick * 2 + "y") == tick * 3 + "x" + tick * 2 + "y" + tick * 3


def test_text_field_uses_minimum_three_backticks_and_expands_as_needed():
    tick = chr(96)
    assert text_field("plain\ntext") == tick * 3 + "text\nplain\ntext\n" + tick * 3
    assert text_field("has " + tick * 3 + " fence") == tick * 4 + "text\nhas " + tick * 3 + " fence\n" + tick * 4


def test_link_removes_md_suffix_and_escapes_display():
    assert link("test/North (abcdef012345).md", "North | [West]") == (
        r"[[test/North (abcdef012345)|North \| \[West\]]]"
    )
