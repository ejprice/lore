# REPORT-corpus-scout-1 — D&D rules corpus characterisation

brief-base v9 read
state: done
deviations: none
Packages considered: none — no mechanism specified (survey only; see §8.1 for the one package
question the lead WILL face and which I did NOT evaluate, so nobody inherits a false clear)
decisions-needed:
  · D1 §7.1 — the tir.md / the-illrigger-revised.md byte-identical pair: drop one or index both?
  · D2 §7.2 — 2014-vs-2024 same-name spells (19 pairs): keep both editions or Core-only?
  · D3 §8.2 — 2014-tier stat blocks are structurally degraded; extract, or 2024-tier only?
receipt pointers:
  · §6 GRAPH VERDICT (the three target queries)          · §6.4 instrument, pasted verbatim
  · §2 entity taxonomy + counts and how each was derived · §3 per-entity field extractability
  · §4 cross-reference conventions (the negative result) · §7 collision tables
  · §8 hazards ranked H1-H10 (H1, H5, H7b are the sharp ones, each with an instrument)
  · §9 what I did NOT check — the stated bound of this survey

**Scope + date of every measurement below: the tree at
`/home/ejprice/code/python/dndlorescraper/output`, measured 2026-08-01. The corpus is a static
scrape (`scraped_at` 2026-07-31T00:22–00:55Z in every file's frontmatter), so the line numbers
cited here are stable for this snapshot — they are NOT stable against a re-crawl.** Cite by
heading text where you can; I give line numbers because the brief required them.

**Tooling honesty:** this corpus is in no lore index, so every measurement here is plain
Read/Bash/Grep/python-stdlib, as the brief authorised. No fallback disclosure is owed.

---

## 1. File / format survey

### 1.1 Layout

```
output/
  .crawl-state.json          scraper manifest (§5)
  Core/{dmg-2024, mm-2024, phb-2024}/          16 + 31 + 15 = 62 files
  Expanded/{efota, erftlw, scag, tcoe, xgte}/  12 + 17 +  9 + 23 + 16 = 77 files
  MCDM/tir/                                     2 files
                                              --------
                                              141 markdown files
```

Sizes: `Core/dmg-2024` 501K · `Core/mm-2024` 432K · `Core/phb-2024` 420K · `Expanded/erftlw`
566K · `Expanded/scag` 342K · `Expanded/tcoe` 300K · `Expanded/xgte` 301K · `Expanded/efota`
165K · `MCDM/tir` 83K.

One file per source **page** (= one dndbeyond chapter URL). Filename = the URL's last path
segment. Each book directory also holds a **root file named for the book slug**
(`phb-2024.md`, `xgte.md`, …) which is a **table of contents**, not content — with exactly one
exception, `MCDM/tir/tir.md`, which is the full book (§7.1).

Largest single files, which is where the entity mass is:
`Core/phb-2024/spell-descriptions.md` 360K · `Expanded/scag/the-sword-coast-and-the-north.md`
307K · `Core/dmg-2024/magic-items-a-z.md` 282K · `Expanded/xgte/subclasses.md` 205K ·
`Core/phb-2024/character-classes-continued.md` 188K.

### 1.2 Frontmatter — 100% uniform, and it is the single best thing about this corpus

**All 141 files open with `---` YAML frontmatter carrying exactly the same 12 keys, no more and
no fewer:**

```
source_book  abbrev  slug  edition  publisher  game  tier
source_url   page    page_title  scraped_at  content_sha256
```

Derived with `^[A-Za-z0-9_]+(?=:)` over the span between each file's first two `---` lines:
**every one of the 12 keys returns 141/141, and a per-file key count finds zero files deviating
from 12.**

⚠ **A note on how that number was nearly wrong, because it is the kind of error this corpus will
invite again.** My first pass used `^[a-z_]+(?=:)` and reported **11** keys — it silently
dropped `content_sha256`, because the character class excludes digits and so could not match a
key ending in `256`. The miss was invisible: 11 keys × 141/141 looks exactly as clean as 12 ×
141/141. It surfaced only because a *different* measurement (§5, the manifest hash cross-check)
needed `content_sha256` and found it present in all 141. **A key-name regex that excludes digits
will under-report any schema containing a digit-suffixed field, and will look perfectly uniform
while doing it.**

Example (`Core/phb-2024/spell-descriptions.md:1-15`):

```yaml
---
source_book: Player's Handbook
abbrev: PHB
slug: phb-2024
edition: '5.5'
publisher: Wizards of the Coast
game: Dungeons & Dragons
tier: Core
source_url: https://www.dndbeyond.com/sources/dnd/phb-2024/spell-descriptions
page: spell-descriptions
page_title: Spell Descriptions
scraped_at: '2026-07-31T00:54:43.305645+00:00'
content_sha256: 9a61e324ce4e9d032488b23c328f3253f8a4ccc8bc7c636e3230bc644ec20a05
---
```

**`edition` is the 2014-vs-2024 disambiguator and it is already in every file** — this is the
key that defuses hazard §7.2. Measured distribution:

| edition | tier | books | files |
|---|---|---|---|
| `'5.5'` | Core | MM, DMG, PHB | 31 + 16 + 15 = 62 |
| `'5.5'` | Expanded | EFotA | 12 |
| `'5.5'` | MCDM | tIR | 2 |
| `'5.0'` | Expanded | TCoE, ERftLW, XGtE, SCAG | 23 + 17 + 16 + 9 = 65 |

### 1.3 Heading structure

Corpus-wide heading histogram: `#`×140, `##`×1068, `###`×4012, `####`×3312, `#####`×738.

**140 H1, not 141** — `Expanded/xgte/xgte.md` has no `# ` heading at all; it opens on a
blockquote (line 17). Every other file's first heading is H1 and equals the book/chapter title.

Depth is **not semantically stable across books.** The same entity type appears at different
levels depending on the file:

| entity | usual level | counter-example |
|---|---|---|
| spell (PHB) | `###` | — 391/391 consistent |
| spell (SCAG) | `####` | `Expanded/scag/classes.md:997` `#### Booming Blade` |
| magic item (DMG) | `###` | 3 sub-variants at `####`, e.g. `magic-items-a-z.md:817` `#### Crystal Ball of Mind Reading` |
| monster (MM) | `###` | `#### Faerie Dragon Adult` under `## Faerie Dragons` (`monsters-f.md:31`) |

**⇒ Do not key entity type on heading depth. Key it on the descriptor/field line that follows
the heading** (§3). This is not a theoretical worry — it costs exactly one false entity today
(§8.4).

Content separator: a bare `***` line is used as an entity terminator in the entity-dense files
(`spell-descriptions.md` 368 of them for 391 spells; `feats.md` 75 for 75 feats;
`creature-stat-blocks.md` 51 for 51 blocks). It is *usable* as a slice-end but is **not
universal** — `magic-items-a-z.md` has zero, and `spell-descriptions.md`'s 368 < 391.

Tables: 24,010 table rows corpus-wide, 2,541 header-separator rows ⇒ roughly 2.5k markdown
tables. Standard GFM pipe tables throughout.

---

## 2. Entity taxonomy and counts

Every count below states its derivation. Where a count needed reconciling, the reconciliation is
shown — no figure here is a raw grep I did not interrogate.

| entity type | count | derivation |
|---|---|---|
| **Spells** | **528 entries / 496 distinct names** | heading whose next non-blank line matches one of the 4 descriptor dialects (§3.1) |
| **Stat blocks (monsters/NPCs/companions)** | **667 entries / 596 distinct names** | 599 with `^**AC** ` (2024 dialect) + 68 with `^**Armor Class** ` (2014 dialect) |
| — of which 2024 dialect | 599 | `grep -c '^\*\*CR\*\* '` = 599, pairs 1:1 with `^**AC** ` |
| — of which 2014 dialect | 68 | `grep -c '^\*\*Armor Class\*\* '` |
| **Magic items** | **372 entries / 368 distinct names** | heading whose next non-blank line matches `^\*(Wondrous Item\|Weapon\|Armor\|Ring\|Rod\|Staff\|Wand\|Potion\|Scroll)[^*]*\*$` |
| **Feats (2024 dialect)** | **103** | `^\*[A-Za-z ]*Feat[^*]*\*$` → PHB `feats.md` 75, EFotA `character-options.md` 28 |
| **Feats (2014 dialect)** | **31** | TCoE `feats.md` 15 H2 entries + XGtE `character-options-racial-feats.md` 16 H3 entries (no descriptor line; heading-only) |
| **Classes (PHB 2024)** | **12** | `^## ` in `character-classes{,-continued}.md` |
| **Subclasses (PHB 2024)** | **48** | `####` inside a `### <Class> Subclasses` region, **minus 1 false positive** (§8.4) |
| **Backgrounds (PHB 2024)** | **16** | `###` under `## Background Descriptions`, `character-origins.md:68-359` |
| **Species (PHB 2024)** | **10** | `###` under `## Species Descriptions`, `character-origins.md:360-` |
| **Class spell-list rows (PHB 2024)** | **987** | rows in the 70 `#### [Level N\|Cantrips] <Class> Spells` tables |
| **Rules sections / prose** | — | the residual; DMG + SCAG + ERftLW are overwhelmingly narrative, not entity-bearing |

### 2.1 Spell entries by file

| file | n | descriptor dialect |
|---|---|---|
| `Core/phb-2024/spell-descriptions.md` | 391 | 2024 italic-Level-Title-Case **+ class list** |
| `Expanded/xgte/spells.md` | 95 | 2014 plain-ordinal-lowercase |
| `Expanded/tcoe/magical-miscellany.md` | 21 | italic-ordinal-lowercase |
| `MCDM/tir/tir.md` | 8 | italic-ordinal-Title-Case |
| `MCDM/tir/the-illrigger-revised.md` | 8 | *(duplicate of the row above — §7.1)* |
| `Expanded/scag/classes.md` | 4 | italic-ordinal-lowercase |
| `Expanded/erftlw/character-creation-dragonmarks.md` | 1 | italic-ordinal-lowercase |

### 2.2 The 2024 stat-block population, derived

Sizes: Medium 254 · Large 158 · Tiny 54 · Huge 49 · Small 38 · Gargantuan 20.

Types: Beast 129 · Humanoid 63 · Monstrosity 60 · Fiend 51 · Dragon 51 · Undead 39 ·
Aberration 36 · Elemental 32 · Fey 26 · Construct 20 · Plant 17 · Celestial 16 · Giant 14 ·
Ooze 6 · plus 11 `Swarm of …` and 2 `Celestial or Fiend`.

CR: 0→48, 1/8→32, 1/4→56, 1/2→43, 1→51, 2→61, 3→45, 4→34, 5→37, 6→25, 7→18, 8→24, 9→14,
10→16, 11→14, 12→7, 13→9, 14→4, 15→6, 16→7, 17→7, 18→1, 19→1, 20→4, 21→5, 22→3, 23→5, 24→2,
25→1, 30→1, **`None`→18**.

**Reconciliation, stated because a raw grep would have misled:** `grep -c '^\*\*CR\*\* '`
returns **599**; a numeric-CR parse returns **581**. The 18-block difference is
`**CR** None (XP 0; PB equals your Proficiency Bonus)` — summoned/companion stat blocks
embedded inside spell descriptions (12 in `spell-descriptions.md`), class features (3 in
`character-classes-continued.md`), EFotA's artificer (2) and one magic item
(`magic-items-a-z.md:1133`). **They are real stat blocks, not parse failures.** Any "monster
count" that says 581 has silently dropped every summon in the game.

---

## 3. Structured field extractability per entity type

### 3.1 SPELLS — four descriptor dialects, all parseable; one carries class, three do not

| # | dialect | example | files | carries class? | ritual? |
|---|---|---|---|---|---|
| A | 2024 italic, `Level N`, Title Case, **class list** | `*Level 2 Abjuration (Bard, Cleric, Druid, Paladin, Ranger)*` | PHB (391) | **YES** | no — see below |
| B | 2014 plain, ordinal, lowercase | `8th-level necromancy` | XGtE (95) | no | `(ritual)` suffix |
| C | italic, ordinal, lowercase | `*9th-level conjuration*` | TCoE (21), SCAG (4), ERftLW (1) | no | `(ritual)` suffix |
| D | italic, ordinal, Title-Case | `*4th-Level Abjuration*` | MCDM (8) | no (separate field) | `(ritual)` suffix |

**Dialect A parses at 391/391 with zero unmatched** against
`^\*(?:Level (\d+) (\w+)|(\w+) Cantrip)( \(Ritual\))?(?: \(([^)]*)\))?\*$`. Levels 0→34, 1→64,
2→63, 3→52, 4→41, 5→48, 6→34, 7→21, 8→18, 9→16. Schools: Conjuration 72, Transmutation 66,
Evocation 63, Abjuration 55, Enchantment 42, Divination 33, Necromancy 31, Illusion 29.

**Field lines: 528/528 spell entries carry all four of Casting Time / Range / Components /
Duration.** No spell in the corpus is missing one. Two styles:

- bold `**Casting Time:** Action` — PHB, TCoE, SCAG, MCDM, ERftLW (433 entries)
- plain `Casting Time: 1 action` — XGtE only (95 entries)

**A fifth field exists in exactly one book:** MCDM's 8 spells each carry
`**Classes:** Cleric, paladin` (e.g. `MCDM/tir/tir.md:1205`). No other file uses it.

**Ritual is NOT in the 2024 descriptor — it is inside the Casting Time value.** PHB encodes it
as `**Casting Time:** Action or Ritual` / `1 minute or Ritual` / `1 hour or Ritual` /
`10 minutes or Ritual`. **31 PHB spells are rituals**, derived by `'Ritual' in casting_time`.
(A `(Ritual)` token in the descriptor line: **zero occurrences** — an extractor looking there
finds nothing and would report 0 rituals. This is the single most likely silent-wrong-answer in
the corpus.)

Casting Time takes 22 distinct values in PHB (Action 278, Bonus Action 24, Action-or-Ritual 18,
1 minute 17, 10 minutes 12, 1-minute-or-Ritual 11, 1 hour 10, …) — a small closed-ish set plus
long trigger clauses (`Bonus Action, which you take immediately after hitting a creature with a
Melee weapon or an Unarmed Strike`, ×5). Components takes 6 shapes: `V, S, M (…)` 198,
`V, S` 125, `V` 46, `V, M (…)` 8, `S, M (…)` 8, `S` 6.

### 3.2 MONSTERS

**2024 dialect (599 blocks) — excellent.** Shape (`Core/mm-2024/monsters-f.md:190-215`,
Fire Giant):

```
### Fire Giant
Huge Giant, Lawful Evil          <- meta line: Size Type[ (Tags)], Alignment
**AC** 18 **Initiative** +3 (13)
**HP** 162 (13d12 + 78)
**Speed** 30 ft.
| Ability | Score | Mod | Save |   <- TWO tables: Str/Dex/Con, then Int/Wis/Cha
**Skills** … **Immunities** … **Senses** … **Languages** …
**CR** 9 (XP 5,000; PB +4)
Actions                          <- plain paragraph, NOT a heading
***Multiattack.*** …
```

- **Size/Type/Alignment meta line parses at 597/599 (99.7%).** The 2 misses:
  `Core/mm-2024/how-to-use-a-monster.md:54` (an annotated teaching example, callout digit `2`)
  and `Core/phb-2024/spell-descriptions.md:204` `Huge or Smaller Construct, Unaligned` (a size
  *range*, not a size). Neither is corruption.
- **The name is a markdown heading in 598/599 (99.8%)** — the sole exception is the same
  teaching example.
- Field-line coverage across all 599: AC 599, HP 599, Speed 599, Senses 599, Languages 599,
  CR 599 (**six fields at 100%**); Skills 394, Immunities 244, Resistances 132, Gear 92,
  Vulnerabilities 24 (genuinely optional).
- Ability scores are in **two** markdown tables per block, not one — `animals.md` shows 192
  `| Ability | Score | Mod | Save |` headers for 96 blocks. An extractor expecting one table
  per monster loses Int/Wis/Cha silently.
- Section labels (`Actions`, `Bonus Actions`, `Reactions`, `Legendary Actions`) are **plain
  paragraphs**, not headings.

**2014 dialect (68 blocks) — structurally degraded, see §8.2.**

### 3.3 MAGIC ITEMS — the cleanest entity in the corpus

`Core/dmg-2024/magic-items-a-z.md` has **347 H3 headings and 347 parsable descriptors
(100.0%)**, plus 3 H4 sub-variants (`#### Crystal Ball of Mind Reading|Telepathy|True Seeing`,
lines 817/823/829) = **350 in that file, 372 corpus-wide**.

Grammar: `*<Category>[ (<Subtype>)], <Rarity>[ (Requires Attunement[ by <restriction>])]*`

- **Category** (372 total): Wondrous Item 185, Weapon 58, Potion 30, Armor 28, Ring 24, Wand 18,
  Staff 17, Rod 9, Scroll 3.
- **Rarity** (DMG 347): Uncommon 93, Rare 93, Very Rare 68, Common 51, Legendary 36,
  Artifact 11, `Rarity Varies` 11. **8 items carry multiple rarities on one line** — variant
  items like `*Armor (Any Light, Medium, or Heavy), Rare (+1), Very Rare (+2), or Legendary
  (+3)*` (`magic-items-a-z.md:158`). A single-rarity extractor must decide what to do with
  these rather than silently take the first.
- **Attunement: 169 of 347 DMG items** say `Requires Attunement` in the descriptor; 278
  occurrences of the phrase corpus-wide. **The restriction is inside the same parenthetical and
  is machine-extractable**, e.g. `Requires Attunement by a Druid or Warlock` (`:694`),
  `by a Sorcerer, Warlock, or Wizard` (`:3100`), `by a Dwarf or a Creature Attuned to a Belt of
  Dwarvenkind` (`:1303`). That is a free item→class and item→species edge set.

### 3.4 FEATS

2024 dialect carries a full descriptor: `*General Feat (Prerequisite: Level 4+)*` ×18,
`*Origin Feat*` ×10, `*Epic Boon Feat (Prerequisite: Level 19+)*` ×11, `*Fighting Style Feat
(Prerequisite: Fighting Style Feature)*` ×10, `*Dragonmark Feat (…)*` ×13 (EFotA), plus ~20
one-off prerequisite strings. **Category and prerequisite are both extractable.** 2014-dialect
feats (TCoE 15, XGtE 16) have **no descriptor line at all** — heading + prose only.

---

## 4. Cross-reference conventions — the important negative result

### 4.1 There are ZERO links and ZERO anchors in the entire corpus

```
grep -rhoP '\[[^]]+\]\([^)]+\)' --include='*.md' .  |  wc -l     ->  0
grep -rc  '<a \|id="'           --include='*.md' .               ->  no file
```

**Not one markdown link. Not one HTML anchor. Not one `id=`.** Every cross-reference in this
corpus is a **bare, capitalised entity name in running prose**. Receipts:

- `magic-items-a-z.md:4012` (Wand of Fireballs): *"you can expend no more than 3 charges to
  cast Fireball (save DC 15) from it"*
- `monsters-l.md:379` (Lich): *"**At Will:** Detect Magic, Detect Thoughts, Dispel Magic,
  Fireball (level 5 version), Invisibility, Lightning Bolt (level 5 version), Mage Hand,
  Prestidigitation"*
- `monsters-l.md:323`: *"can be brought back to life only by a True Resurrection or Wish spell"*

### 4.2 The book's own stated typographic convention did NOT survive the scrape

`Core/dmg-2024/magic-items-a-z.md:20` tells the reader: *"If a magic item description
capitalizes a creature's name and presents it in **bold** type, that's a visual cue pointing you
to the creature's stat block."* **That cue is gone.** Measured over that whole 282K file:

- only **13 bold runs**, 7 distinct — and 6 of the 7 are stat-block field labels (`Speed`,
  `Initiative`, `Senses`, `Languages`, `Immunity`, `Immunities`). **Exactly one** distinct bold
  token is a creature name (`Avatar of Death`, 2 occurrences).
- 156 italic runs, 56 distinct, of which **7 are PHB spell names** (12 occurrences: Wish 3,
  Scrying 2, Suggestion 2, Daylight 2, Detect Thoughts, Light, Sending). The rest are item
  names (`Blackrazor`, `Moonblade`, `Portable Hole`, …).

**⇒ Markup is structural, not referential.** `***Name.***` opens a trait; `**Field**` labels a
stat; `*…*` mostly italicises item titles. **An extractor must not use bold/italic to detect
cross-references — it will find ~1% of them.** Edges have to come from string-matching bare
names against an entity-name index, which makes the entity-name index the load-bearing
artifact and makes name collisions (§7) the load-bearing hazard.

### 4.3 Spell→class mappings: EXPLICIT for 523 of 528 entries, prose-only for 5

*(523 = PHB 391 + XGtE 95 + TCoE 21 + MCDM 8+8; the 5 remainder are SCAG's 4 and ERftLW's 1.
523 + 5 = 528, checked.)*

This is the good news, and it is better than the brief anticipated. **Three structured shapes
plus one prose case:**

**(i) PHB 2024 — TWO independent explicit sources that agree perfectly.**

- *Source A*, inline in the descriptor: `*Level 2 Abjuration (Bard, Cleric, Druid, Paladin,
  Ranger)*` — 987 class tokens over 391 spells.
- *Source B*, the eight `### <Class> Spell List` sections, each holding
  `#### [Cantrips (Level 0 X Spells)|Level N X Spells]` subsections with
  `| Spell | School | Special |` tables, where **Special** is `C`=Concentration, `R`=Ritual,
  `M`=Material (legend at `character-classes.md:1626`). 70 such tables, 987 rows.

  | class | section | file:line |
  |---|---|---|
  | Bard | `### Bard Spell List` | `character-classes.md:630` |
  | Cleric | `### Cleric Spell List` | `character-classes.md:1098` |
  | Druid | `### Druid Spell List` | `character-classes.md:1624` |
  | Paladin | `### Paladin Spell List` | `character-classes-continued.md:334` |
  | Ranger | `### Ranger Spell List` | `character-classes-continued.md:786` |
  | Sorcerer | `### Sorcerer Spell List` | `character-classes-continued.md:1769` |
  | Warlock | `### Warlock Spell List` | `character-classes-continued.md:2582` |
  | Wizard | `### Wizard Spell List` | `character-classes-continued.md:3047` |

  **A vs B cross-check: 987 = 987, zero disagreement in either direction, all 8 classes.**

  | class | via descriptor | via table | A-only | B-only |
  |---|---|---|---|---|
  | Bard | 140 | 140 | 0 | 0 |
  | Cleric | 117 | 117 | 0 | 0 |
  | Druid | 135 | 135 | 0 | 0 |
  | Paladin | 51 | 51 | 0 | 0 |
  | Ranger | 61 | 61 | 0 | 0 |
  | Sorcerer | 150 | 150 | 0 | 0 |
  | Warlock | 91 | 91 | 0 | 0 |
  | Wizard | 242 | 242 | 0 | 0 |

  **Two independent sources that agree is a free correctness oracle for the extractor** — build
  both, diff them, and any future divergence is a real parser bug rather than a silent wrong
  answer. I recommend the lead treat this as a required build-time pin, not a nice-to-have.

**(ii) XGtE (95 spells) — blockquote lists, `## Spell Lists` at `xgte/spells.md:25`,** eight
`### <Class> Spells` subsections (Bard :29, Cleric :69, Druid :95, Paladin :193, Ranger :207,
Sorcerer :237, Warlock :369, Wizard :463). Rows look like `> *Control flames* (transmutation)`
and `> Create bonfire (conjuration)` under `> **Cantrips (0 Level)**` / `> **2nd Level**`
headers. Coverage: Bard 12, Cleric 7, Druid 40, Paladin 3, Ranger 9, Sorcerer 55, Warlock 36,
Wizard 77 = 239 rows over 95 distinct spells.

  ⚠ **Two traps here, both measured:**
  - **Names are case-mangled** (sentence case, not title case). Joining the list to the detail
    headings: **exact-case 20/95; case-insensitive 95/95.** An exact-string join loses 79% of
    XGtE's class edges *silently*.
  - **The italics are noise, not a flag.** 59 distinct names appear italicised, 49 non-
    italicised — **13 names appear BOTH ways** in different class lists (e.g. `Absorb
    elements`). Both sets join 100% to detail entries, so italic carries no information. Do not
    branch on it.

**(iii) TCoE (21 spells) — one flat table**, `### Spells` at
`Expanded/tcoe/magical-miscellany.md:34`, columns
`| Level | Spell | School | Conc. | Ritual | Class |`. This is the **richest** shape of the
three: concentration and ritual are their own columns, and Class is an explicit comma list
including `Artificer` (a class with no PHB-2024 spell list).

**(iv) MCDM (8 spells) — per-spell `**Classes:**` field** (§3.1), plus the prose at
`tir.md:1158`: *"available to the Architect of Ruin. If your GM agrees, these spells are also
available to the classes noted in each spell description."*

**(v) PROSE-ONLY — 5 entries, no structured source:**
- SCAG's 4 cantrips: availability is one English sentence, `Expanded/scag/classes.md:991` —
  *"These cantrips are on the sorcerer, warlock, and wizard spell lists."*
- ERftLW's 1 spell (`character-creation-dragonmarks.md`): dragonmark-gated, prose only.

---

## 5. The one JSON file — `.crawl-state.json` (57,991 bytes)

A **scraper resume/dedup manifest**, and a genuinely useful sidecar. Shape:

```json
{ "version": 1,
  "sources": { "<slug>": { "name": ..., "first_seen": ..., "last_crawled": ...,
      "pages": { "<page>": { "url": ..., "md_path": ..., "content_hash": "sha256:…",
                             "fetched_at": ..., "etag": null, "last_modified": null } } } } }
```

9 sources (dmg-2024, efota, erftlw, mm-2024, phb-2024, scag, tcoe, tir, xgte), page counts
16/12/17/31/15/9/23/2/16.

**Validated against disk, three ways, all clean:**
- 141 page entries, 141 distinct `md_path`, 141 `.md` files on disk
- set difference **both directions: empty** (nothing manifested-but-missing, nothing
  on-disk-but-unmanifested)
- **`content_hash` == the file's own frontmatter `content_sha256`: 141 match, 0 mismatch**

⇒ It is a trustworthy source→file→URL map and a re-crawl change-detector. `etag` and
`last_modified` are `null` throughout, so incremental crawling is hash-based only.

---

## 6. GRAPH-READINESS VERDICT

**Headline: all three target queries are fully supported by PHB-2024 data, and two of the three
are supported by two independent sources that I verified agree exactly.**

### 6.1 (a) All Druid spells of level 4 — ✅ SUPPORTED, two independent sources, both agree

- **Source A (spell-detail):** `Core/phb-2024/spell-descriptions.md`, the descriptor line under
  each `### <Spell>` heading — filter `level == 4 and 'Druid' in classes`.
- **Source B (spell-list):** `Core/phb-2024/character-classes.md`,
  `#### Level 4 Druid Spells` at **line 1719** (inside `### Druid Spell List`, line 1624).

Both return **the same 21 spells, identical sets**:

> Blight · Charm Monster · Confusion · Conjure Minor Elementals · Conjure Woodland Beings ·
> Control Water · Divination · Dominate Beast · Fire Shield · Fount of Moonlight · Freedom of
> Movement · Giant Insect · Grasping Vine · Hallucinatory Terrain · Ice Storm · Locate Creature ·
> Polymorph · Stone Shape · Stoneskin · Summon Elemental · Wall of Fire

### 6.2 (b) All Druid ritual spells — ✅ SUPPORTED, two independent sources, both agree

- **Source A:** `**Casting Time:**` value contains `Ritual` (**not** the descriptor — §3.1).
- **Source B:** `Special` column contains `R` in the Druid spell-list tables
  (`character-classes.md:1624-1815`).

Both return **the same 14 spells**:

> Animal Messenger · Augury · Beast Sense · Commune with Nature · Detect Magic · Detect Poison
> and Disease · Divination · Feign Death · Locate Animals or Plants · Meld into Stone · Purify
> Food and Drink · Speak with Animals · Water Breathing · Water Walk

### 6.3 (c) Exact-name lookup "Fireball" → full spell text — ✅ SUPPORTED, unambiguous

`grep -rn '^#\+ Fireball$'` returns **exactly one hit corpus-wide**:
`Core/phb-2024/spell-descriptions.md:2894`. Full text is the slice from that heading to the next
`***` (line 2910) — descriptor `*Level 3 Evocation (Sorcerer, Wizard)*`, all four fields, body,
and the `***Using a Higher-Level Spell Slot.***` rider.

`\bFireball\b` occurs **45 times across 21 files** corpus-wide. Two of those are inside the
definition file itself — `### Fireball` (:2894) and **`### Delayed Blast Fireball` (:1887),
which is a different spell** (see H7b). So the inbound reference-edge set is **43 occurrences
across 20 other files**: `magic-items-a-z.md` 10, `character-classes-continued.md` 6,
`dms-toolbox.md` 4, then doubles and singles across 17 more.

⚠ **Two bounds on this verdict, both of which the lead should read before generalising:**
1. **`Fireball` happens to be name-unique. It is not representative** — 32 spell names are not
   (§7.2). Exact-name lookup is unambiguous only *after* the edition/book disambiguation is
   designed.
2. **Even for this unique name, naive bare-name matching already produces one false edge**
   (`Delayed Blast Fireball`). That is H7b, and it is not a corner case.

### 6.4 The instrument — pasted verbatim, because the §6.1/§6.2 agreement claim rests on it

I am read-only, so per brief-base §1 this survives here rather than in `scripts/`. Run from
`/home/ejprice/code/python/dndlorescraper/output/Core/phb-2024`.

```python
import re, pathlib, collections

# --- Source A: descriptor lines in spell-descriptions.md ---
sd = pathlib.Path('spell-descriptions.md').read_text().splitlines()
idx = [i for i, l in enumerate(sd) if l.startswith('### ')]
pat = re.compile(r'^\*(?:Level (?P<lvl>\d+) (?P<s1>\w+)|(?P<s2>\w+) Cantrip)'
                 r'(?: \((?P<cls>[^)]*)\))?\*$')
A = {}
for i in idx:
    name = sd[i][4:].strip()
    for w in sd[i+1:i+5]:
        m = pat.match(w)
        if m:
            lvl = int(m['lvl']) if m['lvl'] else 0
            cls = {c.strip() for c in (m['cls'] or '').split(',') if c.strip()}
            ritual = any('Ritual' in x for x in sd[i:i+10]
                         if x.startswith('**Casting Time:**'))
            A[name] = dict(level=lvl, school=m['s1'] or m['s2'],
                           classes=cls, ritual=ritual)
            break

# --- Source B: the eight class spell-list tables ---
B = collections.defaultdict(dict)          # class -> {spell: (level, school, special)}
hdr = re.compile(r'^#### (?:Cantrips \(Level 0 (?P<c0>\w+) Spells\)'
                 r'|Level (?P<lvl>\d+) (?P<c1>\w+) Spells)$')
for fn in ('character-classes.md', 'character-classes-continued.md'):
    L = pathlib.Path(fn).read_text().splitlines()
    cur = None
    for l in L:
        m = hdr.match(l)
        if m:
            cur = (m['c0'] or m['c1'], 0 if m['c0'] else int(m['lvl']));  continue
        if l.startswith('#'):
            if l.startswith('### ') or l.startswith('## '): cur = None
            continue
        if cur and l.startswith('| ') and '| ---' not in l and not l.startswith('| Spell '):
            parts = [p.strip() for p in l.strip('|').split('|')]
            if len(parts) == 3:
                B[cur[0]][parts[0]] = (cur[1], parts[1], parts[2])

# --- the three target queries, each answered twice and diffed ---
for c in sorted(B):
    inA = {n for n, d in A.items() if c in d['classes']}
    assert inA == set(B[c]), (c, inA ^ set(B[c]))       # 8/8 classes, 987 rows, no diff
a4 = sorted(n for n, d in A.items() if 'Druid' in d['classes'] and d['level'] == 4)
b4 = sorted(n for n, (l, s, sp) in B['Druid'].items() if l == 4)
ar = sorted(n for n, d in A.items() if 'Druid' in d['classes'] and d['ritual'])
br = sorted(n for n, (l, s, sp) in B['Druid'].items()
            if 'R' in [x.strip() for x in sp.split(',')])
print(len(a4), a4 == b4)        # -> 21 True
print(len(ar), ar == br)        # -> 14 True
```

---

## 7. Collisions and duplicates (measured, exhaustive)

### 7.1 The one true file duplicate — `MCDM/tir/`

`tir.md` and `the-illrigger-revised.md` have **byte-identical bodies**
(`md5 d31810906adbb3934f38c88df54b8a12` on both, `diff` of everything after the frontmatter =
0 lines). They differ only in `source_url`, `page`, and `scraped_at`; **their
`content_sha256` frontmatter values are equal**, and a corpus-wide `content_sha256` duplicate
scan finds **this pair and no other**.

Cause: tIR is a single-chapter product, so dndbeyond serves the whole book at both the book root
URL (`/sources/dnd/tir`) and the chapter URL (`/sources/dnd/tir/the-illrigger-revised`). Every
other book's root file is a TOC.

**Cost if unhandled: every MCDM entity is double-counted** — 8 spells, 5 stat blocks, 2 magic
items, 1 class, 3 subclasses. **Detection is free** (`content_sha256`). → **decision D1.**

### 7.2 Spell name collisions — 32 distinct names, 19 of them cross-edition

528 entries / 496 distinct names ⇒ **32 duplicated names.** Decomposed (derived by joining each
duplicate's files to their frontmatter `edition`, then partitioning; the three buckets sum
8 + 19 + 5 = 32, checked):

| bucket | n | nature | risk |
|---|---|---|---|
| MCDM self-duplicate | 8 | §7.1 file pair | **mechanical**, kill with the hash |
| **PHB 2024 ↔ XGtE (5.0)** | **10** | Charm Monster, Dragon's Breath, Ice Knife, Mind Spike, Steel Wind Strike, Synaptic Static, Thunderclap, Toll the Dead, Vitriolic Sphere, Word of Radiance | **edition collision** |
| **PHB 2024 ↔ TCoE (5.0)** | **9** | Mind Sliver, Summon Aberration/Beast/Celestial/Construct/Elemental/Fey/Fiend/Undead | **edition collision** |
| SCAG ↔ TCoE (both 5.0) | 4 | Booming Blade, Green-Flame Blade, Lightning Lure, Sword Burst | reprint |
| ERftLW ↔ XGtE (both 5.0) | 1 | Gust | reprint |

**Level and school agree in all 32 pairs — and that is exactly what makes this dangerous.** A
dedup keyed on `(name, level, school)` would silently merge two different rulesets. **The rules
text materially differs.** Receipts:

*Charm Monster* — PHB `spell-descriptions.md:927` vs XGtE `spells.md:830`:
> 2024: *"On a failed save, the target has the **Charmed** condition until the spell ends or
> until **you or your allies damage it**"* + `***Using a Higher-Level Spell Slot.***`
> 2014: *"it is charmed by you until the spell ends or until **you or your companions do
> anything harmful to it**"* + `At Higher Levels.`

Different trigger (damage vs *anything harmful*), different rider heading, different condition
capitalisation. Same name, same level 4, same Enchantment.

*Summon Beast* — PHB `:6797` vs TCoE `magical-miscellany.md:288`: 2024 says
`**Bestial Spirit** stat block` / `0 Hit Points` / `your allies`; 2014 says `Bestial Spirit stat
block` / `0 hit points` / `your companions`, and the material component reads `worth 200+ GP`
vs `worth at least 200 gp`.

**Critically, the class attribution differs too:** PHB's Summon Beast descriptor says
`(Druid, Ranger)`; TCoE's table row says `Druid, Ranger` — those agree, but TCoE's Summon Fey
says `Druid, Ranger, Warlock, Wizard` where PHB's says `(Druid, Ranger, Warlock, Wizard)` — a
merge that picks the wrong side on a spell where they *do* diverge would produce a wrong answer
to exactly the class-availability queries in §6. → **decision D2. `edition` in frontmatter is
already sufficient to key this; the question is product policy, not extraction.**

### 7.3 Stat-block name collisions — 69 names, 64 spanning >1 file

667 entries / 596 distinct. Buckets:

- **~48 intra-Core reprints, `Core/mm-2024/animals.md` ↔ `Core/phb-2024/creature-stat-blocks.md`**
  — Ape, Badger, Bat, Black Bear, Boar, Brown Bear, Camel, Cat, Crab, Crocodile, Dire Wolf,
  Draft Horse, Elephant, Elk, Frog, Giant Badger/Crab/Goat/Seahorse/Spider/Weasel, Goat, Hawk,
  Lion, Lizard, Mastiff, Mule, Octopus, Owl, Panther, Pony, Rat, Raven, Reef Shark, Riding
  Horse, Scorpion, Spider, Tiger, Venomous Snake, Warhorse, Weasel, Wolf, + Imp, Pseudodragon,
  Quasit, Skeleton, Slaad Tadpole, Sphinx of Wonder, Sprite, Zombie. **Same edition, identical
  meta lines** — genuinely one creature printed twice. Low semantic risk, but a naive count says
  667 monsters when the truth is nearer 596.
- **~9 cross-edition summon blocks**, PHB `spell-descriptions.md` (2024) ↔ TCoE
  `magical-miscellany.md` (2014): Aberrant/Bestial/Celestial/Construct/Elemental/Fey/Fiendish/
  Undead Spirit. Same hazard shape as §7.2.
- **2 artificer companions in THREE books each**: `Steel Defender` (EFotA `the-artificer.md:720`
  [2024] · ERftLW `character-creation-class-artificer.md:627` [2014] · TCoE `artificer.md:788`
  [2014]) and `Homunculus Servant` (same three). **Three versions, two editions.**
- **3 TCoE ranger companions** (`Beast of the Land/Sea/Sky`) colliding with PHB 2024.
- **5 MCDM self-duplicates** (§7.1).

### 7.4 Magic item name collisions — only 4, all benign

`Bloodsbane` and `True Name` (MCDM self-duplicate, §7.1); `Dread Helm`
(`magic-items-a-z.md:1258` ↔ `xgte/common-magic-items.md:104`) and `Talking Doll`
(`:3856` ↔ `:285`) — DMG-2024 reprints of XGtE commons, **identical descriptors in both**.
Magic items are effectively collision-free.

---

## 8. Hazards, ranked by what they would silently get wrong

**H1 — Ritual is in the Casting Time value, not the descriptor (§3.1).** An extractor that
looks for `(Ritual)` in the descriptor returns **0 rituals from PHB** and answers target query
(b) with an empty set. Silent, plausible-looking, completely wrong. *Instrument:* the §6.4
two-source diff catches it immediately — Source B's `Special` column is independent.

**H2 — 2014 vs 2024 same-name entities: 19 spell pairs + ~12 stat-block groups (§7.2/§7.3).**
Same name, same level, same school, **different rules text and sometimes different class
availability**. `edition:` in frontmatter defuses it *if the design uses it*. → D2.

**H3 — The `MCDM/tir` byte-identical file pair (§7.1)** double-counts every MCDM entity.
Free to detect via `content_sha256`. → D1.

**H4 — Heading depth is not entity type, and it costs a real false entity today.** In
`Core/phb-2024/character-classes-continued.md:550`, `#### Oath of the Ancients Spells` is a
**spell-table caption at the same `####` level as the subclass `#### Oath of the Ancients`
(line 530)**. A depth-based subclass rule yields **49 subclasses; the truth is 48** (12
classes × 4). I enumerated all H4s inside all twelve `### <Class> Subclasses` regions — **this
is the only instance**, but there are 70 `#### … Spells` captions in those two files, so the
pattern is one refactor away from producing more. *Fix:* require a subclass to be followed by
its `*<flavour>*` italic tagline, or exclude captions ending in ` Spells`.

**H5 — 2014-tier stat blocks are structurally degraded, three ways at once (§3.2).** Of the 68
`**Armor Class**` blocks:
- **52 (76%) have the monster name as a BARE PARAGRAPH, not a heading** (vs 598/599 = 99.8%
  headings in the 2024 dialect). E.g. `Belashyrra` at
  `Expanded/erftlw/friends-and-foes.md:207`. Not addressable by heading; needs the heuristic
  *"last non-blank paragraph before the meta line before `**Armor Class**`"*.
- **Ability scores collapsed from a table into a vertical run of one-token paragraphs** —
  `STR` ⏎⏎ `24 (+7)` ⏎⏎ `DEX` ⏎⏎ `21 (+5)` … (`friends-and-foes.md:217-240`). 69 occurrences
  of a bare `^STR$` line across 12 files (erftlw 40, tcoe 17, MCDM 10, xgte 1). The 2024 tier
  uses proper markdown tables throughout — **this is HTML→markdown conversion damage, not a
  book difference.**
- Different field vocabulary: `**Armor Class**`/`**Hit Points**`/`**Challenge**`/`**Damage
  Resistances**`/`**Condition Immunities**` vs 2024's `**AC**`/`**HP**`/`**CR**`/
  `**Resistances**`/`**Immunities**`. And 19 of 58 `**Challenge**` lines are
  `**Challenge** — **Proficiency Bonus (PB)** equals your bonus` (companion blocks, no CR).
→ **decision D3.**

**H6 — XGtE class-list names are case-mangled; an exact-string join loses 79% of its edges
silently (§4.3-ii).** 20/95 exact vs 95/95 normalised. And **the italics in those lists carry no
information** — 13 names appear both italicised and not.

**H7 — Cross-references have no markup and no links at all (§4).** Edge extraction must be
name-matching against an entity index, which makes H2/H3 upstream of edge correctness, not
parallel to it.

**H7b — …and bare-name matching over-matches, because entity names contain other entity
names.** This is H7's direct consequence and I found it while checking the §6.3 numbers, so it
is measured rather than hypothesised. Using word-boundary matching (`\bNAME\b` — i.e. already
the *careful* version, not naive substring):

- **11 of 391 PHB spell names occur inside another PHB spell name**: `Fireball` ⊂ *Delayed
  Blast Fireball* · `Heal` ⊂ *Mass Heal*, *Power Word Heal* · `Shield` ⊂ *Fire Shield*, *Shield
  of Faith* · `Invisibility` ⊂ *Greater Invisibility*, *See Invisibility* · `Cure Wounds` ⊂
  *Mass Cure Wounds* · `Healing Word` ⊂ *Mass Healing Word* · `Suggestion` ⊂ *Mass Suggestion* ·
  `Polymorph` ⊂ *True Polymorph* · `Resurrection` ⊂ *True Resurrection* · `Commune` ⊂ *Commune
  with Nature* · `Gate` ⊂ *Arcane Gate*.
- **77 of 596 stat-block names occur inside another stat-block name** — and the worst offenders
  are high-frequency words: `Knight` inside 7 (*Death Knight*, *Bone Knight*, …), `Cultist` 6,
  `Shadow` 6, `Vampire` 4, `Bandit` 3, `Priest` 3, `Skeleton` 3, `Spider` 3, `Wolf` 3.

**Consequence:** every mention of *Delayed Blast Fireball* also emits a false `Fireball` edge;
every *Death Knight* emits a false `Knight` edge. **The fix is longest-match-first over a
length-sorted name index, not `\b` anchoring** — `\b` does not help here, which is precisely
why this needed measuring rather than assuming. This is a small implementation rule, but it is
invisible if nobody names it, and it silently inflates the edge set for exactly the most common
entities.

*Instrument (pasted per brief-base §1 — I am read-only; run from the corpus root):*

```python
import re, pathlib
sd = pathlib.Path('Core/phb-2024/spell-descriptions.md').read_text().splitlines()
names = sorted({l[4:].strip() for l in sd if l.startswith('### ')})   # swap in any name set
for s in names:
    pat = re.compile(r'\b' + re.escape(s) + r'\b')
    hosts = [o for o in names if o != s and pat.search(o)]
    if hosts:
        print(f'{s!r} <- inside {hosts}')       # -> 11 rows for PHB spells, 77 for stat blocks
```

**H8 — Two ability tables per 2024 stat block, not one (§3.2).** An extractor taking the first
`| Ability | Score | Mod | Save |` table silently drops Int/Wis/Cha for all 599 blocks.

**H9 — Multi-rarity magic items (8 in DMG) and `Rarity Varies` (11)** break a single-rarity
field (§3.3).

**H10 — Minor/cosmetic:** `Expanded/xgte/xgte.md` has no H1 (only file, 140/141). The `***`
separator is not universal (368 for 391 spells in `spell-descriptions.md`; zero in
`magic-items-a-z.md`) — usable as a hint, not as a contract. Section labels inside stat blocks
(`Actions`, `Reactions`, …) are plain paragraphs and will look like body prose.

### 8.1 The one package question I did NOT evaluate

I specified no mechanism, so `Packages considered: none` is the honest line. But the lead's
extractor will immediately need YAML frontmatter parsing across 141 files. **I did not read the
API of `python-frontmatter` or `PyYAML` and therefore have no verdict to offer** — I am flagging
the decision point rather than leaving a silent gap. Note the frontmatter here is trivially
regular (12 flat scalar keys, no nesting, no lists), so "the package does the job" is very
likely and should be confirmed by reading, not assumed in either direction.

### 8.2 Structural facts only — no chunker designed

Per the brief, chunking is out of scope and I designed none. The facts above (entity boundaries,
`***` separators, heading depth instability, field-line grammars) are reported as structure, not
as a segmentation proposal.

---

## 9. What I did NOT check — so nobody inherits a false clear

Stating the bound of this survey explicitly, per the trust doctrine:

1. **I did not verify the 2014-dialect field coverage** the way I did the 2024 dialect. The 68
   `**Armor Class**` blocks got name-addressability and ability-table shape measured; I did NOT
   run a per-field completeness sweep over them.
2. **I did not enumerate entity types outside the seven I counted.** Backgrounds/species were
   counted for PHB 2024 only — SCAG `backgrounds.md` (49K) and `races-of-the-realms.md` (79K),
   ERftLW `character-creation.md` (88K), and XGtE `subclasses.md` (205K, the largest Expanded
   file) hold more of both and I did not count them. **XGtE's 205K subclass file is the single
   largest uncounted entity population in the corpus.**
3. **I did not check TCoE/XGtE subclass or optional-class-feature structure** beyond noting the
   `#### Expanded Spell List` headings (tcoe/warlock.md:188,269; scag/classes.md:864;
   xgte/subclasses.md:2629,2686) — those are subclass-granted bonus spell lists and are a
   *fourth* spell→class shape I did not parse.
4. **I did not validate that every `### X Spell List` table row's spell actually resolves to a
   detail entry** for the non-PHB books (I did prove it for XGtE 95/95 case-insensitively, and
   the PHB A/B diff proves it there by construction).
5. **Equipment, conditions, and the rules glossary** (`phb-2024/rules-glossary.md` 69K, 155
   `***` entries; `equipment.md` 59K, 107) are entity-shaped and uncounted.
6. **Every count here is over the 141 files present.** I verified the manifest matches disk
   exactly, so nothing is missing *relative to the scrape* — but whether the scrape itself
   covered every page of every book is not something this corpus can tell me, and I did not
   check it against dndbeyond.

---

## 10. Bottom line for the design lead

- **The corpus is in better shape than a typical scrape, and the PHB-2024 tier is genuinely
  graph-ready today.** All three target queries resolve, two of them from two independent
  sources that agree exactly (987/987 class edges, 21/21 and 14/14 on the target queries).
- **Frontmatter is the corpus's best asset**: 12 uniform keys × 141 files, `edition` +
  `tier` + `source_book` already present, `content_sha256` validated against a manifest that
  matches disk perfectly. Book/edition provenance is free; use it.
- **Build the A/B spell-list diff as a permanent build-time pin, not a one-off check.** It is
  the only mechanical instrument in this corpus that can catch a silently-wrong extractor, and
  it costs nothing because both sources already exist.
- **The three decisions the lead owns are D1/D2/D3** — the MCDM duplicate pair, the
  2014-vs-2024 policy, and whether the degraded 2014-tier stat blocks are in scope at all.
  None of them are extraction problems; all three are product-scope rulings.
- **The two sharpest traps are H1 and H7b**, because both fail *silently* and both look
  entirely plausible while doing it: H1 (ritual lives in the Casting Time value, not the
  descriptor) answers target query (b) with an empty set; H7b (entity names contain other
  entity names — 11 spells, 77 stat blocks) inflates the edge set for the most common entities,
  and `\b` anchoring does **not** fix it.
- **Three of my own counts were wrong before I re-derived them** (11-vs-12 frontmatter keys ·
  581-vs-599 stat blocks · 21-vs-19 cross-edition spell pairs), and in every case the wrong
  figure looked clean. Each is documented at the point it appears rather than quietly corrected.
  Treat any count in this report that does **not** carry its derivation as one I did not check.
