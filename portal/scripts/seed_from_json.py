"""
seed_from_json.py — Ingest hand-authored entries from seed.json into the
database. Adapted from TurkaGame's version, completed with ingestion for
timeline_events, arguments, scholarly_refs, images, and essays (that
draft covers figures/concepts/institutions/texts/arguments/bibliography
only; this portal's schema needs all ten content tables fed).

Idempotent: INSERT OR REPLACE keyed on each table's unique slug/id, so
re-running after editing seed.json is always safe.

Usage:
    python portal/scripts/seed_from_json.py --seed-file portal/data/seed.json
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "morigny.db"
SEED_DEFAULT = BASE_DIR / "data" / "seed.json"


def load_seed(path: Path) -> dict[str, Any]:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def j(v):
    return json.dumps(v if v is not None else [])


def ingest_figures(conn, rows):
    for r in rows:
        conn.execute("""
            INSERT OR REPLACE INTO figures (
                slug, name, name_full, name_variants, role, lifespan,
                birth_year, death_year, region, relation_to_john,
                card, body, key_works, affiliations, literature,
                tags, source_method, review_status, confidence
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r['slug'], r['name'], r.get('name_full'), j(r.get('name_variants')),
            r['role'], r.get('lifespan'), r.get('birth_year'), r.get('death_year'),
            r.get('region'), r.get('relation_to_john'), r['card'], r.get('body'),
            j(r.get('key_works')), j(r.get('affiliations')), j(r.get('literature')),
            j(r.get('tags')), r.get('source_method', 'CORPUS_SYNTHESIS'),
            r.get('review_status', 'DRAFT'), r.get('confidence', 'MEDIUM'),
        ))
    conn.commit()
    return len(rows)


def ingest_concepts(conn, rows):
    for r in rows:
        conn.execute("""
            INSERT OR REPLACE INTO concepts (
                slug, name, name_latin, literal_meaning, category, card, body,
                hierarchy_note, related_concepts, literature, tags,
                source_method, review_status, confidence
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r['slug'], r['name'], r.get('name_latin'), r.get('literal_meaning'),
            r['category'], r['card'], r.get('body'), r.get('hierarchy_note'),
            j(r.get('related_concepts')), j(r.get('literature')), j(r.get('tags')),
            r.get('source_method', 'CORPUS_SYNTHESIS'), r.get('review_status', 'DRAFT'),
            r.get('confidence', 'MEDIUM'),
        ))
    conn.commit()
    return len(rows)


def ingest_texts(conn, rows):
    for r in rows:
        conn.execute("""
            INSERT OR REPLACE INTO texts (
                slug, title, title_latin, title_translated, author_figure_slug,
                text_type, language, date_or_period, card, body, known_manuscripts,
                modern_editions, literature, tags, source_method, review_status, confidence
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r['slug'], r['title'], r.get('title_latin'), r.get('title_translated'),
            r.get('author_figure_slug'), r['text_type'], r.get('language'),
            r.get('date_or_period'), r['card'], r.get('body'),
            j(r.get('known_manuscripts')), j(r.get('modern_editions')),
            j(r.get('literature')), j(r.get('tags')),
            r.get('source_method', 'CORPUS_SYNTHESIS'), r.get('review_status', 'DRAFT'),
            r.get('confidence', 'MEDIUM'),
        ))
    conn.commit()
    return len(rows)


def ingest_institutions(conn, rows):
    for r in rows:
        conn.execute("""
            INSERT OR REPLACE INTO institutions (
                slug, name, institution_type, period, region, card, body,
                literature, tags, source_method, review_status, confidence
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r['slug'], r['name'], r.get('institution_type'), r.get('period'),
            r.get('region'), r['card'], r.get('body'), j(r.get('literature')),
            j(r.get('tags')), r.get('source_method', 'CORPUS_SYNTHESIS'),
            r.get('review_status', 'DRAFT'), r.get('confidence', 'MEDIUM'),
        ))
    conn.commit()
    return len(rows)


def ingest_timeline(conn, rows):
    for r in rows:
        conn.execute("""
            INSERT OR REPLACE INTO timeline_events (
                slug, title, year_start, year_end, date_precision, place,
                category, grounding, card, body, figures_involved, texts_involved,
                tags, source_method, review_status, confidence
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r['slug'], r['title'], r.get('year_start'), r.get('year_end'),
            r.get('date_precision', 'CIRCA'), r.get('place'), r['category'],
            r.get('grounding', 'ATTESTED'), r['card'], r.get('body'),
            j(r.get('figures_involved')), j(r.get('texts_involved')), j(r.get('tags')),
            r.get('source_method', 'CORPUS_SYNTHESIS'), r.get('review_status', 'DRAFT'),
            r.get('confidence', 'MEDIUM'),
        ))
    conn.commit()
    return len(rows)


def ingest_arguments(conn, rows):
    for r in rows:
        conn.execute("""
            INSERT OR REPLACE INTO arguments (
                slug, title, proponent_slug, claim, against, evidence, stakes,
                scope, contested, contested_note, card, body, related_concepts,
                literature, tags, source_method, review_status, confidence
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r['slug'], r['title'], r.get('proponent_slug'), r.get('claim'),
            r.get('against'), r.get('evidence'), r.get('stakes'), r.get('scope'),
            1 if r.get('contested') else 0, r.get('contested_note'),
            r['card'], r.get('body'), j(r.get('related_concepts')),
            j(r.get('literature')), j(r.get('tags')),
            r.get('source_method', 'CORPUS_SYNTHESIS'), r.get('review_status', 'DRAFT'),
            r.get('confidence', 'MEDIUM'),
        ))
    conn.commit()
    return len(rows)


def ingest_bibliography(conn, rows):
    for r in rows:
        conn.execute("""
            INSERT OR REPLACE INTO bibliography (
                source_id, author, title, year, publisher, journal, pub_type,
                relevance, card, body, key_arguments, corpus_file,
                conversion_status, online_url, access_note
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r['source_id'], r['author'], r['title'], r.get('year'), r.get('publisher'),
            r.get('journal'), r['pub_type'], r['relevance'], r.get('card'), r.get('body'),
            j(r.get('key_arguments')), r.get('corpus_file'),
            r.get('conversion_status', 'CONVERTED'), r.get('online_url'), r.get('access_note'),
        ))
    conn.commit()
    return len(rows)


def ingest_scholarly_refs(conn, rows):
    conn.execute("DELETE FROM scholarly_refs")  # fully regenerated each run from seed.json
    for r in rows:
        conn.execute("""
            INSERT INTO scholarly_refs (entity_type, entity_slug, bib_source_id, page_ref, quote_or_note)
            VALUES (?,?,?,?,?)
        """, (r['entity_type'], r['entity_slug'], r['bib_source_id'], r.get('page_ref'), r.get('quote_or_note')))
    conn.commit()
    return len(rows)


def ingest_images(conn, rows):
    for r in rows:
        conn.execute("""
            INSERT OR REPLACE INTO images (
                slug, caption, depicts, image_type, institution, shelfmark, folio,
                date_or_period, source_url, rights_status, source_bib_id, source_page,
                notes, tags, source_method, review_status, confidence
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            r['slug'], r['caption'], r.get('depicts'), r.get('image_type'),
            r.get('institution'), r.get('shelfmark'), r.get('folio'),
            r.get('date_or_period'), r.get('source_url'), r.get('rights_status', 'UNDETERMINED'),
            r.get('source_bib_id'), r.get('source_page'), r.get('notes'), j(r.get('tags')),
            r.get('source_method', 'PDF_EXTRACTION'), r.get('review_status', 'DRAFT'),
            r.get('confidence', 'MEDIUM'),
        ))
    conn.commit()
    return len(rows)


def ingest_essays(conn, rows):
    for r in rows:
        conn.execute("""
            INSERT OR REPLACE INTO essays (
                slug, title, subtitle, card, body, related_entities, literature,
                source_method, review_status, confidence
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            r['slug'], r['title'], r.get('subtitle'), r.get('card'), r['body'],
            j(r.get('related_entities')), j(r.get('literature')),
            r.get('source_method', 'CORPUS_SYNTHESIS'), r.get('review_status', 'DRAFT'),
            r.get('confidence', 'MEDIUM'),
        ))
    conn.commit()
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed-file', type=Path, default=SEED_DEFAULT)
    args = ap.parse_args()

    if not args.seed_file.exists():
        print(f"Seed file not found: {args.seed_file}")
        return 1
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run: python portal/scripts/init_db.py")
        return 1

    print(f"Loading seed from {args.seed_file}...")
    seed = load_seed(args.seed_file)
    conn = sqlite3.connect(DB_PATH)
    try:
        counts = {
            'figures': ingest_figures(conn, seed.get('figures', [])),
            'concepts': ingest_concepts(conn, seed.get('concepts', [])),
            'texts': ingest_texts(conn, seed.get('texts', [])),
            'institutions': ingest_institutions(conn, seed.get('institutions', [])),
            'timeline_events': ingest_timeline(conn, seed.get('timeline_events', [])),
            'arguments': ingest_arguments(conn, seed.get('arguments', [])),
            'bibliography': ingest_bibliography(conn, seed.get('bibliography', [])),
            'scholarly_refs': ingest_scholarly_refs(conn, seed.get('scholarly_refs', [])),
            'images': ingest_images(conn, seed.get('images', [])),
            'essays': ingest_essays(conn, seed.get('essays', [])),
        }
        for table, n in counts.items():
            print(f"  {table}: {n} ingested")

        # Orphan-link check: every scholarly_refs row must point at a real bibliography row.
        orphans = conn.execute("""
            SELECT sr.entity_type, sr.entity_slug, sr.bib_source_id FROM scholarly_refs sr
            LEFT JOIN bibliography b ON b.source_id = sr.bib_source_id
            WHERE b.source_id IS NULL
        """).fetchall()
        if orphans:
            print(f"\nWARNING: {len(orphans)} scholarly_refs point at missing bibliography entries:")
            for et, es, bid in orphans:
                print(f"  {et}:{es} -> {bid}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
