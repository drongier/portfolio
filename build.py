#!/usr/bin/env python3
"""Zero-dependency static site generator.

Usage:
    python3 build.py

Reads content/ and templates/, writes the generated site to public/.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import string
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
OUT = ROOT / "public"

MONTHS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


# ---------------------------------------------------------------- markdown
def inline(text: str) -> str:
    """Minimal inline markdown: `code`, **bold**, *italic*, [text](url)."""
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    return text


def md_to_html(md: str) -> str:
    """Minimal block markdown: headings, paragraphs, lists, code, quotes."""
    lines = md.splitlines()
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        # fenced code block
        if line.startswith("```"):
            buf: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            blocks.append(f"<pre><code>{html.escape(chr(10).join(buf))}</code></pre>")
            continue

        # headings
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            blocks.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # blockquote
        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i][1:].strip())
                i += 1
            blocks.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>")
            continue

        # lists (flat only)
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            ordered = m.group(2)[0].isdigit()
            items = []
            while i < len(lines):
                m2 = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i])
                if not m2:
                    break
                items.append(f"<li>{inline(m2.group(3))}</li>")
                i += 1
            tag = "ol" if ordered else "ul"
            blocks.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue

        # paragraph
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "```", ">")):
            if re.match(r"^(\s*)([-*]|\d+\.)\s+", lines[i]):
                break
            buf.append(lines[i])
            i += 1
        blocks.append(f"<p>{inline(' '.join(buf))}</p>")

    return "\n".join(blocks)


# ---------------------------------------------------------------- front matter
def parse_front_matter(text: str) -> tuple[dict, str]:
    """Parse --- delimited front matter, then return (meta, body)."""
    meta = {}
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        end = 1
        while end < len(lines) and lines[end].strip() != "---":
            end += 1
        for line in lines[1:end]:
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = "\n".join(lines[end + 1:]) if end < len(lines) else ""
        return meta, body
    return meta, text


def plain_excerpt(md: str, limit: int = 160) -> str:
    """First words of a markdown body, stripped of syntax, for list pages."""
    text = re.sub(r"```.*?```", " ", md, flags=re.S)
    text = re.sub(r"[#>*_`\[\]()]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return (text[:limit] + "…") if len(text) > limit else text


# ---------------------------------------------------------------- loading
def load_site() -> dict:
    return json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))


def load_projects() -> list:
    return json.loads((CONTENT / "projects.json").read_text(encoding="utf-8"))


def load_posts() -> list[dict]:
    posts = []
    for path in sorted((CONTENT / "blog").glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        date = datetime.strptime(meta.get("date", "1970-01-01"), "%Y-%m-%d")
        posts.append(
            {
                "slug": path.stem,
                "title": meta.get("title", path.stem),
                "date": date,
                "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
                "excerpt": meta.get("excerpt") or plain_excerpt(body),
                "body": body,
            }
        )
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ---------------------------------------------------------------- rendering
def render_template(template_name: str, **vars) -> str:
    tpl = string.Template((TEMPLATES / template_name).read_text(encoding="utf-8"))
    return tpl.substitute(**vars)


def format_date(d: datetime, lang: str) -> str:
    if lang == "fr":
        return f"{d.day} {MONTHS_FR[d.month - 1]} {d.year}"
    return d.strftime("%b %d, %Y")


# ---------------------------------------------------------------- build
def build() -> None:
    site = load_site()
    lang = site.get("lang", "en")
    projects = load_projects()
    posts = load_posts()
    year = str(datetime.now().year)

    # clean output, copy assets
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(ASSETS, OUT / "assets")

    footer_links = "".join(
        f'<a href="{url}">{label}</a>' for label, url in site.get("links", {}).items()
    )

    def shell(page_title: str, content: str, root_prefix: str) -> str:
        return render_template(
            "base.html",
            site_name=site["name"],
            page_title=page_title,
            lang=lang,
            content=content,
            home_link=root_prefix + "/",
            blog_link=root_prefix + "/blog/",
            css_path=root_prefix + "/assets/style.css",
            footer_links=footer_links,
            year=year,
        )

    # ---- home
    project_cards = "".join(
        '<article class="project">'
        f'<div class="project-head"><h3><a href="{p["url"]}">{p["name"]}</a></h3>'
        f'<span class="project-status">{p.get("status", "")}</span></div>'
        f'<p>{p["description"]}</p></article>'
        for p in projects
    )
    latest_html = "".join(
        '<article class="post-item">'
        f'<h3><a href="./blog/{p["slug"]}/">{inline(p["title"])}</a></h3>'
        f'<time>{format_date(p["date"], lang)}</time>'
        f'<p>{inline(p["excerpt"])}</p></article>'
        for p in posts[:3]
    )
    home_content = render_template(
        "home.html",
        name=site["name"],
        tagline=site.get("tagline", ""),
        about_html=md_to_html(site.get("about", "")),
        projects_html=project_cards,
        latest_posts_html=latest_html,
        blog_link="./blog/",
    )
    (OUT / "index.html").write_text(shell("Accueil", home_content, "."), encoding="utf-8")

    # ---- blog index
    posts_html = "".join(
        '<article class="post-item">'
        f'<h2><a href="./{p["slug"]}/">{inline(p["title"])}</a></h2>'
        f'<time>{format_date(p["date"], lang)}</time>'
        f'<p>{inline(p["excerpt"])}</p></article>'
        for p in posts
    )
    blog_content = render_template("blog.html", posts_html=posts_html)
    blog_dir = OUT / "blog"
    blog_dir.mkdir()
    (blog_dir / "index.html").write_text(shell("Blog", blog_content, ".."), encoding="utf-8")

    # ---- posts
    for p in posts:
        tags = "".join(f'<span class="tag">{t}</span>' for t in p["tags"])
        post_content = render_template(
            "post.html",
            post_title=p["title"],
            post_date=format_date(p["date"], lang),
            post_tags=tags,
            post_html=md_to_html(p["body"]),
            blog_link="../",
        )
        post_dir = blog_dir / p["slug"]
        post_dir.mkdir()
        (post_dir / "index.html").write_text(
            shell(p["title"], post_content, "../.."), encoding="utf-8"
        )

    print(f"Site built in {OUT} ({len(posts)} post(s), {len(projects)} project(s)).")


if __name__ == "__main__":
    build()
