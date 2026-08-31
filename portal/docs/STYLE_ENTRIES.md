# John of Morigny Portal — Entry Style Guide

Adapted from TurkaGame's portal style guide (`C:\Dev\TurkaGame\portal\docs\STYLE_ENTRIES.md`),
same card/page system, same provenance discipline, worked examples
rewritten for this corpus.

Every entity (figure, concept, text, institution, timeline event,
argument, bibliography entry) carries a short index **card** and a
longer encyclopedia **body**, both authored as markdown in
`portal/data/seed.json`, rendered to HTML at build time with
`[[wiki-style]]` links resolved.

## Global Standards

### Provenance Discipline

> **No assertion without attribution.** If you write it, you can point
> to it.

- Don't write: "John of Morigny practiced necromancy."
- Do write: "John's own Book of Visions confesses to experimentation
  with both necromancy (*nigromancia*) and the *ars notoria* (Fanger,
  *Rewriting Magic*, p.2)."
- Add the row this claim rests on to `scholarly_refs` in the same
  seed.json edit: `entity_slug` + `bib_source_id` + `page_ref`.

If a claim is CONTEXT (background, not something this portal's corpus
directly attests), say so explicitly rather than letting it read as
equally certain.

### Confidence & Review Status

- `confidence: HIGH` — you read this passage in the source yourself.
- `confidence: MEDIUM` — synthesized from multiple passages or a good
  secondary summary.
- `confidence: LOW` — plausible, not yet verified. Flag it honestly —
  several real gaps exist here (see the portal's `about.html`): the
  Fanger–Watson critical edition, Véronèse's monographs, Watson's 1998
  *Conjuring Spirits* essay, Newman's 2005 *Speculum* article, and
  *RB 1980* were not available at build time.
- `review_status`: `DRAFT` (first pass) → `REVIEWED` → `VERIFIED`
  (every claim checked against its source).

### Terminology

- Latin terms italicized on first use: *ars notoria*, *nigromancia*,
  *Liber florum celestis doctrine*. Keep the Latin alongside any
  translation, don't replace it — John's own idiom matters.
- **Old Compilation** / **New Compilation** capitalized (John's own
  major redactions).
- Bridget's name: use **Burgeta** as the primary form (the manuscript
  reading Fanger's 2015 edition adopts), noting "Gurgeta/Georgette"
  as the superseded 2001 reading in `name_variants`, not as the
  headline.
- "Barking Dogs" (John's own term for his 1315 condemners) stays
  quoted, always — it's his idiom, not a modern label.

---

## Figures

### Card (60–150 words)

Name + dates/floruit + role + one sentence of significance + 2–3
specific claims.

**Worked example** (using findings already in hand):

> **Bridget** (*Burgeta* in the authoritative manuscripts — not
> "Gurgeta/Georgette" as in the superseded 2001 edition), John of
> Morigny's sister. One of two named witnesses (with John of
> Fontainejean) whose testimony against the *ars notoria* John records
> in the Book of Visions (I.iii). Lived near Morigny, in the Orléans–
> Étampes corridor John himself moved through. Her exact role — student,
> co-practitioner, only a witness — is not yet resolved in the sources
> this portal has read; treated here as a real historical presence, not
> assumed beyond what the text says.

### Body (1,200–2,200 words)

1. **Opening (250–350 words):** full name/variants, dates or floruit,
   region, one-sentence significance.
2. **Life (300–450 words):** chronological, dated, place-named. ATTESTED
   vs. COMPARATIVE vs. CONTEXT.
3. **Intellectual work / role (350–500 words):** what did they actually
   do, argue, write?
4. **Transmission and reception (250–400 words, if applicable).**
5. **Historiographical debates (200–350 words, if applicable).**
6. **Literature (5–12 entries), DGWE-style: Author. *Title*. Publisher, Year.**

---

## Concepts

### Card (60–120 words)

**Worked example:**

> ***Ars notoria*** (the Notory Art). A ritual system, condemned since
> the thirteenth century, promising infused knowledge of the liberal
> arts, philosophy, and theology through prayers and the contemplation
> of geometric figures (*notae*) inscribed with unknown words (*verba
> ignota*). John of Morigny practiced it as a young monk at Orléans,
> came to read his own visionary experience as evidence of its
> demonic contamination, and responded not by abandoning ritual
> practice but by rewriting it — the *Liber florum celestis doctrine*
> is his purified answer, explicitly modeled on the ars notoria's own
> shape (Fanger, *Rewriting Magic*, p.2).

### Body (800–1,800 words)

1. Etymology/terminology (100–200 words).
2. Definition and scope (150–300 words).
3. Historical development (250–400 words).
4. John's own treatment, if central (250–400 words).
5. Technical operations, if applicable (150–300 words).
6. Historiographical significance (150–250 words).
7. Related concepts (100–200 words).
8. Literature (5–8 entries).

---

## Texts (Primary Sources)

### Card (80–150 words)

Title (Latin + translated) + author + date + text type + significance
+ 2 key content points.

### Body (1,000–1,800 words)

1. Opening (200–300 words).
2. Content and arguments (350–500 words).
3. Textual tradition — manuscripts, editions (200–400 words).
4. Reception and influence (200–350 words).
5. Historiographical debates (150–250 words).
6. Literature (5–10 entries).

---

## Timeline Events

### Card (40–120 words)

Year + title + what happened + why it matters, in John's own idiom
where the sources give it to us.

**Worked example:**

> **1315: The "Barking Dogs" condemn the Book of Figures.** Unnamed
> canon lawyers — John's own term, never explained further — condemn
> his original Book of Figures as too closely resembling necromantic
> diagrams. This is a real, distinct condemnation eight years before
> the famous 1323 Paris burning, and the direct cause of the New
> Compilation: John cannot recall the already-circulating condemned
> text, so instead rewrites the ritual and spiritual process it
> describes (Fanger, *Rewriting Magic*, p.2–3, p.105).

---

## Arguments (Historiographical Claims)

### Card (80–150 words)

Claim + against what + stakes.

**Worked example:**

> **Book condemnation is not effective censorship.** Fanger argues,
> against the intuitive assumption that a 1323 public burning would
> have suppressed a text, that the evidence of the *Liber florum*'s
> continued transmission and ritual use among literate monks *after*
> 1323 — likely via Benedictine travel between monasteries — directly
> challenges "the widespread belief that book condemnation constitutes
> effective censorship" (*Rewriting Magic*, p.21–22). Stakes: reframes
> how historians should read every other recorded medieval book-burning
> as evidence of suppression's *intent*, not its success.

### Body (800–1,200 words)

1. The argument, precisely (150–250 words).
2. Against what (150–250 words).
3. Evidence (300–500 words).
4. Reception (150–250 words).
5. Literature (3–5 key sources).

---

## Bibliography Entries (Document Summaries)

### Card (80–150 words)

Author + title + year + pub type + one-sentence contribution.

### Body (500–1,000 words)

1. Bibliographic info (100 words).
2. Argument and contribution (250–400 words) — what does this work
   actually argue, and how?
3. Key passages (150–250 words) — specific pages relevant to John.
4. Reception (100–150 words).

---

## Entity Links

`[[slug]]` for specific people/texts/concepts. Don't link generic terms.
Don't link a name in the entry that defines it.

## Verification Checklist Before Publishing

- [ ] Every non-CONTEXT claim has a `scholarly_refs` row with a page number?
- [ ] Confidence and review_status honestly set?
- [ ] Card/body word counts in range?
- [ ] Titles italicized (`*title*`)?
- [ ] `[[slug]]` links resolve (check the build's "missing" styling)?
- [ ] Sources actually read, not summarized from summaries?
