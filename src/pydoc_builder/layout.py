"""Shared HTML, CSS, and MathJax setup for every generated page."""

from __future__ import annotations

from .utils import escape


_CSS = """
    :root {
      color-scheme: light;
      --ink: #1c2024;
      --muted: #687076;
      --line: #dfe3e6;
      --panel: #f7f9fa;
      --accent: #0f766e;
      --accent-dark: #115e59;
      --code: #263238;
      --field-name: #9a3412;
      --field-type: #6d28d9;
      --bg: #ffffff;
      --heading-large: clamp(1.6rem, 3vw, 2.4rem);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font: 16px/1.55 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    a { color: var(--accent-dark); text-decoration: none; }
    a:hover { text-decoration: underline; }
    h1, h2, h3 { line-height: 1.18; margin: 0 0 0.7rem; }
    h1 { font-size: var(--heading-large); max-width: 980px; }
    h2 { font-size: 1.35rem; margin-top: 2rem; }
    .home-hero { margin: 0 0 1.4rem; }
    .home-hero h1,
    .readme > h1:first-child {
      font-size: var(--heading-large);
      margin: 0 0 0.9rem;
      max-width: none;
    }
    .readme {
      margin: 0 0 1.75rem;
      padding: 0;
    }
    .readme h1 { font-size: 1.55rem; margin-top: 1.4rem; max-width: none; }
    .readme h2 { font-size: 1.3rem; margin-top: 1.4rem; }
    .readme h3 { font-size: 1.1rem; margin-top: 1.2rem; }
    .readme p { margin: 0.7rem 0; }
    .readme ul, .readme ol { margin: 0.7rem 0; padding-left: 1.5rem; }
    .readme li { margin: 0.25rem 0; }
    .readme code {
      background: var(--panel);
      padding: 0.1em 0.32em;
      border-radius: 4px;
      font-size: 0.92em;
    }
    .readme pre {
      background: var(--panel);
      padding: 0.85rem 1rem;
      border-radius: 8px;
      border: 1px solid var(--line);
      overflow-x: auto;
      margin: 0.85rem 0;
    }
    .readme pre code { background: none; padding: 0; font-size: 0.92em; }
    .readme blockquote {
      border-left: 3px solid var(--accent);
      padding: 0.1rem 0 0.1rem 0.9rem;
      margin: 0.85rem 0;
      color: var(--muted);
    }
    .readme hr {
      border: 0;
      border-top: 1px solid var(--line);
      margin: 1.5rem 0;
    }
    .inherits {
      display: block;
      margin-top: 0.25rem;
      color: var(--muted);
      font-size: 0.92rem;
      font-weight: 500;
    }
    .superclass {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }
    code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
    .eyebrow {
      color: var(--accent-dark);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: uppercase;
      font-size: 0.78rem;
    }
    section { padding: 0; }
    .module-list {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 0.65rem;
      padding: 0;
      list-style: none;
    }
    .module-list li {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      overflow-wrap: anywhere;
      transition: border-color 0.15s ease, background 0.15s ease, transform 0.15s ease;
    }
    .module-list li.card { padding: 0; }
    .module-list li.card > a {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
      padding: 0.8rem 0.95rem;
      color: inherit;
      text-decoration: none;
      border-radius: inherit;
    }
    .module-list li.card:hover {
      border-color: var(--accent);
      background: var(--panel);
      transform: translateY(-1px);
    }
    .module-list li.card .card-title { color: var(--accent-dark); font-weight: 600; }
    .module-list li.card .card-detail { color: var(--muted); }
    .module-list li:not(.card) { padding: 0.8rem 0.95rem; }
    .module-list.detailed li:not(.card) { display: flex; flex-direction: column; gap: 0.25rem; }
    .module-list span, .muted { color: var(--muted); }
    .directory-section { padding: 0; margin-top: 2rem; }
    .split {
      display: flex;
      align-items: stretch;
      min-height: 100vh;
    }
    .side {
      flex: 0 0 auto;
      width: 320px;
      min-width: 220px;
      max-width: 640px;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      resize: horizontal;
      padding: 1.25rem;
      border-right: 1px solid var(--line);
      background: var(--panel);
    }
    .side::-webkit-resizer {
      background:
        linear-gradient(135deg, transparent 45%, var(--muted) 45%, var(--muted) 55%, transparent 55%);
    }
    .side h2 {
      margin: 0 0 0.55rem;
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
    }
    .side ul { list-style: none; padding: 0; margin: 0; }
    .side li { margin: 0.35rem 0; overflow-wrap: anywhere; }
    .back {
      display: block;
      font-weight: 700;
      color: var(--accent-dark);
    }
    .side-section {
      border-bottom: 1px solid var(--line);
      padding-bottom: 1rem;
      margin-bottom: 1rem;
    }
    .side-section:last-child {
      border-bottom: 0;
      margin-bottom: 0;
      padding-bottom: 0;
    }
    .source-tree, .source-tree ul {
      list-style: none;
      padding-left: 0;
      margin: 0;
    }
    .source-tree li {
      margin: 0.25rem 0;
    }
    .source-tree li > ul {
      margin-top: 0.3rem;
      margin-left: 0.35rem;
      padding-left: 0.7rem;
      border-left: 2px solid var(--line);
    }
    .current-source {
      color: var(--ink);
      font-weight: 700;
    }
    .toc-list ul {
      margin: 0.25rem 0 0.55rem 0.8rem;
      padding-left: 0.7rem;
      border-left: 2px solid var(--line);
    }
    .toc-list a {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 0.45rem;
      align-items: baseline;
      padding: 0.2rem 0;
    }
    .toc-kind {
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--muted);
      font-size: 0.68rem;
      line-height: 1;
      padding: 0.18rem 0.35rem;
      text-transform: uppercase;
    }
    .toc-name {
      overflow-wrap: anywhere;
    }
    .content { flex: 1 1 0; min-width: 0; padding: 2.5rem min(6vw, 4rem); max-width: 1100px; }
    .api-object {
      border-top: 1px solid var(--line);
      padding-top: 1.3rem;
      margin-top: 1.6rem;
    }
    .api-object .api-object {
      margin-left: 1rem;
      padding-left: 1rem;
      border-left: 3px solid var(--line);
    }
    .object-meta {
      color: var(--muted);
      font-size: 0.85rem;
      margin-bottom: 0.25rem;
    }
    .docstring {
      margin: 0.7rem 0 1.1rem;
    }
    .structured-docstring {
      white-space: normal;
      overflow-x: visible;
    }
    .structured-docstring p {
      margin: 0 0 0.9rem;
    }
    .doc-section {
      padding: 0;
      margin-top: 1rem;
    }
    .doc-section h3 {
      margin: 0 0 0.55rem;
      color: var(--accent-dark);
      font-size: 1.1rem;
    }
    .doc-fields {
      display: grid;
      gap: 0.55rem;
      margin: 0;
    }
    .doc-field {
      display: grid;
      grid-template-columns: minmax(140px, 260px) minmax(0, 1fr);
      gap: 0.85rem;
      border-top: 1px solid var(--line);
      padding-top: 0.55rem;
    }
    .doc-field dt {
      display: flex;
      flex-wrap: wrap;
      align-content: flex-start;
      gap: 0.35rem;
      min-width: 0;
    }
    .doc-field dd {
      margin: 0;
      min-width: 0;
    }
    .doc-field-name {
      color: var(--field-name);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
      font-weight: 700;
    }
    .doc-field-type {
      color: var(--field-type);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }
    .doc-field-type::before { content: "("; color: #4b5563; }
    .doc-field-type::after { content: ")"; color: #4b5563; }
    .doc-extra {
      white-space: pre-wrap;
      overflow-x: auto;
      margin: 1rem 0 0;
    }
    .plain-docstring {
      white-space: normal;
      overflow-x: visible;
    }
    .plain-docstring p {
      margin: 0 0 0.9rem;
    }
    .doc-literal {
      white-space: pre-wrap;
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0.9rem;
      background: #ffffff;
      margin: 0.7rem 0 0.9rem;
    }
    .math-block {
      margin: 0.9rem 0;
      overflow-x: auto;
    }
    .example-code {
      white-space: pre-wrap;
      overflow-x: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0.9rem;
      background: #ffffff;
      margin: 0.6rem 0 0;
    }
    .source-block {
      margin: 0.3rem 0 0.6rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #ffffff;
      overflow: hidden;
    }
    .source-block > summary {
      cursor: pointer;
      list-style: none;
      padding: 0.85rem 1.05rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      background: var(--panel);
    }
    .source-block > summary::-webkit-details-marker { display: none; }
    .source-block > summary:hover { background: #eef2f4; }
    .summary-heading {
      flex: 1 1 auto;
      min-width: 0;
    }
    .summary-heading h1,
    .summary-heading h2 {
      margin: 0;
      font-weight: 700;
      color: var(--ink);
    }
    .summary-heading h1 { font-size: var(--heading-large); }
    .summary-heading h2 { font-size: 1.55rem; }
    .api-object .api-object .summary-heading h2 {
      font-size: 1.25rem;
    }
    .source-toggle {
      flex: 0 0 auto;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .source-caret {
      display: inline-block;
      transition: transform 0.15s ease;
    }
    .source-block[open] .source-caret { transform: rotate(90deg); }
    .source-pane {
      display: flex;
      align-items: stretch;
      background: #fafafa;
      border-top: 1px solid var(--line);
      font-size: 0.88rem;
      line-height: 1.55;
      color: #000000;
      overflow: hidden;
    }
    .source-pane > pre {
      margin: 0;
      font-size: inherit;
      line-height: inherit;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }
    .source-gutter {
      padding: 1rem 0.7rem 1rem 1rem;
      color: #b0b3b8;
      text-align: right;
      user-select: none;
      background: #f3f3f3;
      border-right: 1px solid var(--line);
      white-space: pre;
    }
    .source-code {
      padding: 1rem 1.1rem;
      flex: 1 1 auto;
      min-width: 0;
      overflow-x: auto;
      white-space: pre;
    }
    /* VS Code Light Modern palette */
    .tok-keyword      { color: #0000ff; }
    .tok-string       { color: #a31515; }
    .tok-number       { color: #098658; }
    .tok-comment      { color: #008000; font-style: italic; }
    .tok-def-name     { color: #795e26; }
    .tok-class-name   { color: #267f99; }
    .tok-self         { color: #0000ff; }
    .tok-builtin-type { color: #267f99; }
    .tok-builtin-func { color: #795e26; }
    .tok-punct        { color: #000000; }
    @media (max-width: 860px) {
      .split { display: block; }
      .side {
        flex: none;
        width: auto;
        max-width: none;
        min-width: 0;
        resize: none;
        position: static;
        height: auto;
        max-height: 45vh;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }
      .content { padding: 1.5rem; }
      .doc-field { grid-template-columns: 1fr; gap: 0.2rem; }
      section, .hero { padding-left: 1.25rem; padding-right: 1.25rem; }
    }
"""


_MATHJAX_HEAD = r"""  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\(', '\\)']],
        displayMath: [['$$', '$$'], ['\\[', '\\]']]
      },
      svg: { fontCache: 'global' }
    };
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>"""


def page(title: str, body: str, *, layout: str = "split") -> str:
    """Wrap page content in shared HTML, CSS, and metadata."""

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{escape(title)}</title>\n"
        f"{_MATHJAX_HEAD}\n"
        f"  <style>{_CSS}  </style>\n"
        "</head>\n"
        f'<body class="{escape(layout)}">\n'
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )
