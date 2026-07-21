from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from pydoc_builder.markdown import render_inline, render_markdown
from pydoc_builder.utils import escape, inline_markup


class InlineMarkdownTests(unittest.TestCase):
    def test_renders_emphasis_code_links_and_bare_urls(self) -> None:
        rendered = render_inline(
            "Use **bold**, *italic*, `code`, ``other`` and "
            "[the guide](https://example.com/guide). See https://example.com."
        )

        self.assertIn("<strong>bold</strong>", rendered)
        self.assertIn("<em>italic</em>", rendered)
        self.assertIn("<code>code</code>", rendered)
        self.assertIn("<code>other</code>", rendered)
        self.assertIn('<a href="https://example.com/guide">the guide</a>', rendered)
        self.assertIn('href="https://example.com"', rendered)

    def test_preserves_api_cross_references(self) -> None:
        rendered = render_inline(
            "See `Widget`.",
            lambda token: "#api-widget" if token == "Widget" else None,
        )

        self.assertIn(
            '<a class="api-xref" href="#api-widget"><code>Widget</code></a>',
            rendered,
        )

    def test_bare_url_inside_emphasis_does_not_consume_generated_html(self) -> None:
        rendered = render_inline("Visit **https://example.com** now.")

        self.assertIn(
            '<strong><a href="https://example.com" target="_blank" '
            'rel="noopener noreferrer">https://example.com</a></strong>',
            rendered,
        )

    def test_escapes_html_and_rejects_unsafe_link_schemes(self) -> None:
        rendered = render_inline('<script>alert("x")</script> [bad](javascript:alert(1))')

        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn('href="javascript:', rendered)

    def test_link_free_mode_is_safe_inside_a_linked_card(self) -> None:
        rendered = render_inline(
            "Read [the **guide**](https://example.com) or https://example.com.",
            allow_links=False,
        )

        self.assertEqual("Read the <strong>guide</strong> or https://example.com.", rendered)
        self.assertNotIn("<a ", rendered)

    def test_legacy_inline_helper_delegates_without_double_escaping(self) -> None:
        rendered = inline_markup(escape("Use **bold** and `code` <safely>."))

        self.assertEqual(
            "Use <strong>bold</strong> and <code>code</code> &lt;safely&gt;.",
            rendered,
        )


class BlockMarkdownTests(unittest.TestCase):
    def test_renders_the_supported_block_subset(self) -> None:
        rendered = render_markdown(
            """# Heading

> A **quote**

- first
- second

| Name | Value |
| --- | ---: |
| **one** | 1 |

---

```python
print("hello")
```
"""
        )

        self.assertIn("<h1>Heading</h1>", rendered)
        self.assertIn("<blockquote>A <strong>quote</strong></blockquote>", rendered)
        self.assertIn("<ul><li>first</li><li>second</li></ul>", rendered)
        self.assertIn("<table>", rendered)
        self.assertIn('<th style="text-align: right">Value</th>', rendered)
        self.assertIn("<hr>", rendered)
        self.assertIn('class="language-python"', rendered)
        self.assertIn('print(&quot;hello&quot;)', rendered)

    def test_supports_parenthesized_ordered_list_markers(self) -> None:
        rendered = render_markdown("1) first\n2) second")

        self.assertEqual("<ol><li>first</li><li>second</li></ol>", rendered)


if __name__ == "__main__":
    unittest.main()
