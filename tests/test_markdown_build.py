from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from pydoc_builder import BuildConfig, build


class MarkdownBuildTests(unittest.TestCase):
    def test_markdown_is_rendered_on_module_pages_and_summary_cards(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            package_dir = project_root / "src" / "example"
            package_dir.mkdir(parents=True)
            (package_dir / "__init__.py").write_text('"""Example package."""\n', encoding="utf-8")
            (package_dir / "sample.py").write_text(
                '"""Uses **bold** and *italic*."""\n',
                encoding="utf-8",
            )
            docs_dir = project_root / "docs"

            build(
                BuildConfig(
                    project_root=project_root,
                    docs_dir=docs_dir,
                    main_root=project_root / "src",
                    check_arg_docs=False,
                )
            )

            module_html = (docs_dir / "api" / "src" / "example" / "sample.html").read_text(
                encoding="utf-8"
            )
            package_html = (docs_dir / "api" / "src" / "example" / "index.html").read_text(
                encoding="utf-8"
            )

        expected = "Uses <strong>bold</strong> and <em>italic</em>."
        self.assertIn(f"<p>{expected}</p>", module_html)
        self.assertIn(f'<span class="card-detail">{expected}</span>', package_html)


if __name__ == "__main__":
    unittest.main()
