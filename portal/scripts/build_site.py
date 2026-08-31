"""
build_site.py — Generate the static HTML site from the Morigny Portal
SQLite DB. Adapted from IslamicateOccultPortal's build_site.py, updated
for TurkaGame's newer card/body markdown convention (that portal's
version used plain summary/full_description text fields; this one
renders real markdown and resolves [[slug]] wiki-links).

Output goes to portal/docs/ (not portal/site/) because that's the path
.github/workflows/deploy.yml publishes to GitHub Pages, matching
MedievalMagicDB's proven, already-deployed workflow.

NOTE ON IMAGES: this catalogs captions/metadata only; it does not host
image bytes. MORIGNYGAME's own assets_manifest.js is the actual image
pipeline for anything rights-cleared and in use.
"""

import html
import json
import re
import sqlite3
from pathlib import Path

import markdown as md

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "morigny.db"
SITE_DIR = BASE_DIR / "docs"

# (table, dirname, singular entity_type used in scholarly_refs)
ENTITY_TABLES = [
    ("figures", "figures", "figure"),
    ("concepts", "concepts", "concept"),
    ("texts", "texts", "text"),
    ("institutions", "institutions", "institution"),
    ("arguments", "arguments", "argument"),
]

NAV_ITEMS = [
    ("Home", "index.html"),
    ("Figures", "figures/index.html"),
    ("Concepts", "concepts/index.html"),
    ("Texts", "texts/index.html"),
    ("Timeline", "timeline/index.html"),
    ("Institutions", "institutions/index.html"),
    ("Arguments", "arguments/index.html"),
    ("Scholarship", "scholarship.html"),
    ("About", "about.html"),
]

CSS = """
:root {
  --ink: #2e2419; --parchment: #ece2cd; --vermilion: #a63a22; --rule: #cbb98f;
  --card-bg: #f7f0e0; --graphite: #55565a;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--parchment); color: var(--ink);
  font-family: Georgia, "Iowan Old Style", "Palatino Linotype", serif; line-height: 1.62; }
header { background: var(--ink); color: var(--parchment); padding: 1rem 1.5rem; }
header .brand { font-size: 1.35rem; letter-spacing: 0.03em; font-variant: small-caps; }
header .brand a { color: var(--parchment); text-decoration: none; }
nav { display: flex; flex-wrap: wrap; gap: 0.9rem; margin-top: 0.5rem; font-size: 0.88rem; }
nav a { color: #e3d3ad; text-decoration: none; }
nav a:hover { color: #fff; text-decoration: underline; }
main { max-width: 54rem; margin: 0 auto; padding: 2rem 1.5rem 5rem; }
h1 { font-size: 1.95rem; margin-bottom: 0.2rem; color: var(--ink); }
h2 { color: var(--vermilion); font-size: 1.05rem; text-transform: uppercase;
  letter-spacing: 0.07em; margin-top: 2.3rem; border-bottom: 1px solid var(--rule);
  padding-bottom: 0.3rem; }
h3 { font-size: 1.1rem; margin: 1.3rem 0 0.4rem; }
.subtitle { font-style: italic; color: var(--graphite); margin: 0.2rem 0 1.2rem; }
.card { background: var(--card-bg); border: 1px solid var(--rule); border-radius: 4px;
  padding: 1rem 1.2rem; margin-bottom: 1rem; }
.card h3 { margin: 0 0 0.35rem; font-size: 1.08rem; }
.card h3 a { color: var(--ink); text-decoration: none; }
.card h3 a:hover { color: var(--vermilion); }
.meta { font-size: 0.8rem; color: var(--graphite); margin-bottom: 0.4rem; }
.badge { display: inline-block; font-size: 0.7rem; text-transform: uppercase;
  letter-spacing: 0.05em; padding: 0.08rem 0.5rem; border: 1px solid var(--rule);
  border-radius: 999px; color: var(--graphite); margin-right: 0.3rem; }
.badge.high { border-color: #4a6a3a; color: #3e5a30; }
.badge.low { border-color: #a06060; color: #904f4f; }
table { width: 100%; border-collapse: collapse; font-size: 0.92rem; margin: 0.8rem 0; }
th, td { text-align: left; padding: 0.45rem 0.6rem; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { color: var(--vermilion); text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.05em; }
a { color: var(--vermilion); }
a.entlink { color: var(--ink); border-bottom: 1px dotted var(--rule); text-decoration: none; }
a.entlink:hover { color: var(--vermilion); }
a.entlink.missing { color: #904f4f; border-bottom-style: dashed; }
.tags { font-size: 0.8rem; color: var(--graphite); }
.notice { background: #efe3c2; border-left: 3px solid var(--vermilion); padding: 0.7rem 1rem;
  margin: 1rem 0; font-size: 0.9rem; }
.timeline-item { border-left: 2px solid var(--rule); padding: 0 0 1.1rem 1rem; margin-left: 0.3rem; position: relative; }
.timeline-item::before { content: ""; position: absolute; left: -5px; top: 0.3rem; width: 8px; height: 8px;
  border-radius: 50%; background: var(--vermilion); }
.timeline-year { font-weight: bold; font-variant: small-caps; letter-spacing: 0.04em; color: var(--vermilion); }
footer { margin-top: 4rem; font-size: 0.85rem; color: var(--graphite); text-align: center; }
blockquote { border-left: 3px solid var(--rule); margin: 0.8rem 0; padding: 0.2rem 1rem; color: #4a3f2e; font-style: italic; }
"""

MD = md.Markdown(extensions=["extra"])


def build_slug_index(conn) -> dict[str, tuple[str, str]]:
    """slug -> (dirname, display name) across every entity type, for [[slug]] resolution."""
    index: dict[str, tuple[str, str]] = {}
    for table, dirname, _etype in ENTITY_TABLES:
        name_col = "title" if table in ("texts", "arguments") else "name"
        for slug, name in conn.execute(f"SELECT slug, {name_col} FROM {table}"):
            index[slug] = (dirname, name)
    for slug, title in conn.execute("SELECT slug, title FROM timeline_events"):
        index[slug] = ("timeline", title)
    return index


def resolve_links(text: str, slug_index: dict[str, tuple[str, str]], depth: int) -> str:
    """[[slug]] -> <a class=entlink href=...>Display Name</a>, or a flagged
    missing-link span if the slug isn't seeded yet (never a silent 404)."""
    prefix = "../" * depth

    def sub(m):
        slug = m.group(1)
        if slug in slug_index:
            dirname, name = slug_index[slug]
            href = f"{prefix}{dirname}/{slug}.html" if dirname != "timeline" else f"{prefix}timeline/index.html#{slug}"
            return f'<a class="entlink" href="{href}">{html.escape(name)}</a>'
        return f'<span class="entlink missing" title="entry not yet written">{html.escape(slug)}</span>'

    return re.sub(r"\[\[([a-z0-9\-]+)\]\]", sub, text)


def render_md(text: str | None, slug_index: dict[str, tuple[str, str]], depth: int) -> str:
    if not text:
        return ""
    linked = resolve_links(text, slug_index, depth)
    MD.reset()
    return MD.convert(linked)


def page_shell(title: str, body: str, depth: int = 0) -> str:
    prefix = "../" * depth
    nav_html = " · ".join(f'<a href="{prefix}{href}">{label}</a>' for label, href in NAV_ITEMS)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — John of Morigny Portal</title>
<link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
<header>
  <div class="brand"><a href="{prefix}index.html">The John of Morigny Portal</a></div>
  <nav>{nav_html}</nav>
</header>
<main>
{body}
</main>
<footer>A research portal, not a source of religious or occult instruction. See <a href="{prefix}about.html">About</a> for scope and provenance conventions.</footer>
</body>
</html>
"""


def confidence_badge(c: str | None) -> str:
    cls = {"HIGH": "high", "LOW": "low"}.get(c or "", "")
    return f'<span class="badge {cls}">{html.escape(c or "MEDIUM")}</span>'


def jarr(v):
    if not v:
        return []
    try:
        return json.loads(v)
    except (TypeError, json.JSONDecodeError):
        return []


def refs_for(conn, entity_type: str, slug: str) -> str:
    rows = conn.execute("""
        SELECT sr.page_ref, sr.quote_or_note, b.author, b.title, b.year
        FROM scholarly_refs sr JOIN bibliography b ON b.source_id = sr.bib_source_id
        WHERE sr.entity_type=? AND sr.entity_slug=?
        ORDER BY b.author
    """, (entity_type, slug)).fetchall()
    if not rows:
        return ""
    items = []
    for page, note, author, title, year in rows:
        cite = f"{html.escape(author)}, <em>{html.escape(title)}</em>{f' ({year})' if year else ''}"
        page_s = f", p.{html.escape(page)}" if page else ""
        note_s = f" — {html.escape(note)}" if note else ""
        items.append(f"<li>{cite}{page_s}{note_s}</li>")
    return f"<h2>Sources</h2><ul>{''.join(items)}</ul>"


def build_index(conn):
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["figures", "concepts", "texts", "institutions", "timeline_events", "arguments", "bibliography"]}
    body = f"""
<h1>John of Morigny</h1>
<p class="subtitle">A research portal on the Benedictine monk, visionary, and rewriter of condemned magic (fl. c. 1300&ndash;1323), grounded in Claire Fanger's scholarship</p>

<p>John of Morigny was a fourteenth-century Benedictine monk who experimented with the
condemned ritual art called the <em>ars notoria</em>, was denounced for it, and
responded not by abandoning the practice but by <strong>rewriting it</strong> &mdash;
composing the <em>Liber florum celestis doctrine</em> ("Flowers of Heavenly Teaching"),
a purified system he claimed was authorized by visions of the Virgin Mary. Condemned and
burned at Paris in 1323, his book nonetheless survived in over twenty manuscripts and was
rediscovered by modern scholarship only in the 1990s.</p>

<div class="notice">Phase 1 of this portal: {counts['figures']} figures, {counts['concepts']} concepts,
{counts['texts']} texts, {counts['timeline_events']} timeline events, {counts['arguments']} historiographical
arguments, {counts['bibliography']} document summaries &mdash; all grounded in a direct, page-cited reading of
Claire Fanger's <em>Rewriting Magic</em> and <em>Invoking Angels</em>, and the wider medieval-magic scholarship
around them. See <a href="about.html">About</a> for what's verified and what's still on the research queue.</div>

<h2>Browse</h2>
<div class="card"><h3><a href="figures/index.html">Figures</a></h3><div class="meta">{counts['figures']} people &mdash; John himself, his witnesses, and the modern scholars who study him</div></div>
<div class="card"><h3><a href="concepts/index.html">Concepts</a></h3><div class="meta">{counts['concepts']} ritual-magic, theological, and manuscript terms</div></div>
<div class="card"><h3><a href="texts/index.html">Texts</a></h3><div class="meta">{counts['texts']} primary sources &mdash; John's own writing and the chronicle notices about him</div></div>
<div class="card"><h3><a href="timeline/index.html">Timeline</a></h3><div class="meta">{counts['timeline_events']} dated events, from his formation to his modern rediscovery</div></div>
<div class="card"><h3><a href="institutions/index.html">Institutions</a></h3><div class="meta">{counts['institutions']} abbeys, universities, and the bodies that condemned him</div></div>
<div class="card"><h3><a href="arguments/index.html">Arguments</a></h3><div class="meta">{counts['arguments']} historiographical claims &mdash; what scholars argue, and why it matters</div></div>
<div class="card"><h3><a href="scholarship.html">Scholarship</a></h3><div class="meta">{counts['bibliography']} document summaries: the secondary literature, actually read and described</div></div>
"""
    (SITE_DIR / "index.html").write_text(page_shell("Home", body, depth=0), encoding="utf-8")


def build_entity_section(conn, slug_index, table, dirname, etype, title, meta_fn):
    out_dir = SITE_DIR / dirname
    out_dir.mkdir(parents=True, exist_ok=True)
    order_col = "title" if table in ("texts", "arguments") else "name"
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order_col}").fetchall()
    col_names = [d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 1").description]

    cards = []
    for row in rows:
        r = dict(zip(col_names, row))
        name = r.get("name") or r.get("title")
        card_html = render_md(r.get("card"), slug_index, depth=1)
        cards.append(f'<div class="card"><h3><a href="{r["slug"]}.html">{html.escape(name)}</a></h3>'
                      f'<div class="meta">{confidence_badge(r.get("confidence"))}{meta_fn(r)}</div>'
                      f'{card_html}</div>')
    (out_dir / "index.html").write_text(
        page_shell(title, f"<h1>{title}</h1>\n" + "\n".join(cards), depth=1), encoding="utf-8")

    for row in rows:
        r = dict(zip(col_names, row))
        name = r.get("name") or r.get("title")
        body_html = render_md(r.get("body") or r.get("card"), slug_index, depth=1)
        tags = jarr(r.get("tags"))
        tag_html = f'<p class="tags">{", ".join(html.escape(t) for t in tags)}</p>' if tags else ""
        lit = jarr(r.get("literature"))
        lit_html = ("<h2>Literature</h2><ul>" + "".join(f"<li>{html.escape(x)}</li>" for x in lit) + "</ul>") if lit else ""
        page_body = f"""
<h1>{html.escape(name)}</h1>
<div class="meta">{confidence_badge(r.get('confidence'))} {meta_fn(r)}</div>
{body_html}
{tag_html}
{refs_for(conn, etype, r['slug'])}
{lit_html}
<p><a href="index.html">&larr; back to {title}</a></p>
"""
        (out_dir / f"{r['slug']}.html").write_text(page_shell(name, page_body, depth=1), encoding="utf-8")


def build_timeline(conn, slug_index):
    out_dir = SITE_DIR / "timeline"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = conn.execute("SELECT * FROM timeline_events ORDER BY year_start").fetchall()
    col_names = [d[0] for d in conn.execute("SELECT * FROM timeline_events LIMIT 1").description]
    items = []
    for row in rows:
        r = dict(zip(col_names, row))
        year = r.get("year_start")
        year_label = f"{year}" if year else "?"
        if r.get("year_end") and r["year_end"] != year:
            year_label += f"&ndash;{r['year_end']}"
        prec = r.get("date_precision") or ""
        card_html = render_md(r.get("card"), slug_index, depth=1)
        body_html = render_md(r.get("body"), slug_index, depth=1) if r.get("body") else ""
        items.append(f'<div class="timeline-item" id="{r["slug"]}">'
                      f'<div class="timeline-year">{year_label} <span class="badge">{html.escape(prec)}</span> '
                      f'<span class="badge">{html.escape(r.get("grounding") or "")}</span></div>'
                      f'<h3>{html.escape(r["title"])}</h3>{card_html}{body_html}</div>')
    body = "<h1>Timeline</h1>\n<p>Dated events in John of Morigny's life and the transmission, condemnation, and rediscovery of his book.</p>\n" + "\n".join(items)
    (out_dir / "index.html").write_text(page_shell("Timeline", body, depth=1), encoding="utf-8")


def build_scholarship(conn, slug_index):
    rows = conn.execute("SELECT * FROM bibliography ORDER BY relevance, author").fetchall()
    col_names = [d[0] for d in conn.execute("SELECT * FROM bibliography LIMIT 1").description]
    sections = []
    for row in rows:
        r = dict(zip(col_names, row))
        year = r.get("year") or ""
        pub = r.get("journal") or r.get("publisher") or ""
        card_html = render_md(r.get("card"), slug_index, depth=0)
        body_html = render_md(r.get("body"), slug_index, depth=0) if r.get("body") else ""
        access = f"<p class=\"tags\">Access: {html.escape(r['access_note'])}</p>" if r.get("access_note") else ""
        sections.append(f"""<div class="card">
<h3 id="{r['source_id']}">{html.escape(r['author'])}, <em>{html.escape(r['title'])}</em>{f' ({year})' if year else ''}</h3>
<div class="meta"><span class="badge">{html.escape(r.get('relevance') or '')}</span> {html.escape(pub)}</div>
{card_html}
{body_html}
{access}
{refs_for(conn, 'text', r['source_id'])}
</div>""")
    body = f"""
<h1>Scholarship</h1>
<p>{len(rows)} secondary sources, each read and summarized directly &mdash; not paraphrased from an abstract.
See <a href="about.html">About</a> for the provenance discipline this portal follows.</p>
{''.join(sections)}
"""
    (SITE_DIR / "scholarship.html").write_text(page_shell("Scholarship", body, depth=0), encoding="utf-8")


def build_about():
    body = """
<h1>About</h1>
<p>A research portal on John of Morigny (fl. c. 1300&ndash;1323), the Benedictine monk,
visionary, and rewriter of the condemned <em>ars notoria</em>, built alongside
<a href="https://github.com/t3dy/MORIGNYGAME">MORIGNYGAME</a> (a narrative game on the
same subject) but standing independently as scholarship &mdash; the portal does not
depend on the game, and the game's fiction is never blended into these entries.</p>

<h2>Architecture</h2>
<p>SQLite source of truth (<code>portal/db/morigny.db</code>), a Python static-site
generator, vanilla HTML/CSS &mdash; no frameworks. Follows the same pattern as this
workspace's other knowledge portals (TurkaGame's own portal, IslamicateOccultPortal,
MedievalMagicDB, witcherportal).</p>

<h2>Provenance conventions</h2>
<ul>
<li><strong>Every content row</strong> carries <code>source_method</code>,
<code>review_status</code>, and <code>confidence</code>. <code>confidence: HIGH</code>
means a direct, page-locatable passage was actually read &mdash; never inferred, never
guessed.</li>
<li><strong>No assertion without attribution.</strong> Non-obvious claims carry a
<code>scholarly_refs</code> row with a real page number, shown as "Sources" on the
entry itself.</li>
<li><strong>The corpus is not the site.</strong> <code>portal/corpus/sources/*.md</code>
holds full-text conversions of copyrighted scholarly works for research reference only
&mdash; gitignored, never published here. The public artifact is the cited entry, not
the source text behind it.</li>
<li><strong>Modern scholars are historical figures too.</strong> Claire Fanger, Nicholas
Watson, Richard Kieckhefer, and others who study John appear in the Figures section
with real biographical treatment, not just as citation strings.</li>
<li><strong>What isn't confirmed says so.</strong> Several sources central to John's
biography &mdash; the Fanger&ndash;Watson critical edition of the <em>Liber florum</em>,
Julien V&eacute;ron&egrave;se's standalone monographs, Nicholas Watson's 1998
<em>Conjuring Spirits</em> essay, Barbara Newman's 2005 <em>Speculum</em> article &mdash;
were not available to this portal's author at build time. Claims resting on them are
marked <code>confidence: LOW</code> or left out rather than guessed.</li>
</ul>

<h2>Status</h2>
<p>Phase 1 build. See the notice on the <a href="index.html">home page</a> for current
coverage.</p>
"""
    (SITE_DIR / "about.html").write_text(page_shell("About", body, depth=0), encoding="utf-8")


def main():
    conn = sqlite3.connect(DB_PATH)
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "style.css").write_text(CSS, encoding="utf-8")
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")

    slug_index = build_slug_index(conn)

    build_index(conn)
    build_entity_section(conn, slug_index, "figures", "figures", "figure", "Figures",
        lambda r: f"{html.escape(r.get('role') or '')} &middot; {html.escape(r.get('lifespan') or '')}")
    build_entity_section(conn, slug_index, "concepts", "concepts", "concept", "Concepts",
        lambda r: f"{html.escape(r.get('category') or '')}")
    build_entity_section(conn, slug_index, "texts", "texts", "text", "Texts",
        lambda r: f"{html.escape(r.get('text_type') or '')} &middot; {html.escape(r.get('date_or_period') or '')}")
    build_entity_section(conn, slug_index, "institutions", "institutions", "institution", "Institutions",
        lambda r: f"{html.escape(r.get('institution_type') or '')} &middot; {html.escape(r.get('period') or '')}")
    build_entity_section(conn, slug_index, "arguments", "arguments", "argument", "Arguments",
        lambda r: f"{html.escape(r.get('scope') or '')}")
    build_timeline(conn, slug_index)
    build_scholarship(conn, slug_index)
    build_about()

    conn.close()
    print(f"Site built: {SITE_DIR}")


if __name__ == "__main__":
    main()
