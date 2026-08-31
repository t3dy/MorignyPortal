"""
init_db.py — Create the John of Morigny Portal SQLite schema.

Adapted directly from TurkaGame's portal schema (portal/scripts/init_db.py
there), which itself follows WitcherPortal / AtalantaClaudiens /
ALCHEMYTIMELINEMAP conventions. Kept identical in shape and provenance
discipline; adapted in vocabulary for this corpus (French/Latin monastic
and ritual-magic material, not Islamicate lettrism):

  * `figures.role` enum swaps in MONK/VISIONARY/CANON_LAWYER/CONDEMNER
    for this corpus's actual cast, keeps MODERN_SCHOLAR — "modern
    scholars are historical figures too" (STYLE_ENTRIES.md).
  * `concepts.category` enum swaps in RITUAL_MAGIC_TERM/THEOLOGICAL/
    MANUSCRIPT_TERM/LITURGICAL/HISTORIOGRAPHIC for OCCULT_SCIENCE etc.
  * `texts.text_type` enum swaps PRIMARY_VISIONARY_AUTOBIOGRAPHY/
    PRIMARY_PRAYER_CYCLE/PRIMARY_RITUAL_FIGURES/PRIMARY_CHRONICLE for
    the Islamicate treatise/grimoire/epistle vocabulary.
  * `arguments` kept as a first-class entity — TurkaGame's own
    innovation, and it fits this corpus too: Fanger's own
    historiographical arguments (censorship doesn't work; rewriting as
    devotion) are load-bearing claims, not incidental facts.
  * No game material — this portal is purely scholarly. MORIGNYGAME
    (the sibling narrative-game project) cites portal entries by slug
    from its own docs; it does not write into this database.

Provenance discipline is unchanged: every content row carries
source_method, review_status, confidence. confidence: HIGH means a
direct, page-locatable passage was actually read — see
portal/docs/STYLE_ENTRIES.md.

Idempotent. Load data with seed_from_json.py afterward.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "morigny.db"

SCHEMA = """
-- ============================================================
-- John of Morigny Portal schema v1
-- ============================================================

-- Historical people: the monk, his witnesses, his condemners, and
-- (role MODERN_SCHOLAR) the authors of the secondary literature itself.
CREATE TABLE IF NOT EXISTS figures (
    id                  INTEGER PRIMARY KEY,
    slug                TEXT UNIQUE NOT NULL,
    name                TEXT NOT NULL,
    name_full           TEXT,
    name_variants       TEXT,                  -- JSON array (e.g. Bridget/Burgeta/Gurgeta)
    role                TEXT CHECK(role IN ('MONK','VISIONARY','WITNESS','CANON_LAWYER','CONDEMNER','PATRON','CHRONICLER','MODERN_SCHOLAR','TEXTUAL_FIGURE')),
    lifespan            TEXT,                  -- "fl. c. 1300-1323", "b. 1955"
    birth_year          INTEGER,
    death_year          INTEGER,
    region              TEXT,
    relation_to_john    TEXT,                  -- sister / fellow witness / condemner / modern editor / none
    card                TEXT NOT NULL,         -- 60-150 word index card (markdown)
    body                TEXT,                  -- 1,200-2,200 word encyclopedia page (markdown)
    key_works           TEXT,                  -- JSON array of text slugs
    affiliations        TEXT,                  -- JSON array of institution slugs
    literature          TEXT,                  -- JSON array of citation strings
    tags                TEXT,
    source_method       TEXT DEFAULT 'CORPUS_SYNTHESIS',
    review_status       TEXT DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','REVIEWED','VERIFIED')),
    confidence          TEXT DEFAULT 'MEDIUM' CHECK(confidence IN ('HIGH','MEDIUM','LOW'))
);

-- The dictionary of concepts: ritual-magic and theological vocabulary,
-- manuscript/textual terms, historiographic categories.
CREATE TABLE IF NOT EXISTS concepts (
    id                  INTEGER PRIMARY KEY,
    slug                TEXT UNIQUE NOT NULL,
    name                TEXT NOT NULL,
    name_latin          TEXT,                  -- the Latin term
    literal_meaning     TEXT,
    category            TEXT CHECK(category IN ('RITUAL_MAGIC_TERM','THEOLOGICAL','MANUSCRIPT_TERM','LITURGICAL','HISTORIOGRAPHIC','INSTITUTIONAL')),
    card                TEXT NOT NULL,         -- the dictionary definition, 60-150 words
    body                TEXT,                  -- 800-1,800 word encyclopedia page
    hierarchy_note      TEXT,
    related_concepts    TEXT,                  -- JSON array of concept slugs
    literature          TEXT,
    tags                TEXT,
    source_method       TEXT DEFAULT 'CORPUS_SYNTHESIS',
    review_status       TEXT DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','REVIEWED','VERIFIED')),
    confidence          TEXT DEFAULT 'MEDIUM' CHECK(confidence IN ('HIGH','MEDIUM','LOW'))
);

-- Primary sources: John's own texts, the chronicle notices, the ars
-- notoria tradition he inherited.
CREATE TABLE IF NOT EXISTS texts (
    id                   INTEGER PRIMARY KEY,
    slug                 TEXT UNIQUE NOT NULL,
    title                TEXT NOT NULL,
    title_latin          TEXT,
    title_translated     TEXT,
    author_figure_slug   TEXT,                 -- soft FK -> figures.slug
    text_type            TEXT CHECK(text_type IN ('PRIMARY_VISIONARY_AUTOBIOGRAPHY','PRIMARY_PRAYER_CYCLE','PRIMARY_RITUAL_FIGURES','PRIMARY_CHRONICLE','PRIMARY_RITUAL_TEXT','MODERN_EDITION')),
    language             TEXT,
    date_or_period        TEXT,
    card                 TEXT NOT NULL,
    body                 TEXT,
    known_manuscripts    TEXT,
    modern_editions      TEXT,
    literature           TEXT,
    tags                 TEXT,
    source_method        TEXT DEFAULT 'CORPUS_SYNTHESIS',
    review_status        TEXT DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','REVIEWED','VERIFIED')),
    confidence            TEXT DEFAULT 'MEDIUM' CHECK(confidence IN ('HIGH','MEDIUM','LOW'))
);

-- Abbeys, universities, condemning bodies, modern scholarly societies.
CREATE TABLE IF NOT EXISTS institutions (
    id                  INTEGER PRIMARY KEY,
    slug                TEXT UNIQUE NOT NULL,
    name                TEXT NOT NULL,
    institution_type    TEXT CHECK(institution_type IN ('ABBEY','UNIVERSITY','CONDEMNING_BODY','DIOCESE','MODERN_SOCIETY','PUBLISHER')),
    period              TEXT,
    region              TEXT,
    card                TEXT NOT NULL,
    body                TEXT,
    literature          TEXT,
    tags                TEXT,
    source_method       TEXT DEFAULT 'CORPUS_SYNTHESIS',
    review_status       TEXT DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','REVIEWED','VERIFIED')),
    confidence          TEXT DEFAULT 'MEDIUM' CHECK(confidence IN ('HIGH','MEDIUM','LOW'))
);

-- The biographical timeline. `grounding` follows TurkaGame's convention.
CREATE TABLE IF NOT EXISTS timeline_events (
    id               INTEGER PRIMARY KEY,
    slug             TEXT UNIQUE NOT NULL,
    title            TEXT NOT NULL,
    year_start       INTEGER,
    year_end         INTEGER,
    date_precision   TEXT CHECK(date_precision IN ('EXACT','YEAR','CIRCA','RANGE','DISPUTED')),
    place            TEXT,
    category         TEXT CHECK(category IN ('LIFE','TEXTS','CONDEMNATION','TRANSMISSION','RECEPTION','CONTEXT')),
    grounding        TEXT DEFAULT 'ATTESTED' CHECK(grounding IN ('ATTESTED','COMPARATIVE','CONTEXT')),
    card             TEXT NOT NULL,
    body             TEXT,
    figures_involved TEXT,                     -- JSON array of figure slugs
    texts_involved   TEXT,                     -- JSON array of text slugs
    tags             TEXT,
    source_method    TEXT DEFAULT 'CORPUS_SYNTHESIS',
    review_status    TEXT DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','REVIEWED','VERIFIED')),
    confidence       TEXT DEFAULT 'MEDIUM' CHECK(confidence IN ('HIGH','MEDIUM','LOW'))
);

-- Historiographical arguments as first-class entities.
CREATE TABLE IF NOT EXISTS arguments (
    id                  INTEGER PRIMARY KEY,
    slug                TEXT UNIQUE NOT NULL,
    title               TEXT NOT NULL,
    proponent_slug      TEXT,                  -- soft FK -> figures.slug (MODERN_SCHOLAR)
    claim               TEXT NOT NULL,
    against             TEXT,
    evidence            TEXT,
    stakes              TEXT,
    scope               TEXT CHECK(scope IN ('JOHN_OF_MORIGNY','ARS_NOTORIA','MONASTIC_MAGIC','PERIODIZATION','METHOD')),
    contested           INTEGER DEFAULT 0,
    contested_note      TEXT,
    card                TEXT NOT NULL,
    body                TEXT,
    related_concepts    TEXT,
    literature          TEXT,
    tags                TEXT,
    source_method       TEXT DEFAULT 'CORPUS_SYNTHESIS',
    review_status       TEXT DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','REVIEWED','VERIFIED')),
    confidence          TEXT DEFAULT 'MEDIUM' CHECK(confidence IN ('HIGH','MEDIUM','LOW'))
);

-- Scholarly secondary sources, with real document summaries.
CREATE TABLE IF NOT EXISTS bibliography (
    id                INTEGER PRIMARY KEY,
    source_id         TEXT UNIQUE NOT NULL,
    author            TEXT NOT NULL,
    title             TEXT NOT NULL,
    year              INTEGER,
    publisher         TEXT,
    journal           TEXT,
    pub_type          TEXT CHECK(pub_type IN ('monograph','article','chapter','review','edited_volume','primary_source_edition','website')),
    relevance         TEXT CHECK(relevance IN ('PRIMARY','DIRECT','CONTEXTUAL')),
    card              TEXT,
    body              TEXT,
    key_arguments     TEXT,                    -- JSON array of argument slugs
    corpus_file       TEXT,
    conversion_status TEXT DEFAULT 'CONVERTED' CHECK(conversion_status IN ('CONVERTED','NOT_CONVERTED','EXTERNAL')),
    online_url        TEXT,
    access_note       TEXT
);

-- Polymorphic link: any entity -> bibliography entry, with page reference.
CREATE TABLE IF NOT EXISTS scholarly_refs (
    id              INTEGER PRIMARY KEY,
    entity_type     TEXT NOT NULL CHECK(entity_type IN ('figure','concept','text','institution','event','argument','image')),
    entity_slug     TEXT NOT NULL,
    bib_source_id   TEXT NOT NULL REFERENCES bibliography(source_id),
    page_ref        TEXT,
    quote_or_note   TEXT
);

-- Image catalog: cross-references MORIGNYGAME's own sourced leaves
-- (assets_manifest.js) rather than duplicating a sourcing effort.
CREATE TABLE IF NOT EXISTS images (
    id                INTEGER PRIMARY KEY,
    slug              TEXT UNIQUE NOT NULL,
    caption           TEXT NOT NULL,
    depicts           TEXT,
    image_type        TEXT CHECK(image_type IN ('MANUSCRIPT_PAGE','DIAGRAM','PORTRAIT','ARCHITECTURE','OBJECT','OTHER')),
    institution       TEXT,
    shelfmark         TEXT,
    folio             TEXT,
    date_or_period    TEXT,
    source_url        TEXT,
    rights_status     TEXT DEFAULT 'UNDETERMINED' CHECK(rights_status IN ('UNDETERMINED','PUBLIC_DOMAIN','CLEARED','DO_NOT_USE')),
    source_bib_id     TEXT,
    source_page       INTEGER,
    notes             TEXT,
    tags              TEXT,
    source_method     TEXT DEFAULT 'PDF_EXTRACTION',
    review_status     TEXT DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','REVIEWED','VERIFIED')),
    confidence        TEXT DEFAULT 'MEDIUM' CHECK(confidence IN ('HIGH','MEDIUM','LOW'))
);

-- Long-form synthesis threading multiple entities together.
CREATE TABLE IF NOT EXISTS essays (
    id               INTEGER PRIMARY KEY,
    slug             TEXT UNIQUE NOT NULL,
    title            TEXT NOT NULL,
    subtitle         TEXT,
    card             TEXT,
    body             TEXT NOT NULL,
    related_entities TEXT,
    literature       TEXT,
    source_method    TEXT DEFAULT 'CORPUS_SYNTHESIS',
    review_status    TEXT DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','REVIEWED','VERIFIED')),
    confidence       TEXT DEFAULT 'MEDIUM' CHECK(confidence IN ('HIGH','MEDIUM','LOW'))
);

CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT DEFAULT (datetime('now')),
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_refs_entity ON scholarly_refs(entity_type, entity_slug);
CREATE INDEX IF NOT EXISTS idx_refs_bib    ON scholarly_refs(bib_source_id);
CREATE INDEX IF NOT EXISTS idx_events_year ON timeline_events(year_start);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES (1, 'John of Morigny Portal v1: figures, concepts, texts, institutions, timeline_events, arguments, bibliography, scholarly_refs, images, essays. Adapted from TurkaGame portal schema.');
"""

EXPECTED = {
    'figures', 'concepts', 'texts', 'institutions', 'timeline_events',
    'arguments', 'bibliography', 'scholarly_refs', 'images', 'essays',
    'schema_version',
}


def main() -> int:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()

    print(f"Database: {DB_PATH}")
    print(f"Tables ({len(tables)}): {', '.join(sorted(tables))}")
    missing = EXPECTED - tables
    if missing:
        print(f"ERROR: missing tables: {missing}")
        return 1
    print("Schema v1 ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
