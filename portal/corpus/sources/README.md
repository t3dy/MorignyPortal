# Corpus sources

This directory holds page-numbered markdown conversions of copyrighted
scholarly monographs and articles (Fanger, Kieckhefer, Page, Klaassen,
Láng, and others — see `../../data/corpus_manifest.json` for the full
list with editions and provenance). **These files are gitignored and
never committed or published.** They are local research material only,
read via `../../scripts/mine_corpus.py` to write cited, page-referenced
entries in `../../data/seed.json` — the entries are the public artifact;
the corpus is the private research library behind them.

If you're setting this repository up fresh, you will need to supply
your own copies of the sources listed in `corpus_manifest.json`.
