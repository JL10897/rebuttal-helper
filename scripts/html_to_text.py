"""Turn a saved review page (e.g. an OpenReview forum saved as HTML) into plain text.

Usage:
    python3 html_to_text.py page.html reviews.txt

Drops scripts and styles, keeps block structure as line breaks, collapses blank lines.
The output is the single source that quoted excerpts are checked against.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

BLOCK = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "pre",
         "blockquote", "section", "article", "header", "footer", "dt", "dd", "hr"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
        elif tag in BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip = max(0, self.skip - 1)
        elif tag in BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, dst = map(Path, sys.argv[1:])
    p = Text()
    p.feed(src.read_text(encoding="utf-8", errors="replace"))
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in "".join(p.out).splitlines()]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"
    if len(text) < 200:
        raise SystemExit(f"{src}: only {len(text)} characters of text; the page may be rendered by JavaScript. "
                         "Save it from the browser after it fully loads, or copy the page text into reviews.txt.")
    dst.write_text(text, encoding="utf-8")
    print(f"wrote {dst}: {len(text.splitlines())} lines")


if __name__ == "__main__":
    main()
