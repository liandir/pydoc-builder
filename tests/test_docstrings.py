from __future__ import annotations

import sys
import textwrap
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from pydoc_builder.docstrings import doc_block


class DocstringMarkdownTests(unittest.TestCase):
    def test_plain_docstring_renders_markdown_and_preserves_protected_blocks(self) -> None:
        rendered = doc_block(
            textwrap.dedent(
                r"""
                Intro with **bold** and *italic*.

                # Details

                > Read [the guide](https://example.com).

                | Item | State |
                | --- | --- |
                | `value` | **ready** |

                ```python
                print("**code**")
                ```

                    **literal**

                \[
                    **math**
                \]
                """
            ).strip()
        )

        self.assertIn("<strong>bold</strong>", rendered)
        self.assertIn("<em>italic</em>", rendered)
        self.assertIn("<h1>Details</h1>", rendered)
        self.assertIn("<blockquote>", rendered)
        self.assertIn("<table>", rendered)
        self.assertIn('class="language-python"', rendered)
        self.assertIn('print(&quot;**code**&quot;)', rendered)
        self.assertIn('<pre class="doc-literal">    **literal**</pre>', rendered)
        self.assertIn('<div class="math-block">\\[\n**math**\n\\]</div>', rendered)
        self.assertNotIn("<strong>literal</strong>", rendered)
        self.assertNotIn("<strong>math</strong>", rendered)

    def test_structured_sections_render_markdown_in_prose_and_fields(self) -> None:
        rendered = doc_block(
            textwrap.dedent(
                """
                Perform an **important** operation with `Widget`.

                Args:
                    value (str): Read [the guide](https://example.com).
                        - first **choice**
                        - second choice

                Returns:
                    bool: Whether the *operation* succeeded.

                Examples
                    Use **carefully**.

                    >>> print("**not emphasis**")
                """
            ).strip(),
            lambda token: "#api-widget" if token == "Widget" else None,
        )

        self.assertIn("<strong>important</strong>", rendered)
        self.assertIn('class="api-xref" href="#api-widget"', rendered)
        self.assertIn('<a href="https://example.com">the guide</a>', rendered)
        self.assertIn("<li>first <strong>choice</strong></li>", rendered)
        self.assertIn("Whether the <em>operation</em> succeeded.", rendered)
        self.assertIn("Use <strong>carefully</strong>.", rendered)
        self.assertIn('&gt;&gt;&gt; print(&quot;**not emphasis**&quot;)', rendered)
        self.assertNotIn("<strong>not emphasis</strong>", rendered)


if __name__ == "__main__":
    unittest.main()
