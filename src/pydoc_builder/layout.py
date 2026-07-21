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
      --accent: #0451a5;
      --accent-dark: #003d8b;
      --code: #263238;
      --field-name: #795e26;
      --field-type: #267f99;
      --bg: #ffffff;
      --surface: #ffffff;
      --hover-bg: #eef2f4;
      --source-bg: #fafafa;
      --gutter-bg: #f3f3f3;
      --gutter-fg: #b0b3b8;
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
    .home-hero {
      margin: 0 0 1.4rem;
      padding: 9rem 1.5rem;
      background: linear-gradient(to bottom, rgba(4, 81, 165, 0.12), rgba(4, 81, 165, 0));
      border-radius: 6px;
    }
    .home-hero h1 {
      font-size: clamp(1.35rem, 2.2vw, 1.8rem);
      margin: 0 0 0.4rem;
      max-width: none;
    }
    .readme > h1:first-of-type {
      font-size: var(--heading-large);
      margin: 0 0 0.9rem;
      max-width: none;
    }
    .home-built-with { margin: 0; font-size: 0.85rem; color: var(--muted); }
    .readme {
      margin: 0 0 1.75rem;
      padding: 0;
    }
    .readme h1 { font-size: 1.55rem; margin-top: 1.4rem; max-width: none; }
    .readme h2 { font-size: 1.3rem; margin-top: 1.4rem; }
    .readme h3 { font-size: 1.1rem; margin-top: 1.2rem; }
    .readme p { margin: 0.7rem 0; }
    .readme ul, .readme ol,
    .docstring ul, .docstring ol { margin: 0.7rem 0; padding-left: 1.5rem; }
    .readme li, .docstring li { margin: 0.25rem 0; }
    .readme code {
      background: var(--panel);
      padding: 0.1em 0.32em;
      border-radius: 4px;
      font-size: 0.92em;
    }
    .readme pre,
    .docstring .code-block > pre {
      background: var(--panel);
      padding: 0.85rem 1rem;
      border-radius: 8px;
      border: 1px solid var(--line);
      overflow-x: auto;
      margin: 0.85rem 0;
    }
    .readme pre code,
    .docstring .code-block > pre code { background: none; padding: 0; font-size: 0.92em; }
    .readme .code-block,
    .docstring .code-block { position: relative; margin: 0.85rem 0; }
    .readme .code-block > pre,
    .docstring .code-block > pre { margin: 0; }
    .copy-btn {
      position: absolute;
      top: 0.4rem;
      right: 0.4rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 1.85rem;
      height: 1.85rem;
      padding: 0;
      color: var(--muted);
      background: var(--bg);
      border: 1px solid var(--line);
      border-radius: 6px;
      cursor: pointer;
      opacity: 0;
      transition: opacity 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    }
    .copy-btn svg { width: 0.95rem; height: 0.95rem; display: block; }
    .copy-btn .check-icon { display: none; }
    .copy-btn.copied .copy-icon { display: none; }
    .copy-btn.copied .check-icon { display: block; }
    .code-block:hover .copy-btn,
    .copy-btn:focus-visible { opacity: 1; }
    .copy-btn:hover { color: var(--accent-dark); border-color: var(--accent); }
    .copy-btn.copied { color: var(--accent-dark); border-color: var(--accent); opacity: 1; }
    .readme blockquote,
    .docstring blockquote {
      border-left: 3px solid var(--accent);
      padding: 0.1rem 0 0.1rem 0.9rem;
      margin: 0.85rem 0;
      color: var(--muted);
    }
    .readme hr,
    .docstring hr {
      border: 0;
      border-top: 1px solid var(--line);
      margin: 1.5rem 0;
    }
    .readme table,
    .docstring table {
      border-collapse: collapse;
      margin: 0.85rem 0;
      font-size: 0.95em;
    }
    .readme th, .readme td,
    .docstring th, .docstring td {
      border: 1px solid var(--line);
      padding: 0.4rem 0.7rem;
      text-align: left;
      vertical-align: top;
    }
    .readme thead th,
    .docstring thead th {
      background: var(--panel);
      font-weight: 600;
    }
    .inherits {
      display: block;
      margin-top: 0.25rem;
      color: var(--muted);
      font-size: 0.92rem;
      font-weight: 500;
    }
    .varargs {
      color: var(--muted);
      font-size: 0.85rem;
      font-weight: 500;
      margin-left: 0.5rem;
    }
    .varargs > code {
      background: none;
      padding: 0;
      font-size: inherit;
      color: inherit;
    }
    .superclass {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    }
    code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }
    code {
      background: #f0f1f3;
      padding: 0.05em 0.35em;
      border-radius: 4px;
      font-size: 0.92em;
    }
    pre code, .source-code code, .example-code code {
      background: none;
      padding: 0;
      border-radius: 0;
      font-size: inherit;
    }
    .api-xref { text-decoration: none; }
    .api-xref > code { color: var(--accent-dark); }
    .api-xref:hover > code { text-decoration: underline; }
    .eyebrow {
      color: var(--accent-dark);
      font-weight: 700;
      letter-spacing: 0;
      text-transform: uppercase;
      font-size: 0.78rem;
    }
    .readme-eyebrow {
      margin: 0 0 0.6rem;
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
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
      background: var(--surface);
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
      width: 280px;
      min-width: 200px;
      max-width: 600px;
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
    .side a { color: var(--ink); }
    .back {
      display: block;
      font-weight: 700;
      color: var(--field-name);
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
    .tree-chevron {
      width: 0.7em;
      height: 0.7em;
      vertical-align: -0.05em;
      margin-right: 0.55em;
      color: var(--muted);
      flex-shrink: 0;
    }
    .tree-chevron-down { color: var(--accent-dark); }
    .py-icon {
      width: 0.8em;
      height: 0.8em;
      vertical-align: -0.1em;
      margin-right: 0.55em;
      color: #3776AB;
      flex-shrink: 0;
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
    .docstring h1,
    .docstring h2,
    .docstring h3,
    .docstring h4,
    .docstring h5,
    .docstring h6 {
      max-width: none;
      margin: 1.2rem 0 0.55rem;
    }
    .docstring h1 { font-size: 1.35rem; }
    .docstring h2 { font-size: 1.25rem; }
    .docstring h3 { font-size: 1.15rem; }
    .docstring h4, .docstring h5, .docstring h6 { font-size: 1rem; }
    .structured-docstring {
      white-space: normal;
      overflow-x: visible;
    }
    .structured-docstring p {
      margin: 0 0 0.9rem;
    }
    .doc-section {
      padding: 0;
      margin-top: 1.6rem;
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
      gap: 0.4rem;
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
    .doc-field dd > :first-child { margin-top: 0; }
    .doc-field dd > :last-child  { margin-bottom: 0; }
    .doc-field dd ul, .doc-field dd ol { margin: 0.3rem 0; padding-left: 1.4rem; }
    .doc-field-name {
      color: var(--ink);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
      font-weight: 700;
    }
    .doc-field-type, .doc-return-type {
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
      background: var(--surface);
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
      background: var(--surface);
      margin: 0.6rem 0 0;
    }
    .source-block {
      margin: 0.3rem 0 0.6rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
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
    .source-block > summary:hover { background: var(--hover-bg); }
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
      background: var(--source-bg);
      border-top: 1px solid var(--line);
      font-size: 0.88rem;
      line-height: 1.55;
      color: var(--ink);
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
      color: var(--gutter-fg);
      text-align: right;
      user-select: none;
      background: var(--gutter-bg);
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
    /* VS Code Dark Modern palette */
    :root[data-theme="dark"] {
      color-scheme: dark;
      --bg: #1f1f1f;
      --ink: #d4d4d4;
      --muted: #858585;
      --line: #2b2b2b;
      --panel: #181818;
      --accent: #4FC1FF;
      --accent-dark: #569CD6;
      --field-name: #DCDCAA;
      --field-type: #4EC9B0;
      --surface: #252526;
      --hover-bg: #2d2d2d;
      --source-bg: #1e1e1e;
      --gutter-bg: #252526;
      --gutter-fg: #6e7681;
    }
    :root[data-theme="dark"] code { background: #2d2d2d; }
    :root[data-theme="dark"] pre code,
    :root[data-theme="dark"] .source-code code,
    :root[data-theme="dark"] .example-code code { background: none; }
    :root[data-theme="dark"] .doc-field-type::before,
    :root[data-theme="dark"] .doc-field-type::after { color: #9CA3AF; }
    :root[data-theme="dark"] .tok-keyword      { color: #569CD6; }
    :root[data-theme="dark"] .tok-string       { color: #CE9178; }
    :root[data-theme="dark"] .tok-number       { color: #B5CEA8; }
    :root[data-theme="dark"] .tok-comment      { color: #6A9955; font-style: italic; }
    :root[data-theme="dark"] .tok-def-name     { color: #DCDCAA; }
    :root[data-theme="dark"] .tok-class-name   { color: #4EC9B0; }
    :root[data-theme="dark"] .tok-self         { color: #569CD6; }
    :root[data-theme="dark"] .tok-builtin-type { color: #4EC9B0; }
    :root[data-theme="dark"] .tok-builtin-func { color: #DCDCAA; }
    :root[data-theme="dark"] .tok-punct        { color: #D4D4D4; }
    .theme-toggle {
      position: fixed; top: 0.85rem; right: 1rem; z-index: 50;
      display: inline-flex; align-items: center;
      width: 46px; height: 24px; padding: 0;
      background: var(--panel); border: 1px solid var(--line);
      border-radius: 999px; cursor: pointer;
    }
    .theme-toggle .sun, .theme-toggle .moon {
      position: absolute; width: 12px; height: 12px; color: var(--muted);
    }
    .theme-toggle .sun  { left: 6px; }
    .theme-toggle .moon { right: 6px; }
    .theme-toggle .thumb {
      position: absolute; top: 2px; left: 2px;
      width: 18px; height: 18px; border-radius: 50%;
      background: var(--bg); border: 1px solid var(--line);
      transform: translateX(0); transition: transform 0.15s ease;
    }
    :root[data-theme="dark"] .theme-toggle .thumb { transform: translateX(22px); }
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


_THEME_BOOT_TEMPLATE = """  <script>
    (function(){{
      try {{
        var saved = localStorage.getItem('theme');
        var theme = saved || '{default_theme}';
        if (theme === 'dark') document.documentElement.dataset.theme = 'dark';
      }} catch (e) {{}}
      window.__copyCode = function(btn){{
        var pre = btn.parentElement && btn.parentElement.querySelector('pre');
        if (!pre) return;
        var text = pre.innerText;
        var done = function(){{
          btn.classList.add('copied');
          setTimeout(function(){{ btn.classList.remove('copied'); }}, 1200);
        }};
        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(text).then(done, function(){{}});
        }} else {{
          var ta = document.createElement('textarea');
          ta.value = text; ta.setAttribute('readonly', '');
          ta.style.position = 'absolute'; ta.style.left = '-9999px';
          document.body.appendChild(ta);
          ta.select();
          try {{ document.execCommand('copy'); done(); }} catch (e) {{}}
          document.body.removeChild(ta);
        }}
      }};
      window.__toggleTheme = function(){{
        var html = document.documentElement;
        var next = html.dataset.theme === 'dark' ? 'light' : 'dark';
        if (next === 'dark') html.dataset.theme = 'dark';
        else delete html.dataset.theme;
        try {{ localStorage.setItem('theme', next); }} catch (e) {{}}
        var btn = document.querySelector('.theme-toggle');
        if (btn) btn.setAttribute('aria-pressed', String(next === 'dark'));
      }};
    }})();
  </script>"""


_THEME_TOGGLE = (
    '<button class="theme-toggle" type="button" aria-label="Toggle dark mode" '
    'aria-pressed="false" onclick="__toggleTheme()">'
    '<svg class="sun" viewBox="0 0 16 16" aria-hidden="true">'
    '<circle cx="8" cy="8" r="3" fill="none" stroke="currentColor" stroke-width="1.5"/>'
    '<path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.1 3.1l1.4 1.4M11.5 11.5l1.4 1.4'
    'M3.1 12.9l1.4-1.4M11.5 4.5l1.4-1.4" stroke="currentColor" stroke-width="1.5" '
    'stroke-linecap="round"/>'
    '</svg>'
    '<svg class="moon" viewBox="0 0 16 16" aria-hidden="true">'
    '<path d="M13 9.5A5.5 5.5 0 1 1 6.5 3a4.5 4.5 0 0 0 6.5 6.5z" '
    'fill="currentColor"/>'
    '</svg>'
    '<span class="thumb"></span>'
    '</button>'
)


def page(title: str, body: str, *, layout: str = "split", default_theme: str = "light") -> str:
    """Wrap page content in shared HTML, CSS, and metadata.

    Args:
        title: Text used for the ``<title>`` element.
        body: Pre-rendered HTML inserted inside ``<body>``.
        layout: Body class controlling the page's top-level layout
            (``"split"`` or ``"single"``).
        default_theme: Theme used when the visitor has no saved preference
            (``"light"`` or ``"dark"``).

    Returns:
        A complete HTML document as a string, ready to be written to disk.
    """

    theme = default_theme if default_theme in {"light", "dark"} else "light"
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{escape(title)}</title>\n"
        f"{_THEME_BOOT_TEMPLATE.format(default_theme=theme)}\n"
        f"{_MATHJAX_HEAD}\n"
        f"  <style>{_CSS}  </style>\n"
        "</head>\n"
        f'<body class="{escape(layout)}">\n'
        f"{_THEME_TOGGLE}\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )
