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
    """Minimal inline markdown: `code`, **bold**, *italic*, ![alt](src), [text](url)."""
    text = html.escape(text, quote=False)
    # set code spans aside so their content is not formatted
    codes: list[str] = []

    def stash(m: re.Match) -> str:
        codes.append(f"<code>{m.group(1)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)", r'<img src="\2" alt="\1">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


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

        # horizontal rule
        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            blocks.append("<hr>")
            i += 1
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


def load_categories() -> list:
    return json.loads((CONTENT / "categories.json").read_text(encoding="utf-8"))


def load_posts() -> list[dict]:
    posts = []
    for path in sorted((CONTENT / "blog").glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        # the post template already shows the title, drop a leading "# Title"
        body = re.sub(r"^\s*#\s+[^\n]*\n", "", body, count=1)
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


def time_tag(d: datetime, lang: str) -> str:
    return f'<time datetime="{d:%Y-%m-%d}">{format_date(d, lang)}</time>'


# ---------------------------------------------------------------- build
def build() -> None:
    site = load_site()
    lang = site.get("lang", "en")
    projects = load_projects()
    posts = load_posts()
    categories = load_categories()
    year = str(datetime.now().year)

    # clean output, copy assets
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(ASSETS, OUT / "assets")

    footer_links = "".join(
        f'<a href="{url}">{label}</a>' for label, url in site.get("links", {}).items()
    )

    def shell(page_title: str, content: str, root_prefix: str, description: str) -> str:
        title = html.escape(f"{page_title} | {site['name']}")
        return render_template(
            "base.html",
            site_name=site["name"],
            page_title=title,
            description=html.escape(description),
            lang=lang,
            content=content,
            home_link=root_prefix + "/",
            blog_link=root_prefix + "/blog/",
            css_path=root_prefix + "/assets/style.css",
            footer_links=footer_links,
            year=year,
        )

    def post_item(p: dict, href: str, heading: str) -> str:
        return (
            '<article class="post-item">'
            f'<{heading}><a href="{href}">{inline(p["title"])}</a></{heading}>'
            f'{time_tag(p["date"], lang)}'
            f'<p>{inline(p["excerpt"])}</p></article>'
        )

    posts_by_category = {
        c["slug"]: [p for p in posts if c["slug"] in p["tags"]] for c in categories
    }

    # ---- home
    project_cards = "".join(
        '<article class="project">'
        f'<div class="project-head"><h3><a href="{p["url"]}">{p["name"]}</a></h3>'
        f'<span class="project-status">{p.get("status", "")}</span></div>'
        f'<p>{p["description"]}</p></article>'
        for p in projects
    )
    latest_html = "".join(post_item(p, f'./blog/{p["slug"]}/', "h3") for p in posts[:3])
    # only interests that already have posts, with their count
    category_buttons = "".join(
        f'<a class="category-btn" href="./blog/category/{c["slug"]}/">{c["label"]}'
        f'<span class="category-count">{len(posts_by_category[c["slug"]])}</span></a>'
        for c in categories
        if posts_by_category[c["slug"]]
    )
    home_content = render_template(
        "home.html",
        name=site["name"],
        tagline=site.get("tagline", ""),
        about_html=md_to_html(site.get("about", "")),
        categories_html=category_buttons,
        projects_html=project_cards,
        latest_posts_html=latest_html,
        blog_link="./blog/",
    )
    (OUT / "index.html").write_text(
        shell("Accueil", home_content, ".", site.get("tagline", "")), encoding="utf-8"
    )

    # ---- blog index
    posts_html = "".join(post_item(p, f'./{p["slug"]}/', "h2") for p in posts)
    blog_content = render_template("blog.html", posts_html=posts_html)
    blog_dir = OUT / "blog"
    blog_dir.mkdir()
    (blog_dir / "index.html").write_text(
        shell("Blog", blog_content, "..", f"Tous les articles de {site['name']}."),
        encoding="utf-8",
    )

    # ---- posts
    category_slugs = {c["slug"] for c in categories}
    for p in posts:
        tags = "".join(
            f'<a class="tag" href="../category/{t}/">{t}</a>'
            if t in category_slugs
            else f'<span class="tag">{t}</span>'
            for t in p["tags"]
        )
        post_content = render_template(
            "post.html",
            post_title=html.escape(p["title"]),
            post_date=time_tag(p["date"], lang),
            post_tags=tags,
            post_html=md_to_html(p["body"]),
            blog_link="../",
        )
        post_dir = blog_dir / p["slug"]
        post_dir.mkdir()
        (post_dir / "index.html").write_text(
            shell(p["title"], post_content, "../..", p["excerpt"]), encoding="utf-8"
        )

    # ---- category pages (blog/category/<slug>/ is three levels deep)
    for c in categories:
        cat_posts = posts_by_category[c["slug"]]
        if cat_posts:
            cat_posts_html = "".join(post_item(p, f'../../{p["slug"]}/', "h2") for p in cat_posts)
        else:
            cat_posts_html = '<p class="muted">Aucun article pour l\'instant.</p>'
        cat_content = render_template(
            "category.html", category_label=c["label"], posts_html=cat_posts_html
        )
        cat_dir = blog_dir / "category" / c["slug"]
        cat_dir.mkdir(parents=True)
        (cat_dir / "index.html").write_text(
            shell(c["label"], cat_content, "../../..", f"Articles : {c['label']}."),
            encoding="utf-8",
        )

    print(f"Site built in {OUT} ({len(posts)} post(s), {len(projects)} project(s)).")


if __name__ == "__main__":
    build()
