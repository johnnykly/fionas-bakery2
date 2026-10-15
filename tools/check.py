"""Sanity checks on the built site: run after tools/build.py.

Fails on: em/en dashes in copy, exclamation marks in headings, pages without
exactly one <h1>, images without alt/width/height, missing title/description,
duplicate titles, and broken internal links.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "_site")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.stack = []
        self.text = []
        self.heads = []
        self.imgs = []
        self.links = []
        self.title = ""
        self.desc = ""
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
        if tag == "h1":
            self.h1 += 1
        if tag in ("h1", "h2", "h3", "h4", "title"):
            self.stack.append([tag, ""])
        if tag == "img":
            self.imgs.append(a)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "meta" and a.get("name") == "description":
            self.desc = a.get("content", "")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
        if self.stack and self.stack[-1][0] == tag:
            t, txt = self.stack.pop()
            if t == "title":
                self.title = txt.strip()
            else:
                self.heads.append(txt.strip())

    def handle_data(self, data):
        if self.skip:
            return
        self.text.append(data)
        for s in self.stack:
            s[1] += data


def main():
    problems, titles = [], {}
    pages = sorted(SITE.rglob("*.html"))
    for f in pages:
        rel = f.relative_to(SITE)
        p = Page()
        p.feed(f.read_text(encoding="utf-8"))
        text = "".join(p.text)
        if re.search("[—–]", text):
            problems.append(f"{rel}: em/en dash in copy")
        for h in p.heads:
            if "!" in h:
                problems.append(f"{rel}: exclamation mark in heading '{h}'")
        if p.h1 != 1:
            problems.append(f"{rel}: {p.h1} h1 elements")
        if not p.title or not p.desc:
            problems.append(f"{rel}: missing title or description")
        if p.title in titles:
            problems.append(f"{rel}: duplicate title with {titles[p.title]}")
        titles[p.title] = rel
        for img in p.imgs:
            if not img.get("alt") or not img.get("width") or not img.get("height"):
                problems.append(f"{rel}: image without alt/width/height {img.get('src')}")
        for href in p.links:
            if href.startswith(("http", "mailto:", "tel:", "#")):
                continue
            path = href.split("#")[0].split("?")[0]
            target = SITE / path.lstrip("/")
            if path.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                problems.append(f"{rel}: broken link {href}")
    for line in problems:
        print("FAIL", line)
    print(f"checked {len(pages)} pages, {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
