"""
mine_corpus.py — the corpus research tool, adapted from TurkaGame's portal
(same rank -> kwic -> read -> cite workflow; see that project's version for
the original Islamicate-lettrism edition of this tool).

This corpus is French/English monastic and magical-manuscript scholarship,
not Arabic/Persian, so two things differ from the TurkaGame original:

  * Page markers are `## Page N` (the literal page number is IN the
    marker, from this project's own PDF->markdown conversion), not a
    bare separator string counted sequentially. `page_of()` looks the
    real number up directly instead of inferring an index.
  * No diacritic-folding for Arabic/Persian transliteration variants;
    folds French/Latin accents instead (Étampes/Etampes, Bâtard/Batard)
    so a search catches both spellings.

The corpus is gitignored (full texts of copyrighted scholarly works, kept
as local research material only) — see corpus/sources/README.md.

Subcommands
-----------
  sources                 List the corpus with sizes.
  rank TERM [TERM...]     Per-source hit counts. Which files are worth opening.
  kwic TERM               Keyword-in-context concordance with page numbers.
  read SLUG               Read a region: --page N, --around TERM, --chars N.
  pages SLUG              Page/character map of one source.
  near TERM1 TERM2        Passages where two terms co-occur within a window.

Usage:
    python portal/scripts/mine_corpus.py rank "John of Morigny" "ars notoria"
    python portal/scripts/mine_corpus.py kwic "verba ignota" --max 25
    python portal/scripts/mine_corpus.py read fanger-rewriting-magic-2015 --around "Bridget" --chars 3000
    python portal/scripts/mine_corpus.py near "John" "1323" --window 600
"""

import argparse
import io
import re
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent.parent
CORPUS_DIR = BASE_DIR / "corpus" / "sources"

PAGE_RE = re.compile(r"^## Page (\d+)\s*$", re.MULTILINE)

FOLD = str.maketrans({
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "à": "a", "â": "a", "ä": "a",
    "î": "i", "ï": "i",
    "ô": "o", "ö": "o",
    "û": "u", "ù": "u", "ü": "u",
    "ç": "c", "ñ": "n",
    "ʿ": "", "ʾ": "",
    "'": "", "'": "", "'": "",
})


def fold(s: str) -> str:
    return s.translate(FOLD).lower()


def corpus_files(only: list[str] | None = None) -> list[Path]:
    files = sorted(CORPUS_DIR.glob("*.md"))
    if only:
        wanted = {o.lower() for o in only}
        files = [f for f in files if any(w in f.stem.lower() for w in wanted)]
    return files


class Source:
    """One converted source, with a real page index built once on load."""

    def __init__(self, path: Path):
        self.slug = path.stem
        self.text = path.read_text(encoding="utf-8", errors="replace")
        self.folded = fold(self.text)
        # (char position, page number) for every "## Page N" marker.
        self.page_marks = [(m.start(), int(m.group(1))) for m in PAGE_RE.finditer(self.text)]
        if not self.page_marks:
            self.page_marks = [(0, 1)]

    def page_of(self, pos: int) -> int:
        page = self.page_marks[0][1]
        for mark_pos, mark_page in self.page_marks:
            if mark_pos > pos:
                break
            page = mark_page
        return page

    def n_pages(self) -> int:
        return len(self.page_marks)

    def finditer(self, term: str):
        ft = fold(term)
        start = 0
        while True:
            i = self.folded.find(ft, start)
            if i < 0:
                return
            yield i
            start = i + 1

    def count(self, term: str) -> int:
        return self.folded.count(fold(term))


def clean(snippet: str) -> str:
    s = re.sub(r"## Page \d+", " ", snippet)
    s = re.sub(r"\s+", " ", s).strip()
    return s.encode('utf-8', errors='replace').decode('utf-8', errors='replace')


# ------------------------------------------------------------------ commands

def cmd_sources(args) -> int:
    files = corpus_files(args.only)
    for f in files:
        kb = f.stat().st_size // 1024
        print(f"{kb:>6}K  {f.stem}")
    total_mb = sum(f.stat().st_size for f in files) / (1024 * 1024)
    print(f"\n{len(files)} sources, {total_mb:.1f} MB total.")
    return 0


def cmd_rank(args) -> int:
    results = []
    for f in corpus_files(args.only):
        src = Source(f)
        counts = {t: src.count(t) for t in args.terms}
        total = sum(counts.values())
        if total:
            results.append((total, src.slug, counts, src.n_pages()))
    results.sort(reverse=True)
    if not results:
        print(f"No hits for {args.terms}")
        return 0
    width = max(len(r[1]) for r in results)
    print(f"{'total':>6}  {'source':<{width}}  pages  breakdown")
    for total, slug, counts, pages in results[: args.max]:
        parts = " ".join(f"{t}={c}" for t, c in counts.items() if c)
        print(f"{total:>6}  {slug:<{width}}  {pages:>5}  {parts}")
    print(f"\n{len(results)} sources with hits; {sum(r[0] for r in results)} occurrences total.")
    return 0


def cmd_kwic(args) -> int:
    shown = 0
    for f in corpus_files(args.only):
        src = Source(f)
        hits = list(src.finditer(args.term))
        if not hits:
            continue
        print(f"\n=== {src.slug} ({len(hits)} hits) ===")
        for pos in hits[: args.per_source]:
            lo = max(0, pos - args.width)
            hi = min(len(src.text), pos + len(args.term) + args.width)
            print(f"  p{src.page_of(pos):<4} {clean(src.text[lo:hi])}")
            shown += 1
            if shown >= args.max:
                print(f"\n[stopped at --max {args.max}]")
                return 0
    if not shown:
        print(f"No hits for {args.term!r}")
    return 0


def cmd_near(args) -> int:
    shown = 0
    for f in corpus_files(args.only):
        src = Source(f)
        a_hits = list(src.finditer(args.term1))
        if not a_hits:
            continue
        b_folded = fold(args.term2)
        printed_header = False
        for pos in a_hits:
            lo = max(0, pos - args.window)
            hi = min(len(src.folded), pos + args.window)
            if b_folded not in src.folded[lo:hi]:
                continue
            if not printed_header:
                print(f"\n=== {src.slug} ===")
                printed_header = True
            print(f"  p{src.page_of(pos):<4} {clean(src.text[lo:hi])}\n")
            shown += 1
            if shown >= args.max:
                print(f"[stopped at --max {args.max}]")
                return 0
    if not shown:
        print(f"No co-occurrence of {args.term1!r} and {args.term2!r} within {args.window} chars.")
    return 0


def cmd_read(args) -> int:
    matches = corpus_files([args.slug])
    if not matches:
        print(f"No source matching {args.slug!r}. Try: mine_corpus.py sources")
        return 1
    src = Source(matches[0])

    if args.around:
        hits = list(src.finditer(args.around))
        if not hits:
            print(f"{args.around!r} not found in {src.slug}")
            return 1
        pos = hits[min(args.nth, len(hits) - 1)]
        lo = max(0, pos - args.chars // 3)
        hi = min(len(src.text), pos + (args.chars * 2) // 3)
        print(f"# {src.slug} — around {args.around!r} (hit {args.nth + 1}/{len(hits)}, p{src.page_of(pos)})\n")
    elif args.page:
        candidates = [p for p, n in src.page_marks if n == args.page]
        lo = candidates[0] if candidates else 0
        hi = min(len(src.text), lo + args.chars)
        print(f"# {src.slug} — from p{args.page}\n")
    else:
        lo, hi = 0, min(len(src.text), args.chars)
        print(f"# {src.slug} — from the start ({src.n_pages()} pages, {len(src.text):,} chars)\n")

    print(src.text[lo:hi])
    return 0


def cmd_pages(args) -> int:
    matches = corpus_files([args.slug])
    if not matches:
        print(f"No source matching {args.slug!r}")
        return 1
    src = Source(matches[0])
    print(f"{src.slug}: {src.n_pages()} marked pages, {len(src.text):,} chars")
    for pos, num in src.page_marks[: args.max]:
        head = clean(src.text[pos:pos + 90])
        print(f"  p{num:<4} @{pos:<9} {head[:80]}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def only_arg(parser):
        parser.add_argument("--only", nargs="*", default=None,
                             help="restrict to sources whose slug contains these substrings")

    p = sub.add_parser("sources", help="list the corpus")
    only_arg(p)
    p.set_defaults(func=cmd_sources)

    p = sub.add_parser("rank", help="per-source hit counts")
    p.add_argument("terms", nargs="+")
    p.add_argument("--max", type=int, default=25)
    only_arg(p)
    p.set_defaults(func=cmd_rank)

    p = sub.add_parser("kwic", help="keyword-in-context concordance")
    p.add_argument("term")
    p.add_argument("--width", type=int, default=180)
    p.add_argument("--max", type=int, default=40)
    p.add_argument("--per-source", type=int, default=8)
    only_arg(p)
    p.set_defaults(func=cmd_kwic)

    p = sub.add_parser("near", help="two terms co-occurring in a window")
    p.add_argument("term1")
    p.add_argument("term2")
    p.add_argument("--window", type=int, default=500)
    p.add_argument("--max", type=int, default=20)
    only_arg(p)
    p.set_defaults(func=cmd_near)

    p = sub.add_parser("read", help="read a region of one source")
    p.add_argument("slug")
    p.add_argument("--page", type=int)
    p.add_argument("--around")
    p.add_argument("--nth", type=int, default=0)
    p.add_argument("--chars", type=int, default=3000)
    p.set_defaults(func=cmd_read)

    p = sub.add_parser("pages", help="page map of one source")
    p.add_argument("slug")
    p.add_argument("--max", type=int, default=200)
    p.set_defaults(func=cmd_pages)

    args = ap.parse_args()
    if not CORPUS_DIR.exists() or not any(CORPUS_DIR.glob("*.md")):
        print("Corpus empty. Place converted .md sources in portal/corpus/sources/")
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
