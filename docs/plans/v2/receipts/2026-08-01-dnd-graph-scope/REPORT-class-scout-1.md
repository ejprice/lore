<!-- ARCHIVED 2026-08-02: read-only Explore scout, graph-scope deep pass (class side — subclasses, features, the wild-shape chain).
     Spawned by the D&D slot-in planning session at fa12c11; corpus = dndlorescraper
     output, 2026-07-31 scrape. Extends (does not supersede) the 2026-08-01 scoping
     reports in ../2026-08-01-dnd-rag-scoping/. Every count carries its derivation. -->

# REPORT — corpus-scout-2: the CLASS side

**Scope + date:** the tree at `/home/ejprice/code/python/dndlorescraper/output`, measured 2026-08-01, same static snapshot as REPORT-corpus-scout-1 (frontmatter `scraped_at` 2026-07-31). Line numbers are stable for this snapshot only.

**Read first:** REPORT-corpus-scout-1 §2/§3/§4/§7/§8. I did not re-derive spells, spell↔class edges, stat blocks, magic items, or feats. Everything below is new ground, and the XGtE 205K subclass file — scout-1's stated bound — is now fully enumerated.

**Tooling honesty:** plain Bash/grep/awk + `python3 -c` (read-only, nothing written to disk). Every count below carries its derivation.

---

## 0. Headline

1. **The class side is five distinct heading grammars, not one.** PHB-2024, EFotA, XGtE, TCoE, SCAG, ERftLW and MCDM each nest classes/subclasses/features at *different depths with different level-marker conventions*. Heading depth is useless as an entity discriminator (this confirms and sharpens scout-1's §1.3 finding); the **descriptor line under the heading** is the discriminator in every dialect.
2. **134 subclass entries / 115 distinct names**, of which XGtE contributes 31 (previously uncounted). **16 name-collision groups**, 11 of them cross-edition — structurally identical to the spell hazard scout-1 called H2.
3. **Class features are first-class, structurally identifiable entities in every source**, and PHB-2024 gives them at **174 class + 241 subclass = 415** level-marked headings that cross-check 174/174 against an independent level-progression table. That is a **second free correctness oracle** of exactly the kind scout-1 recommended pinning for spells.
4. **The worked example resolves end-to-end and MECHANICALLY — for the 2024 edition only.** There is **no 2014 base Druid, no 2014 Wild Shape, and no 2014 Circle of the Moon anywhere in the corpus.** Both 2014 books that mention Circle of the Moon reference it as living in a book that was never scraped. Stated explicitly in §4.
5. Species and backgrounds **do** carry feature-like structure worth graphing — 47 named species traits and a 16/16 clean background→feat edge in PHB alone.

---

## 1. Classes → subclasses: the grammar of each source

### 1.1 The seven dialects, side by side

| source | edition | class heading | subclass-group heading | subclass heading | feature heading | how a feature's level is encoded |
|---|---|---|---|---|---|---|
| **PHB 2024** `character-classes{,-continued}.md` | 5.5 | `## Druid` | `### Druid Subclasses` | `#### Circle of the Moon` + italic tagline | `##### Level 3: Circle Forms` | **in the heading**, `Level N: ` prefix |
| **EFotA** `the-artificer.md` | 5.5 | `# The Artificer` (file H1) | `## Artificer Subclasses` | `### Alchemist` | `#### Level 3: Tools of the Trade` | **in the heading**, `Level N: ` prefix |
| **XGtE** `subclasses.md` | 5.0 | `## Druid` | `## Druid Circles` | `## Circle of Dreams` (**same depth as class!**) | `#### Balm of the Summer Court` | **prose first sentence** (`At 2nd level, …`) **+ a `#### <Subclass> Features` level table** |
| **TCoE** one file per class | 5.0 | `# Druid` (file H1) | `## Druid Circles` | `### Circle of Spores` | `#### Halo of Spores` | **italic descriptor line**, `*2nd-level Circle of Spores feature*` |
| **SCAG** `classes.md` | 5.0 | `## Druids` (**plural!**) | `### Primal Paths` | `### Path of the Battlerager` | `#### Battlerager Armor` | **prose first sentence** only |
| **ERftLW** `character-creation-class-artificer.md` | 5.0 | `# Chapter 1: Artificer` | `## Artificer Specialists` | `### Alchemist` | `#### Tool Proficiency` | **prose first sentence** only |
| **MCDM** `tir.md` | 5.5 | `## The Illrigger` (twice — lore + mechanical) | `## Diabolic Contracts` | `### Architect of Ruin` + italic tagline | `#### Asmodeus's Blessing` | **italic descriptor line**, `*3rd-Level Architect of Ruin Feature*` (Title Case — **a different dialect from TCoE's**) |

**The one structural fact that matters most:** in XGtE, a class name and a subclass name are *both* `## `. `## Druid` (:727), `## Druid Circles` (:788), `## Circle of Dreams` (:792) are indistinguishable by depth. Any depth-based rule fails on the corpus's largest Expanded file.

### 1.2 What identifies a subclass's parent class — per source

| source | parent-class carrier | grade |
|---|---|---|
| PHB 2024 | enclosing `### <Class> Subclasses` H3 region | MECHANICAL |
| EFotA | enclosing `## Artificer Subclasses` + file H1 | MECHANICAL |
| **XGtE** | **the first column header of the subclass's own level table: `\| Druid Level \| Feature \|`** — 31/31, class name literally in the header. Plus a redundant `## <Class>` ancestor, plus a **whole-book manifest table** (§1.4) | MECHANICAL, **three independent sources** |
| TCoE | file name + file H1 (`druid.md` → `# Druid`); redundantly the `*Nth-level <Subclass> feature*` descriptor names the subclass | MECHANICAL |
| SCAG | enclosing `## <Class>s` H2 — **plural form**, needs de-pluralising to join | MECHANICAL after normalisation |
| ERftLW | file name + `## Artificer Specialists` | MECHANICAL |
| MCDM | file H1 + `## Diabolic Contracts`; the `*Nth-Level <Subclass> Feature*` descriptor | MECHANICAL |

### 1.3 The subclass population — full census

```
134 subclass entries, 115 distinct names
(derivation: per-source rules below, run as one python3 -c over the tree;
 MCDM/tir/the-illrigger-revised.md excluded as the byte-identical duplicate of tir.md — scout-1 §7.1)
```

| source | n | derivation rule used |
|---|---|---|
| **PHB 2024** | **48** | `#### X` inside a `### <Class> Subclasses` region **whose line+2 is an italic tagline not beginning `*Prerequisite`**. Exactly 4 per class × 12. |
| **XGtE** | **31** | `## X` that owns a `#### X Features` heading before the next `## ` |
| **TCoE** | **30** | `### X` directly under a group `## ` in {Primal Paths, Bard Colleges, Divine Domains, Druid Circles, Martial Archetypes, Monastic Traditions, Sacred Oaths, Ranger Archetypes, Roguish Archetypes, Sorcerous Origins, Otherworldly Patrons, Arcane Traditions, Artificer Specialists} |
| **SCAG** | **12** | `### X` following a singular group `### ` heading, before the next `## ` |
| **EFotA** | **5** | `### X` under `## Artificer Subclasses` |
| **MCDM** | **5** | `### X` under `## Diabolic Contracts` |
| **ERftLW** | **3** | `### X` under `## Artificer Specialists` |

Per-class distribution: PHB **4/4/4/4/4/4/4/4/4/4/4/4** (all twelve). XGtE Barb 3, Bard 3, Cleric 2, Druid 2, Fighter 3, Monk 3, Paladin 2, Ranger 3, Rogue 4, Sorc 3, Warlock 2, Wiz 1. TCoE Artificer 4, Cleric 3, Druid 3, all others 2. SCAG Barb 2, Cleric 1, Fighter 1, Monk 2, Paladin 1, Rogue 2, Sorc 1, Warlock 1, Wiz 1.

**The PHB tagline rule is strictly better than scout-1 §8.4's region+depth rule.** The tagline scan returns 71 hits = 48 subclasses + 23 Eldritch Invocations carrying `*Prerequisite: …*` taglines; excluding the prereq form gives **48/48 with zero false positives**, so the `#### Oath of the Ancients Spells` false entity (scout-1 H4) never arises and you don't need the ad-hoc " Spells" suffix exclusion.

### 1.4 ⭐ XGtE ships a machine-readable subclass manifest — and nobody else does

`Expanded/xgte/subclasses.md:30`:

```
| Class | Subclass | Level Available | Description |
| Barbarian | Path of the Ancestral Guardian | 3rd | Calls on the spirits of honored ancestors to protect others |
| Druid     | Circle of Dreams              | 2nd | Mends wounds, guards the weary, and strides through dreams |
…31 rows
```

Verified: **31/31 rows join to an `## ` heading in the same file; 29/31 join to a `#### X Features` anchor** — the 2 misses are `The Celestial` / `The Hexblade`, whose anchors drop the leading "The" (`#### Celestial Features` :2620, `#### Hexblade Features` :2677). This is a **free two-source correctness pin for class↔subclass in XGtE**, and it also gives `Level Available` (21 at 3rd, 7 at 1st, 3 at 2nd) which nothing else in the 2014 tier states as a field.

`grep -rn '^| Class | Subclass' --include='*.md' .` → **one hit corpus-wide**. No other book has this.

---

## 2. Class features: structure, containment, and level

### 2.1 The 2024 dialect is the cleanest thing in the corpus after magic items

`Core/phb-2024/character-classes.md`, Druid, verbatim skeleton:

```
1437  ## Druid
1439  ### Core Druid Traits          <- 8-row 2-column attribute table
1458  #### Becoming a Druid...       <- multiclass rules
1474  ### Druid Features             <- the 20-row level-progression TABLE
1500  #### Level 1: Spellcasting
1538  #### Level 2: Wild Shape
1552  ##### Beast Shapes             <- a TABLE CAPTION at the same depth as subclass features
1576  #### Level 3: Druid Subclass
1624  ### Druid Spell List
1813  ### Druid Subclasses
1894  #### Circle of the Moon
1902  ##### Level 3: Circle Forms
```

Counts (`grep -c` over the two PHB class files):
- `^#### Level \d+: ` → **174** class features
- `^##### Level \d+: ` → **241** subclass features
- `^### Core \w+ Traits$` / `### \w+ Class Features$` / `### \w+ Features$` / `### \w+ Subclasses$` → **12 / 12 / 12 / 12**
- `### \w+ Spell List$` → **8** (the 8 spellcasting classes; scout-1 §4.3-i)
- EFotA adds **13 + 33 = 46** more `Level N: ` features at H3/H4.
- **`^#+ Level \d+: ` corpus-wide = 461** (PHB 415 + EFotA 46). Zero other files use this form.

**Named sub-features inside a feature body** use the bold-run construct `***Known Forms.***` — 140 + 135 = **275** in the two PHB class files, **4,923 corpus-wide** (also used for monster traits, magic-item riders, species traits, feat clauses). It is the generic "named sub-entity" carrier and is *not* class-specific.

### 2.2 ⭐ Feature-gained-at-level exists TWICE in PHB 2024, and the two sources agree 174/174

**Source A** — the heading: `#### Level 2: Wild Shape` → `(Druid, 2, "Wild Shape")`.
**Source B** — the `### <Class> Features` table's `Class Features` column: row `| 2 | +2 | Wild Shape, Wild Companion | … |` → `(Druid, 2, "Wild Shape")`, `(Druid, 2, "Wild Companion")`.

Derivation (one `python3 -c`, both files, splitting the cell on commas):

```
12 tables · 240 level rows (12 × 20, exact) · 258 Class-Features cells
A (headings) = 174 ; B (table) = 258
A − B after stripping trailing parentheticals:  EMPTY   (174/174 subset)
B − A residue: Subclass feature 35 · Ability Score Improvement 39 ·
               Mystic Arcanum 3 · Expertise 2 · Indomitable 2 · Metamagic 2 · Action Surge 1
```

The B−A residue is entirely legitimate — *repeat grants of an already-headed feature at later levels*, plus the 35 `Subclass feature` placeholders. **Before normalisation there were exactly 3 mismatches**, all parenthetical qualifiers the table adds and the heading omits:

| heading | table cell |
|---|---|
| `#### Level 2: Action Surge` | `Action Surge (one use)` |
| `#### Level 9: Indomitable` | `Indomitable (one use)` |
| `#### Level 11: Mystic Arcanum` | `Mystic Arcanum (level 6 spell)` |

**Recommendation: pin this diff the way scout-1 recommended pinning the spell A/B diff.** It costs nothing, both sources already exist, and it will catch a silently-broken heading parser or a broken table parser immediately.

### 2.3 🔴 HAZARD — for 7 of 12 classes the markdown table header row is a merged span, and the real column names are the first body row

`Core/phb-2024/character-classes.md:1476-1479` (Druid):

```
1476  |  | | | | | | ——Spell Slots per Spell Level—— | | | | | | | | |     <- GFM header row
1477  | --- | --- | --- | … |                                              <- separator
1478  | Level | Proficiency Bonus | Class Features | Wild Shape | … |      <- the ACTUAL column names, as a BODY row
1479  | 1 | +2 | Spellcasting, Druidic, Primal Order | … |                 <- first real data row
```

`tables whose GFM header row is a merged SPAN row: 7 of 12` (Bard, Cleric, Druid, Paladin, Ranger, Sorcerer, Wizard — every class with a multi-level spell-slot block).

**A conformant GFM table parser will name those columns `''` and hand you "Level / Proficiency Bonus / Class Features / …" as data.** My own first pass silently returned **233 level rows instead of 240** because of this — the wrong figure looked perfectly clean (19-vs-20 rows reads as "the table just starts at level 2"). Same failure mode as scout-1's 11-vs-12 frontmatter keys.

### 2.4 The 2014 dialects

**TCoE — the best 2014 shape, and the only one with an explicit feature descriptor.** Every feature body opens with an italic line:

```
Expanded/tcoe/druid.md:126     *2nd-level Circle of Spores feature*
Expanded/tcoe/druid.md:179     *2nd-level Circle of the Stars feature*
Expanded/tcoe/cleric.md:74     *8th-level cleric feature, which replaces the Divine Strike or Potent Spellcasting feature*
```

`grep -rcE '^\*[0-9]+(st|nd|rd|th)-level .* feature\*$'` → **247 across 14 TCoE files.** The descriptor carries **level + owner in one regex-able line**. Owner case is the discriminator: **34 Title-Case owners** (30 subclasses + 3 sidekick classes + `Beast Master`) vs **13 lower-case owners** (the 13 base classes, i.e. optional class features).

**MCDM — same idea, different casing.** `*3rd-Level Architect of Ruin Feature*` (`MCDM/tir/tir.md:589`). `grep -rcE '^\*[0-9]+(st|nd|rd|th)-Level [^*]+ Feature\*$'` → **46 per file × 2 files = 92**; owners: Illrigger 14, Architect of Ruin 7, Hellspeaker 7, Painkiller 6, Sanguine Knight 6, Shadowmaster 6.

**XGtE / SCAG / ERftLW — level lives in the first sentence of the body, nowhere else.**

```
Expanded/xgte/subclasses.md:810   At 2nd level, you become imbued with the blessings of the Summer Court…
Expanded/xgte/subclasses.md:826   Starting at 10th level, you can use the hidden, magical pathways…
Expanded/scag/classes.md:46       When you choose this path at 3rd level, you gain the ability to use spiked armor…
Expanded/erftlw/…-artificer.md:463  When you adopt this specialization at 3rd level, you gain proficiency…
```

Measured coverage, XGtE subclass regions only (feature headings after the `#### X Features` anchor): **156 / 172 = 90.7%** carry an ordinal level marker within 7 lines. **All 16 misses are spell-granting captions or option groups** — `#### Domain Spells` ×2, `#### <X> Spells` ×7, `#### Oath Spells` ×2, `#### Expanded Spell List` ×2, `#### <X> Expanded Spells` ×2, `#### Arcane Shot Options` ×1 — i.e. features whose level lives in an adjacent *table* instead. Excluding them, coverage is effectively 100%.

Opening-phrase distribution corpus-wide (`grep -rhoE '^[A-Z][A-Za-z ,’]{0,60}\b[0-9]+(st|nd|rd|th) level\b' Expanded/`):

```
126  At Nth level                              3  When you take this oath at Nth level
 92  Starting at Nth level                     3  When you adopt this specialization at Nth level
 16  Beginning at Nth level                    3  Starting when you choose this tradition at Nth level
  9  When you choose this archetype at Nth level   2  When you choose this domain at Nth level
  7  When you reach Nth level                  … ~10 more one-offs
```

**GRAMMAR grade, not MECHANICAL** — a designed phrase list gets you ~95%, but you must filter false positives, because `of Nth level` in the same sentence shape means *spell* level (`When you cast any spell of 1st level`, `You also learn an additional spell of 2nd level`). Confusing spell level with class level here would silently mis-gate features.

### 2.5 Feature ≠ heading depth, even inside one source

`Core/phb-2024/character-classes.md:2188-2312`, Battle Master:

```
2194  ##### Level 3: Combat Superiority      <- a subclass FEATURE
2230  ##### Maneuver Options                 <- a group caption
2234  ##### Ambush                           <- a MANEUVER (sub-option), same depth
…     20 maneuvers total, all at #####
```

The `Level N: ` prefix is the only thing separating a subclass feature from a sub-option at the same depth. Same for `##### Beast Shapes` (:1552, a table caption) and `##### Circle of the Moon Spells` (:1918, a table caption) sitting among `##### Level 3: Circle Forms`.

---

## 3. Sub-option families (a distinct entity class, not features)

Several features grant a *choice from a named menu*. These menus are entity populations in their own right and they are **not** in scout-1's taxonomy.

| family | count | derivation |
|---|---|---|
| Eldritch Invocations (PHB 2024) | **28** | `#### ` under `### Eldritch Invocation Options`, `character-classes-continued.md:2326` |
| Eldritch Invocations (XGtE) | **14** | `#### ` under `## Eldritch Invocations`, `subclasses.md:2732` |
| Eldritch Invocations (TCoE) | **8** | `#### ` under `### Eldritch Invocation Options`, `warlock.md:108` |
| Metamagic Options (PHB 2024) | **10** | `##### ` under `#### Metamagic Options`, `character-classes-continued.md:1699` |
| Battle Master Maneuvers (PHB 2024) | **20** | `##### ` after `##### Maneuver Options`, `character-classes.md:2230-2312` |
| Maneuver Options (TCoE) | **7** | `### ` under `## Maneuver Options`, `fighter.md:65` |
| Artificer Infusions (TCoE) | **16** | `### ` under `## Artificer Infusions`, `artificer.md:871` |
| Artificer Infusions (ERftLW) | **11** | `### ` under `## Artificer Infusions`, `…-artificer.md:704` |
| Sidekick classes (TCoE) | **3** | Expert / Spellcaster / Warrior, `### ` under `## Sidekicks`, `dungeon-masters-tools.md:112` |
| Battle Master *Builds* (TCoE) | **12** | `### ` under `## Battle Master Builds`, `fighter.md:260` — **advice, not mechanics; a trap for any "H3-under-H2" subclass rule** |

**23 of the 28 PHB invocations carry an extractable prerequisite** in their italic tagline: `*Prerequisite: Level 5+ Warlock, Pact of the Blade Invocation*` (`character-classes-continued.md:5374` counting from file start). That yields an invocation→invocation dependency edge and an invocation→level gate, both MECHANICAL.

---

## 4. ⭐ THE WORKED EXAMPLE — "What can my level 4 Moon Druid wild shape into?"

### 4.1 Edition inventory first — the answer that matters most

**There is exactly one Druid class, one Wild Shape feature, and one Circle of the Moon in this corpus, and all three are 2024 (PHB, `edition: '5.5'`).**

```
grep -rn 'Circle of the Moon' --include='*.md' .    ->  11 hits, 5 files
   DEFINITIONAL: Core/phb-2024/character-classes.md  (:1578 :1815 :1894 :1898 :1912 :1918)
   REFERENCE ONLY, 2014 books pointing at a book that was never scraped:
     Expanded/xgte/subclasses.md:904
     Expanded/scag/classes.md:281, :289
     Expanded/erftlw/khorvaire-gazeteer.md:795

grep -rc 'Wild Shape\|wild shape' --include='*.md' .  ->  only 4 files
   Core/phb-2024/character-classes.md 24 · Expanded/tcoe/druid.md 5
   Expanded/xgte/subclasses.md 4 · Core/phb-2024/rules-glossary.md 1

grep -rn 'Circle Forms' --include='*.md' .          ->  3 hits
   Core/phb-2024/character-classes.md:1902, :1927   (definitions)
   Expanded/xgte/subclasses.md:904                  (dangling reference)

grep -rn '^#\+ Class Features$' --include='*.md' .  ->  base-class definitions in the corpus:
   tcoe/artificer.md:111 · erftlw/…-artificer.md:54 · MCDM/tir/tir.md:290 (+ its duplicate)
   (+ the 12 PHB-2024 classes, which use '### <Class> Class Features' instead)
```

⇒ **The corpus holds the 2024 PHB for all twelve core classes and NO 2014 PHB at all.** The 2014-era books present are *supplements* — they add subclasses and optional features to a 2014 base that is not in the corpus. **Ask the 2014 version of this question and the corpus cannot answer it**, and worse, it will *look* like it can, because `Expanded/xgte/subclasses.md:904` says:

> "The tables include all the individual beasts that are eligible for Wild Shape (up to a challenge rating of 1) or the Circle Forms feature of the Circle of the Moon (up to a challenge rating of 6)."

That sentence names both features and both CR ceilings but is a **pointer, not a rule**: the level→CR *function* it refers to (2014's "as high as your druid level divided by 3, rounded down, starting at 6th level") appears nowhere in the corpus. `Expanded/xgte/subclasses.md:896` says so outright: *"The Wild Shape feature **in the Player's Handbook** lets you transform into a beast that you've seen… you must abide by the limitations in the Beast Shapes table **in that book**."*

**This is the single sharpest retrieval hazard on the class side.** A RAG system that retrieves XGtE :904 for "moon druid wild shape CR" returns a fluent, authoritative-sounding, *2014* sentence that answers a different question than the one asked, and there is no 2014 rule text to correct it. Grade: **PROSE / UNANSWERABLE for 2014.**

### 4.2 The 2024 trace, quoted verbatim

**Step 1 — the class.** `Core/phb-2024/character-classes.md:1437` `## Druid`.

**Step 2 — the subclass is gained.** `:1576` `#### Level 3: Druid Subclass`, body at `:1578`:

> "You gain a Druid subclass of your choice. The Circle of the Land, Circle of the Moon, Circle of the Sea, and Circle of the Stars subclasses are detailed after this class's description. **A subclass is a specialization that grants you features at certain Druid levels. For the rest of your career, you gain each of your subclass's features that are of your Druid level or lower.**"

That last sentence is the *only* statement in the corpus of the general rule "you have every subclass feature at or below your level". It is prose, it appears once per class, and it is the semantic contract behind every subclass-feature-at-level edge.

**Step 3 — the base feature.** `:1538` `#### Level 2: Wild Shape`. Load-bearing paragraphs:

`:1546` —
> "***Known Forms.*** You know four Beast forms for this feature, chosen from among **Beast stat blocks that have a maximum Challenge Rating of 1/4 and that lack a Fly Speed** (see appendix B for stat block options). The Rat, Riding Horse, Spider, and Wolf are recommended. Whenever you finish a Long Rest, you can replace one of your known forms with another eligible form."

`:1548` —
> "When you reach certain Druid levels, your number of known forms and the maximum Challenge Rating for those forms increases, as shown in the Beast Shapes table. In addition, **starting at level 8, you can adopt a form that has a Fly Speed**."

`:1552-1558` — `##### Beast Shapes`:

| Druid Level | Known Forms | Max CR | Fly Speed |
| --- | --- | --- | --- |
| 2 | 4 | 1/4 | No |
| **4** | **6** | **1/2** | **No** |
| 8 | 8 | 1 | Yes |

**Step 4 — the subclass.** `:1894` `#### Circle of the Moon`, tagline `:1896` `*Adopt Animal Forms to Guard the Wilds*`. Its first feature, `:1902` `##### Level 3: Circle Forms`:

`:1904` —
> "You can channel lunar magic when you assume a Wild Shape form, granting you the benefits below."

`:1906` — **the load-bearing sentence, the level→CR function:**
> "***Challenge Rating.*** **The maximum Challenge Rating for the form equals your Druid level divided by 3 (round down).**"

`:1908` —
> "***Armor Class.*** Until you leave the form, your AC equals 13 plus your Wisdom modifier if that total is higher than the Beast's AC."

`:1910` —
> "***Temporary Hit Points.*** You gain a number of Temporary Hit Points equal to three times your Druid level."

**Step 5 — resolve.** Level 4 ÷ 3 = 1.33 → **Max CR 1** (Circle Forms overrides the Beast Shapes `Max CR` of 1/2). **Known Forms stays 6** and **Fly Speed stays No** (Circle Forms says nothing about either; `:1548` gates flight at level 8). Type is still Beast (`:1540` "shape-shift into a **Beast** form").

**Step 6 — enumerate the eligible creatures.** `:1546` points to appendix B = `Core/phb-2024/creature-stat-blocks.md` (`# Appendix B: Creature Stat Blocks`, stat blocks at **`## `** — a *third* depth for stat blocks, vs MM's `### `), plus `:1550` "you may look in the **Monster Manual** or elsewhere". Derived from the meta line + `**Speed**` + `**CR**` of every `**AC**` block in `Core/mm-2024/animals.md` + `Core/phb-2024/creature-stat-blocks.md`:

```
147 AC blocks in the two files; 134 whose meta line contains 'Beast'
filter: CR <= 1 AND 'Fly' not in the **Speed** line   ->  56 distinct names
```

> Ape · Baboon · Badger · Black Bear · Boar · Brown Bear · Camel · Cat · Constrictor Snake · Crab · Crocodile · Deer · Dire Wolf · Draft Horse · Elk · Frog · Giant Badger · Giant Centipede · Giant Crab · Giant Fire Beetle · Giant Frog · Giant Goat · Giant Hyena · Giant Lizard · Giant Octopus · Giant Rat · Giant Seahorse · Giant Spider · Giant Toad · Giant Venomous Snake · Giant Weasel · Giant Wolf Spider · Goat · Hyena · Jackal · Lion · Lizard · Mastiff · Mule · Octopus · Panther · Piranha · Pony · Rat · Reef Shark · Riding Horse · Scorpion · Seahorse · Spider · Swarm of Piranhas · Swarm of Rats · Tiger · Venomous Snake · Warhorse · Weasel · Wolf

Excluded by the Fly Speed clause (13, all CR ≤ 1): Bat · Blood Hawk · Eagle · Giant Bat · Giant Wasp · Hawk · Owl · Pteranodon · Raven · Swarm of Bats · Swarm of Insects · Swarm of Ravens · Vulture.

**A third, cheaper route exists and cross-checks:** `Core/mm-2024/monster-lists.md` (`# Appendix B: Monster Lists`) has `### Beast` (:445) and `### CR 1` (:1797) as bare one-name-per-paragraph lists. Verified: **the 91 names under `### Beast` join 91/91 to actual stat-block headings** in `animals.md` + PHB appendix B. Intersecting `### Beast` with `### CR 0 ∪ 1/8 ∪ 1/4 ∪ 1/2 ∪ 1` gives the same answer without parsing a single stat block.

### 4.3 What the query needs that the corpus never states

Three things must be *inferred*, not read:

1. **Circle Forms overrides only the `Max CR` column** of Beast Shapes. The corpus never says "this replaces". It says "granting you the benefits below" (`:1904`) and then re-states a maximum CR. A reader infers override; a machine must be told.
2. **Fly Speed is still gated at level 8** even for a Moon Druid, because Circle Forms is silent on it. Silence-means-unchanged is a rules convention, not corpus text.
3. **Swarms.** `Swarm of Rats` has meta `Medium Swarm of Tiny Beasts, Unaligned` and CR 1/4. Whether a swarm is a legal "Beast form" is not addressed anywhere in the corpus. My 56-name list includes 2 swarms; a rules lawyer would exclude them.

⇒ **Extraction of the pieces: MECHANICAL. Composition of the answer: PROSE.**

---

## 5. RELATIONSHIP CATALOG

Applying the stated dividing line — *both ends have identity, attributes and inbound questions ⇒ EDGE; one scalar on one entity ⇒ FIELD.*

| # | relationship | verdict | evidence (file : heading/line) | mult. | count + derivation | grade | hazards |
|---|---|---|---|---|---|---|---|
| **R1** | **subclass —specialises→ class** | **EDGE** | `character-classes.md:1894 #### Circle of the Moon` inside `:1813 ### Druid Subclasses` · `xgte/subclasses.md:30` manifest row `\| Druid \| Circle of Dreams \| 2nd \|` · `tcoe/druid.md:96 ### Circle of Spores` under `:92 ## Druid Circles` | N:1 | **134** entries / **115** distinct names. `python3 -c` per-source rules of §1.3 | **MECHANICAL** all 7 sources | 7 dialects; XGtE class & subclass share `## `; SCAG class headings PLURAL (`## Druids`); **16 cross-source name collisions** (§6.1); MCDM duplicate file doubles 5 subclasses |
| **R2** | class —grants-subclass-at→ level | **FIELD on R1** (one integer per class/edition) | `#### Level 3: <Class> Subclass` ×12/12 PHB · `xgte:30` `Level Available` column · `tcoe/druid.md:94` "At 2nd level, a druid gains the Druid Circle feature" | 1:1 | PHB **12/12 = level 3**; XGtE per-subclass: 21×3rd, 7×1st, 3×2nd | MECHANICAL (PHB, XGtE) · GRAMMAR (TCoE/SCAG prose) | **cross-edition divergence is the point**: Druid subclass at 3 in 2024, at 2 in 2014 — merging editions corrupts it |
| **R3** | **class feature —belongs-to→ class** | **EDGE** | `character-classes.md:1538 #### Level 2: Wild Shape` under `:1437 ## Druid` | N:1 | **174** PHB + **13** EFotA = 187 headed; **258** table cells incl. repeats. `grep -c '^#### Level [0-9]\+: '` ×2 files; table cells via python | **MECHANICAL** | 2014 sources have no headed class-feature list except TCoE optional features (**44**, lower-case descriptor) |
| **R4** | **subclass feature —belongs-to→ subclass** | **EDGE** | `character-classes.md:1902 ##### Level 3: Circle Forms` under `:1894` · `tcoe/druid.md:128 *2nd-level Circle of Spores feature*` · `tir.md:589 *3rd-Level Architect of Ruin Feature*` | N:1 | **241** PHB + **33** EFotA (heading) · **~203** TCoE Title-Case descriptors (247 total − 44 lower-case) · **92** MCDM (46 ×2 files) · **172** XGtE (H4 after the Features anchor) · SCAG/ERftLW **UNCOUNTED at entity level** (H4 mixes features with restrictions/lore/captions) | **MECHANICAL** PHB/EFotA/TCoE/MCDM · **GRAMMAR** XGtE · **PROSE** SCAG/ERftLW | TCoE descriptor name ≠ heading name (§6.2); XGtE anchor drops "The" |
| **R5** | **feature —gained-at→ level** | **FIELD on R3/R4** (scalar per feature) — but see note | heading `Level 2: ` · `\| 2 \| +2 \| Wild Shape, Wild Companion \|` (`:1480`) · `*2nd-level … feature*` · "At 2nd level," | 1:1 (mostly) | PHB **174/174** two-source-clean after stripping trailing parentheticals; table has **240** rows / **258** cells. XGtE **156/172 = 90.7%** prose coverage | **MECHANICAL** 2024/TCoE/MCDM · **GRAMMAR** XGtE/SCAG/ERftLW | ⚠ **not always 1:1** — `Ability Score Improvement` recurs 39×, `Mystic Arcanum` 3×, `Improved Brutal Strike` at 13 *and* 17. Model as a multi-valued field or a `granted_at` edge with a level property |
| **R6** | class —grants-subclass-feature-at→ level | **FIELD** (a level list per class) | `\| 6 \| +3 \| Subclass feature \|` `character-classes.md:1484` | 1:N | **35** placeholders; per class Barb 3, Bard 2, Cleric 2, Druid 3, Fighter 4, Monk 3, Pal 3, Ran 3, Rog 3, Sorc 3, Warl 3, Wiz 3 | MECHANICAL | the per-class variation is **real book data**, not a parse error — don't "fix" it to 3 |
| **R7** | **subclass —grants→ spell (at class level)** | **EDGE** | `character-classes.md:1918 ##### Circle of the Moon Spells` → `\| Druid Level \| Prepared Spells \|` `\| 3 \| Cure Wounds, Moonbeam, Starry Wisp \|` | N:M | **56** class-level-indexed tables / **263** level rows (`python3`, header `\| <Class> Level \| Spell(s)/Circle Spells/Prepared Spells \|`). Files: phb 23, xgte 7, efota 5, tcoe 11, erftlw 3, scag 2. **Plus 28** *spell-level*-indexed tables (`\| Spell Level \| Spells \|` — 24 dragonmarks + 4 warlock "Expanded Spell List") | **MECHANICAL** | **this is scout-1's flagged "fourth spell→class shape"** — now counted. Two incompatible axes (class level vs spell level). Spell names are lower-cased in every 2014 table (scout-1 H6 applies verbatim) |
| **R8** | class —has→ spell list | EDGE | 8 `### <Class> Spell List` sections | N:M | 987 rows — **scout-1 §4.3, not re-derived** | MECHANICAL | — |
| **R9** | class —has-attribute→ {primary ability, hit die, saves, armor, …} | **FIELD** | `### Core Druid Traits` table `:1439-1450` | 1:1 | **12/12** tables; keys **12/12** for 7 keys, **4/12** for `Tool Proficiencies` (genuinely optional) | MECHANICAL | ⚠ **EFotA uses BOLD keys** `\| **Primary Ability** \| Intelligence \|` (`the-artificer.md:30`) where PHB uses plain — exact-cell-match fails cross-book |
| **R10** | multiclass-into(class) —requires→ ability ≥ 13 | **FIELD** (derived from R9) | `creating-a-character.md:578` "you must have a score of at least 13 in the primary ability of the new class and your current classes" | — | one prose sentence; per-class values come from R9's `Primary Ability` | **PROSE** (the rule) over MECHANICAL (the data) | 2024 rule differs from 2014's per-class table, which is absent |
| **R11** | class —offers-multiclass-entry→ subset of traits | FIELD | `#### Becoming a Druid...` `:1458` → `##### As a Multiclass Druid` `:1465` | 1:1 | **12/12** (`grep -c '^#### Becoming a'`) | MECHANICAL | bullet-list prose body |
| **R12** | **optional feature —replaces→ feature** | **EDGE** (both ends are features) | `tcoe/ranger.md:132 *3rd-level ranger feature, which replaces the Primeval Awareness feature*` | N:1 | **6** — cleric.md:74, ranger.md:28/:50/:132/:156, ranger.md:328. `grep -rnE '^\*[0-9]+(st\|nd\|rd\|th)-level [^*]*replac[^*]*\*$'` | **MECHANICAL** | **the replaced feature is a 2014-PHB feature that does not exist in this corpus** — every one of these 6 edges dangles |
| **R13** | **invocation —requires→ {level, class, other invocation}** | **EDGE** (invocation→invocation) + FIELD (level) | `character-classes-continued.md` `#### Devouring Blade` → `*Prerequisite: Level 12+ Warlock, Thirsting Blade Invocation*` | N:M | **23 of 28** PHB invocations carry a prereq tagline (tagline scan, §1.3) | **MECHANICAL** | 5 invocations have no prereq line |
| **R14** | sub-option —chosen-from→ feature | **EDGE** | `##### Ambush` (:2234) under `##### Maneuver Options` (:2230) under `##### Level 3: Combat Superiority` (:2194) | N:1 | 28+14+8 invocations · 10 metamagic · 20+7 maneuvers · 16+11 infusions (§3) | MECHANICAL per family, GRAMMAR to generalise | **same heading depth as real features** — only the absent `Level N: ` prefix separates them |
| **R15** | **retainer/companion stat block —belongs-to→ subclass** | **EDGE** | `MCDM/tir/tir.md:807 ### Agent (Shadowmaster)`, `:861 ### Bloodletter (Sanguine Knight)`, `:915 ### Deceiver (Architect of Ruin)`, `:969 ### Schemer (Hellspeaker)` | 1:1 | **4** in MCDM (subclass name **inside the heading parenthetical**); PHB analogues (`Steel Defender`, `Beast of the Land/Sea/Sky`) are embedded in feature bodies — **UNCOUNTED** | MECHANICAL (MCDM) · PROSE (PHB/TCoE) | overlaps scout-1's `**CR** None` companion blocks |
| **R16** | subclass —restricted-to→ species | **EDGE** | `scag/classes.md:38 #### Restriction: Dwarves Only`, `:343 #### Restriction: Knighthood` | 1:1 | **2** (`grep -rn '^#\+ Restriction: '`) | MECHANICAL (the heading) · PROSE (the content) | SCAG only |
| **R17** | **background —grants→ feat** | **EDGE** | `character-origins.md:110 **Feat:** Magic Initiate (Cleric) (see chapter 5)` | N:1 | **16/16** PHB + **17/17** EFotA = 33. `grep -c '^\*\*Feat:\*\* '` | **MECHANICAL** | the parenthetical carries a **class parameter** (`Magic Initiate (Cleric\|Druid\|Wizard)`) → a background→feat→class chain; `(see chapter 5)` suffix must be stripped |
| **R18** | background —grants→ background feature | **EDGE** (2014 only) | `scag/backgrounds.md:38 ### Feature: Watcher's Eye` | 1:1 | **13** (`grep -rc '^#\+ Feature: '` → scag 12, erftlw 1) | MECHANICAL | 2024 backgrounds replaced this with R17 — **cross-edition structural divergence, not just naming** |
| **R19** | **species —has→ trait** | **EDGE** | `character-origins.md:455 #### Dwarf Traits` → `***Darkvision.*** …`, `***Dwarven Resilience.*** …` | N:1 | **47** bold-run traits under 10 PHB species (`grep -c '^\*\*\*[^*]*\.\*\*\*'` in `character-origins.md`); trait blocks corpus-wide: PHB 10, ERftLW 9, EFotA 5, SCAG 2, other 4 | **MECHANICAL** | ERftLW nests `#### Bugbear/Goblin/Hobgoblin Traits` under `### Racial Traits` under `## Goblinoids` — three-level species taxonomy |
| **R20** | species —has-attribute→ {creature type, size, speed} | FIELD | `**Creature Type:** Humanoid` / `**Size:** Medium` / `**Speed:** 30 feet` | 1:1 | **10/10** PHB, **5/5** EFotA, all three keys | MECHANICAL | — |
| **R21** | background —has-attribute→ {abilities, skills, tools, equipment} | FIELD | `**Ability Scores:** Intelligence, Wisdom, Charisma` | 1:1 | PHB **16/16** on all 5 keys; EFotA **17/17**; SCAG (2014) **12** Skill/Equipment, **10** Languages, **8** Tool | MECHANICAL | 2014 key set ≠ 2024 key set |
| **R22** | species —grants→ dragonmark spells | EDGE | `erftlw/character-creation-dragonmarks.md:146 #### Mark of Detection Spells` → `\| Spell Level \| Spells \|` | N:M | **24** tables (12 ERftLW 2014 + 12 EFotA 2024 — **the same 12 marks in both editions**) | MECHANICAL | full cross-edition duplication of one feature family |
| **R23** | class/subclass —has→ flavour roll table | FIELD (low value) | `xgte/subclasses.md:76 ### Personal Totems`, `:95 ### Tattoos`, `:112 ### Superstitions` | N:1 | **39** H3 in `xgte/subclasses.md` (3–4 per class × 12) | MECHANICAL | pure character-building colour; **but they are the ONLY `### ` headings in that file**, so an H3-based rule there harvests exclusively noise |

---

## 6. Hazards specific to the class side

**C1 — 🔴 Heading depth is meaningless across sources, and XGtE is the proof.** `## Druid` (class), `## Druid Circles` (group) and `## Circle of Dreams` (subclass) are all H2 in the same file. Meanwhile a subclass is H4 in PHB, H3 in TCoE/SCAG/EFotA/ERftLW/MCDM, H2 in XGtE. *Fix: key on the descriptor/anchor line, exactly as scout-1 §1.3 concluded for spells.*

**C2 — 🔴 Cross-source subclass name collisions: 16 groups, 19 duplicate entries (134 entries − 115 names).** Eleven are **cross-edition** and therefore mechanically different rulesets under one name:

| collision | sources | nature |
|---|---|---|
| Alchemist, Artillerist, Battle Smith | EFotA (5.5) · TCoE (5.0) · ERftLW (5.0) | **three versions, two editions** each |
| Armorer | EFotA (5.5) · TCoE (5.0) | cross-edition |
| College of Glamour, Path of the Zealot, Gloom Stalker | PHB-2024 (5.5) · XGtE (5.0) | cross-edition |
| Fey Wanderer, Oath of Glory, Psi Warrior, Soulknife | PHB-2024 (5.5) · TCoE (5.0) | cross-edition |
| Bladesinging | TCoE · SCAG (both 5.0) | same-edition reprint |
| Mastermind, Storm Sorcery, Swashbuckler, Way of the Sun Soul | XGtE · SCAG (both 5.0) | same-edition reprint |

Same shape as scout-1's spell hazard H2, same defusal: `edition` + `source_book` are already in frontmatter. **Same trap too** — parent class agrees in all 16 groups, so a dedup keyed on `(name, class)` merges two different rulesets silently.

**C3 — 🔴 Names disagree *within a single file*.** The subclass heading and the feature descriptor that points at it are not always the same string:

| file | heading | descriptor / anchor says |
|---|---|---|
| `tcoe/druid.md` | `### Circle of Stars` (:167) | `*2nd-level Circle of the Stars feature*` (:179 and 4 more) |
| `tcoe/warlock.md` | `### The Fathomless` (:176) | `*1st-level Fathomless feature*` |
| `tcoe/warlock.md` | `### The Genie` (:250) | `*1st-level Genie feature*` |
| `xgte/subclasses.md` | `## The Celestial` (:2614) | `#### Celestial Features` (:2620) |
| `xgte/subclasses.md` | `## The Hexblade` (:2669) | `#### Hexblade Features` (:2677) |

An exact-string join on subclass name loses these 5 R4 edge groups **silently**. Normalisation must handle both a leading `The ` and an inserted `the`. (Note the TCoE *prose* manifest at `druid.md:94` says "Circle of Stars", agreeing with the heading and disagreeing with the descriptor — there is no single right answer inside the file.)

**C4 — 🔴 The merged-span table header (§2.3).** 7 of 12 PHB class tables. Cost me 233-instead-of-240 rows on first pass, invisibly.

**C5 — 🟠 SCAG H3 is overloaded three ways.** Under `## Bards`: `### The Harpers` (lore org), `### Bardic Colleges` (group), and under it `#### College of Fochlucan` (a *lore* college with no mechanics). Under `## Druids`: `### Druid Circles` → `#### The Circle of Swords`, `#### The Emerald Enclave`, `#### The Moonshea Circles` — **all lore, zero mechanical Druid subclasses in SCAG.** Under `## Rangers`: `### Human Rangers`, `### Elf Rangers`… also lore. Only the H3 *following the singular-form group heading* is a real subclass. **PROSE-grade discrimination; my 12 is the count under that rule and I did not independently verify it against the printed book.**

**C6 — 🟠 TCoE `## Battle Master Builds` → 12 H3s** (Archer, Bodyguard, Brawler, …) that look exactly like subclasses to any "H3-under-H2" rule. They are build *advice*. Similarly `## Maneuver Options`, `## Artificer Infusions`, `## Beast Master Companions`.

**C7 — 🟠 Dangling references to a book that was never scraped.** All 6 R12 `replaces` edges, `Beast Master` as a TCoE descriptor owner, `Path of the Totem Warrior` (SCAG extends it), and the XGtE/SCAG Circle-of-the-Moon references point at 2014-PHB entities absent from the corpus. **Any completeness metric over the 2014 tier will look broken and won't be.**

**C8 — 🟠 Sub-options wear the same heading depth as features** (§2.5, R14). The `Level N: ` prefix in 2024 and the `*…feature*` descriptor in TCoE/MCDM separate them; **XGtE, SCAG and ERftLW have no separator at all**, and there `#### Arcane Shot Options` (a menu) sits among `#### Curving Shot` (a feature).

**C9 — 🟡 Ordinal-level false positives.** In 2014 prose, `Nth level` means *class* level after "At/Starting at/Beginning at" but *spell* level after "of" (`any spell of 1st level`, `an additional spell of 2nd level`). ~6 such lines in the phrase census. Confusing them mis-gates features.

**C10 — 🟡 MCDM's duplicate file inflates the class side too.** `tir.md` ≡ `the-illrigger-revised.md` (scout-1 §7.1) ⇒ **1 class, 5 subclasses, 46 features, 4 retainers each counted twice** if the hash isn't used. My §1.3 census excludes the duplicate; my §2.4 MCDM feature figure (92) does not — the real number is **46**.

---

## 7. Verdict on the two questions the lead will actually ask

**Is a class/subclass/feature graph buildable from this corpus?** Yes, and the 2024 tier is buildable *mechanically today*, with a second free correctness oracle (§2.2) alongside the spell one scout-1 found. The 2014 tier is buildable with a **per-source grammar** — six of them — and its feature→level edges are GRAMMAR-grade, not MECHANICAL.

**Which relationships are genuinely EDGES?** R1 (subclass→class), R3/R4 (feature→owner), R7 (subclass→spell), R12 (optional→replaced feature), R13 (invocation→invocation), R14 (sub-option→feature), R15 (retainer→subclass), R16 (subclass→species), R17 (background→feat), R18 (background→feature), R19 (species→trait), R22 (species→spell). Everything in the Core-Traits table (R9), the multiclass prerequisite (R10), background/species scalars (R20/R21) and the subclass-grant level (R2/R6) are **fields** — one scalar hanging off one entity, no inbound questions of their own.

**The one genuinely ambiguous case is R5, feature-gained-at-level.** It reads like a field, but the corpus grants the *same named feature at multiple levels* 47 times in PHB alone (Ability Score Improvement 39, Mystic Arcanum 3, Expertise 2, Indomitable 2, Metamagic 2, Action Surge 1) — so a single scalar loses data. Model it as a `granted_at` edge carrying a level property, or as a multi-valued field; a plain integer is wrong.

---

## 8. BOUNDS — what I did NOT look at

1. **I did not verify any subclass count against the printed books.** Every figure is a count of what this scrape contains under a rule I designed and stated. SCAG's 12 in particular rests on the PROSE discrimination of C5 and is the count I trust least.
2. **SCAG and ERftLW subclass *features* are UNCOUNTED at entity level.** Their H4s mix features, restrictions, lore, and table captions with no descriptor line to separate them (R4). I measured level-marker coverage (SCAG 53/84, ERftLW 22/33 over *all* H4s) but did not build a feature/non-feature classifier or count the real feature population.
3. **I did not enumerate PHB/TCoE companion & summon stat blocks embedded in feature bodies** (Steel Defender, Beast of the Land/Sea/Sky, Wildfire Spirit, Homunculus Servant). R15 is counted for MCDM only. These overlap scout-1's 18 `**CR** None` blocks but are not the same set and I did not reconcile them.
4. **I did not parse the XGtE "Learning Beast Shapes" environment tables** (`subclasses.md:894-1139`, 10 tables, `| CR | Beast | Fly/Swim |`) into edges, nor check whether their beast names resolve to MM-2024 stat blocks. They are **2014 MM** names in sentence case — the join is likely lossy in exactly the way scout-1's H6 describes, and I did not measure it.
5. **I did not check the DMG, MM, or the ERftLW/SCAG gazetteer files for class-side content.** Class-restricted magic items (`Requires Attunement by a Druid or Warlock`) are scout-1 §3.3 and I did not re-derive or extend them into a class→item edge count.
6. **I did not verify that every subclass-granted spell name in the 56+28 spell tables resolves to a spell entry.** Scout-1 left the same gap for the non-PHB class spell lists (its §9.4); mine is the subclass-level version of it and is equally open.
7. **The 56-name Wild Shape answer covers `mm-2024/animals.md` + `phb-2024/creature-stat-blocks.md` only.** `grep` says those are the only files with Beast meta lines in the Core tier, and the MM `### Beast` index joins 91/91 to headings in them, but I did not audit the MM letter files block-by-block for a Beast that the index missed.
8. **I did not evaluate whether the level-4 answer is *rules-correct*** — only that the corpus text supports the derivation. The swarm question (§4.3) is genuinely unresolved by the corpus.
9. **Feats, spells, magic items, stat blocks, conditions, equipment and the rules glossary are out of my scope** — see scout-1 §2 and its own §9 bounds, which I did not extend.