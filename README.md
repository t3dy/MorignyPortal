# John of Morigny Portal

A scholarly knowledge portal on **John of Morigny** (fl. c. 1300–1323), the Benedictine
monk who practiced the condemned ritual art known as the *ars notoria*, was denounced
for it twice, and responded not by abandoning ritual practice but by rewriting it —
composing the *Liber florum celestis doctrine*, a purified system claiming direct
authorization from visions of the Virgin Mary. Burned at Paris in 1323, his book
nonetheless survived in over twenty manuscripts and was rediscovered by modern
scholarship only in the 1990s.

Built alongside [MORIGNYGAME](https://github.com/t3dy/MORIGNYGAME) (a narrative game
on the same subject) but standing independently as scholarship — the portal does not
depend on the game, and the game's fiction is never blended into these entries.

Grounded in a direct, page-cited reading of Claire Fanger's *Rewriting Magic* (2015)
and *Invoking Angels* (2012), plus the wider medieval-magic scholarship (Kieckhefer,
Page, Klaassen, Láng) that supplies the field's context.

**Live site: [t3dy.github.io/MorignyPortal](https://t3dy.github.io/MorignyPortal/)**

## Quick Start

```bash
# Create the SQLite schema
python portal/scripts/init_db.py

# Ingest hand-authored entries from seed.json
python portal/scripts/seed_from_json.py --seed-file portal/data/seed.json

# Generate the static site (outputs to portal/docs/, served by GitHub Pages)
python portal/scripts/build_site.py
```

All three scripts are idempotent — safe to re-run after editing `seed.json`.

### Search the corpus from the command line

The corpus (18 full-text scholarly sources, ~11MB, gitignored — see
`portal/corpus/sources/README.md`) is searched by targeted retrieval, never read
end-to-end:

```bash
# List every source in the corpus
python portal/scripts/mine_corpus.py sources

# Which sources discuss a term?
python portal/scripts/mine_corpus.py rank "ars notoria" "notae"

# What do they say about a term, in context?
python portal/scripts/mine_corpus.py kwic "Barking Dogs" --max 10

# Read a passage: find it, read around it
python portal/scripts/mine_corpus.py read fanger-rewriting-magic-2015 --around "1323" --chars 2000

# List the real page numbers embedded in a source
python portal/scripts/mine_corpus.py pages fanger-rewriting-magic-2015
```

Every hit includes a real page number (embedded in the corpus conversion as
`## Page N` markers) — a hit becomes a citation immediately.

## Architecture

Same pattern as this workspace's other knowledge portals (TurkaGame's own portal,
IslamicateOccultPortal, MedievalMagicDB, witcherportal): SQLite source of truth, a
Python static-site generator, vanilla HTML/CSS — no frameworks.

```
portal/
├── docs/STYLE_ENTRIES.md    card/body word-count targets, provenance discipline
├── corpus/sources/*.md       18 gitignored full-text scholarly sources
├── data/
│   ├── seed.json              hand-authored entries (tracked)
│   └── corpus_manifest.json   per-source metadata (tracked)
├── db/morigny.db              SQLite, built from seed.json (gitignored)
├── scripts/
│   ├── mine_corpus.py         rank / kwic / read / pages — the research tool
│   ├── init_db.py             schema (11 tables)
│   ├── seed_from_json.py      JSON -> DB, idempotent
│   └── build_site.py          DB -> static HTML
└── docs/ (output)             built site — GitHub Pages serves this
```

### Entities

- **Figures** — people: John himself, his named witnesses (Bridget/Burgeta, John of
  Fontainejean), and the modern scholars who study him (Fanger, Watson, Kieckhefer,
  Véronèse) — treated as historical actors in their own right, not just citation
  strings.
- **Concepts** — ritual-magic, theological, and manuscript terminology: *ars notoria*,
  *notae*, the Old/New Compilation, "plundering the Egyptian treasure," the "Barking
  Dogs."
- **Texts** — primary sources: the *Liber florum celestis doctrine* itself, the
  *Grandes Chroniques* 1323 notice.
- **Institutions** — the Abbey of Morigny, the University of Orléans, Rice University,
  the Societas Magica.
- **Timeline** — dated events in John's life and the transmission, condemnation, and
  rediscovery of his book.
- **Arguments** — historiographical claims, first-class: "book condemnation is not
  effective censorship," "rewriting is devotion, not retraction," the historiography
  of erasure.
- **Bibliography** — real document summaries of the secondary scholarship, not just
  citation strings.

### Provenance discipline

**Every non-obvious claim carries a `scholarly_refs` row with a real page number.**
This enforces:

1. **You've actually read it.** No paraphrasing from abstracts or other summaries.
2. **The portal is citable.** A reader can trace any claim back to the exact page.
3. **Confidence is honest.** `confidence: HIGH` only for claims verified by directly
   reading the passage. `MEDIUM` for synthesis across multiple passages. `LOW` for
   plausible-but-unverified — flagged, not hidden.

See `portal/docs/STYLE_ENTRIES.md` for card/body word-count targets and worked
examples, and `about.html` on the built site for the specific sources this portal's
author did **not** have access to (the Fanger–Watson critical edition, Véronèse's
standalone monographs, Watson's 1998 *Conjuring Spirits* essay, Newman's 2005
*Speculum* article, *RB 1980*) — claims resting on those are marked `LOW` or left out
rather than guessed.

## Status

**Phase 1 (current):** 7 figures, 5 concepts, 2 primary texts, 4 institutions, 11
timeline events, 3 historiographical arguments, 6 document summaries — all grounded in
a direct, page-cited reading of *Rewriting Magic* and Véronèse's *ars notoria* chapter
in *Invoking Angels*.

**Deferred, named rather than dropped:** Sylvie Barnay and other secondary modern
scholars as full figure entries; a full institution-by-institution treatment; the
`essays` table (schema-ready, empty this phase); anything resting only on the five
confirmed-unavailable sources listed above.

## Deployment

The site is built locally (`build_site.py`) and `portal/docs/` is committed to the
repo. On every push to `main`, GitHub Actions (`.github/workflows/deploy.yml`)
publishes that committed `portal/docs/` folder via `actions/upload-pages-artifact` +
`actions/deploy-pages` — no build step runs in CI. After editing `seed.json`, re-run
the three pipeline scripts locally and commit the regenerated `portal/docs/` output
along with the source changes.

---

Sibling project: [MORIGNYGAME](https://github.com/t3dy/MORIGNYGAME) — the narrative
game this portal's scholarship underwrites.
