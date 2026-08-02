<!-- ARCHIVED 2026-08-02: read-only Explore scout, graph-scope deep pass (cross-cutting — items, feats, conditions/glossary, equipment, reference resolution).
     Spawned by the D&D slot-in planning session at fa12c11; corpus = dndlorescraper
     output, 2026-07-31 scrape. Extends (does not supersede) the 2026-08-01 scoping
     reports in ../2026-08-01-dnd-rag-scoping/. Every count carries its derivation. -->

# REPORT — corpus scout 2: cross-cutting entities & relationships

Corpus: `/home/ejprice/code/python/dndlorescraper/output` (141 md, ~3.1M). All commands below run **from that directory**. Every count carries its derivation. Prior report (`REPORT-corpus-scout-1.md`) read in full; I do not re-derive its figures.

---

## 0. Headline

The prior scout's "zero links, bare capitalized names" result is correct but **understates the problem in one direction and overstates it in another.**

- **Overstates**: there is far more *structured* relational data than "prose only" implies. Nine distinct table/field grammars carry edges mechanically (`| Spell | Charge Cost |`, `**Gear**`, `**At Will:**`, `**Feat:**`, `| Spell Level | Spells |`, `(Requires Attunement by …)`, weapon `Properties`/`Mastery` columns, `| Deity | Alignment | Domains | Symbol |`, `| Outer Plane | Alignment |`). These are MECHANICAL, not PROSE.
- **Understates**: the prior report's H7b (entity names nest inside other entity names) is the *smaller* half of the name-matching hazard. The larger half is that **the 2024 books Title-Case ordinary game vocabulary**, so ~8 spell names are indistinguishable from common rules terms in running text. `Light` matches 59× in `magic-items-a-z.md`; **~5 of those are the spell.** Longest-match-first over a 1,184-name unified index reduces it to 16 and *cannot* go lower, because `Resistance` the glossary term and `Resistance` the spell are the same string. **This is not fixable by a name index. It needs a verb/suffix cue.** Measured in §6.2.

**Also**: the corpus contains a **74-entry lore glossary** (`Core/dmg-2024/lore-glossary.md`) of named characters, places, materials, and organizations. Neither the class scout nor the monster scout owns it and the prior report did not mention it. For a *lore* RAG this is arguably the highest-value uncatalogued node set in the corpus.

---

## 1. ITEMS

### 1.1 The attunement grammar — the cleanest edge set in the corpus

**Exhaustive enumeration of every attunement parenthetical form corpus-wide** (all 32 distinct strings, not a sample):

```bash
grep -rhoiP "\(requires attunement[^)]*\)" --include='*.md' . | sort | uniq -c | sort -rn
```
→ **265 parentheticals total; 191 bare `(Requires Attunement)`; 74 carrying a `by …` restriction.**

```bash
grep -rniP "requires attunement" --include='*.md' . | grep -viP "\(requires attunement"
```
→ **14 hits, all of them prose about the attunement *rule*, none a descriptor.** (Confirmed by reading all 14: `Core/phb-2024/equipment.md:1355`, `Core/dmg-2024/dms-toolbox.md:315`, artificer-infusion preamble text, etc.) **⇒ the parenthetical form is a complete and clean extraction key; no prose fallback is needed.**

Verbatim samples across all four dialect variants:

| dialect | verbatim | file:line |
|---|---|---|
| 2024 Title Case, italic descriptor | `*Wondrous Item, Very Rare (Requires Attunement by a Druid or Warlock)*` | `Core/dmg-2024/magic-items-a-z.md:695` |
| 2024, multi-class list | `*Wondrous Item, Rare (Requires Attunement by a Cleric, Druid, or Paladin)*` | `Core/dmg-2024/magic-items-a-z.md:2326` |
| 2024, **item→item** restriction | `*Weapon (Warhammer), Very Rare (Requires Attunement by a Dwarf or a Creature Attuned to a Belt of Dwarvenkind)*` | `Core/dmg-2024/magic-items-a-z.md:1304` |
| 2024, free-text restriction | `*Weapon (Greatsword, Longsword, Rapier, Scimitar, or Shortsword), Legendary (Requires Attunement by a Creature of the Weapon's Choice)*` | `Core/dmg-2024/magic-items-a-z.md:2260` |
| 2014 lowercase, **non-italic plain paragraph** | `Wondrous item, common (requires attunement by a warlock)` | `Expanded/xgte/common-magic-items.md:97` |
| infusion, italic opens on *previous* line | `*Prerequisite: 14th-level artificer` ⏎ `Item: A suit of armor (requires attunement)*` | `Expanded/tcoe/artificer.md:882-884` |

**Restriction taxonomy** (word-boundary classification of all 74):
```bash
grep -rhoiP "requires attunement by [^)]*" --include='*.md' . | python3 -c "…"   # §derivation run, word-set membership
```
→ **53 mention a class · 11 generic `Spellcaster` · 5 species (3 warforged, 2 dwarf) · 3 dragonmark-gated · 2 free-text.**

⚠ **Derivation warning worth recording**: my first classification pass used `grep -ciP "…|orc|…"` for species and returned **19**. It was wrong: `orc` matches inside **s-ORC-erer**. The corrected word-boundary pass returns 5. *This is the same failure mode as the prior report's `[a-z_]+` frontmatter miss — a substring test that looks clean while being 4× off.*

**Occurrence-level (item, class) pairs**: **89** — wizard 22, sorcerer 14, warlock 13, druid 13, cleric 8, bard 7, paladin 6, ranger 3, illrigger 2, artificer 1.

**Catalog rows:**

| edge | evidence | multiplicity | count | grade | hazards |
|---|---|---|---|---|---|
| `item —attunable_by→ class` | `magic-items-a-z.md:695`, `:2326` | M:N | **89 pairs** over 53 descriptors (derivation above) | **MECHANICAL** | (a) 2014 books lowercase the class name — normalise case or lose all XGtE/TCoE/ERftLW/MCDM edges; (b) `Spellcaster` (11) is a *predicate over classes*, not a class — must not be minted as a class node; (c) `Artificer`/`Illrigger` are classes with no PHB-2024 entry |
| `item —attunable_by→ species` | `magic-items-a-z.md:1303` (Dwarf); `Expanded/erftlw/treasures.md` (warforged ×3) | M:N | **5** | **MECHANICAL** | 2014 species vocabulary ≠ 2024 species vocabulary |
| `item —attunable_by→ feat` (dragonmark) | `requires attunement by a creature with the Mark of Warding` | M:N | **3** | **GRAMMAR** | target is a *feat* (`Mark of Warding`), not a species; naive typing puts it in the species bucket |
| `item —attunement_requires→ item` | `magic-items-a-z.md:1303` "…or a Creature Attuned to a **Belt of Dwarvenkind**" | 1:1 | **1** | **GRAMMAR** | single instance; will look like noise to any generalising extractor |
| `item —has_attunement→ (bool)` | 265 parentheticals | scalar | **265** (191 bare + 74 restricted) | **MECHANICAL** | **FIELD, not edge** — one scalar on one entity, no inbound questions |
| `item —attunement_restriction→ (free text)` | `Creature of the Weapon's Choice`; `creature missing a hand or an arm` | scalar | **2** | PROSE | keep verbatim; do not try to resolve |

**Extractability grade for the attunement block overall: MECHANICAL.** One regex, `\((?i:requires attunement)(?: by ([^)]+))?\)`, over 100% of the population. **The only decision is case normalisation**, and that decision is forced (see §6.1).

⚠ **Descriptor-line shape is NOT uniform.** 247 of the 265 attunement lines start with `*`; **18 do not** — 8 in `Expanded/xgte/common-magic-items.md` (plain unformatted paragraph descriptors) and 10 in the artificer infusion blocks where the opening `*` sits on the previous line. A `^\*.*\*$` descriptor detector loses all 8 XGtE items silently.
```bash
grep -rhiP "\(requires attunement" --include='*.md' . | grep -cP '^\*'   # -> 247 of 265
```

### 1.2 Items that grant or reference spells

Three shapes, two of them structured:

**(i) `***Spells.***` trait + bullet list — MECHANICAL.** 15 occurrences (`grep -cP "^\*\*\*Spells\.\*\*\*" Core/dmg-2024/magic-items-a-z.md`). Example `magic-items-a-z.md:516-521`:
```
***Spells.*** While attuned to the book, you can cast the following spells (save DC 18) from it:

* Animate Dead
* Circle of Death
* Dominate Monster
* Finger of Death
```

**(ii) `| Spell | Charge Cost |` tables — MECHANICAL, and the edge carries a property.** 16 tables, **87 data rows**, all in `magic-items-a-z.md`:
```bash
grep -c "^| Spell | Charge Cost |" Core/dmg-2024/magic-items-a-z.md          # -> 16
find . -name '*.md' | xargs awk '/^\| Spell \| Charge Cost \|/{f=1;next} f&&/^\| *-+/{next} f&&/^\|/{n++;next} {f=0} END{}' # 87 rows
```
Sample `magic-items-a-z.md:3514-3518` — `| Burning Hands | 1 |`, `| Wall of Fire | 4 |`, `| Fireball | 3 |`. **`charge_cost` is a genuine edge property, not a field on either endpoint** — it belongs on the `RELATE item->spell` record.

**(iii) prose `cast <Spell>` — GRAMMAR.**
```bash
grep -ohP "cast (the )?\*?[A-Z][A-Za-z’'/]*( [A-Z][A-Za-z’'/]*){0,3}\*?( spell)?" Core/dmg-2024/magic-items-a-z.md | sort | uniq -c | sort -rn
```
→ ~90 hits, e.g. `cast Wish` ×5, `cast Scrying` ×4, `cast the Disguise Self spell` ×1, `cast *Suggestion*` ×1. **Note the three surface forms in one file: bare, `the … spell`, and italicised.**

**Combined derived count** (structured shapes ∪ `cast X` cue, per-item-block, longest-match against the 391 PHB spell names):
→ **61 DMG item blocks reference ≥1 spell; 139 distinct (item, spell) pairs; 97 distinct spells targeted.**

| edge | evidence | multiplicity | count | grade | hazards |
|---|---|---|---|---|---|
| `item —grants_spell→ spell` | `magic-items-a-z.md:516`, `:3514` | M:N | **139 pairs / 61 items / 97 spells** (derivation above) | **MECHANICAL** for shapes (i)+(ii) (≈98 pairs), **GRAMMAR** for (iii) | (a) save-DC/charge-cost live in the trait sentence, not the row — must be lifted separately; (b) the *table* shape has no bullets and the *bullet* shape has no table — an extractor written against one silently returns 0 for the other |
| `item —named_after→ spell` | `Wand of Fireballs`, `Necklace of Fireballs`, `Ring of Invisibility` | M:1 | **29 items** | **GRAMMAR** | **Pluralisation**: `Fireballs`→`Fireball`, `Lightning Bolts`, `Magic Missiles`. Also a *false-positive generator*: naive matching emits an item→spell edge from the item's **own heading**, so `Wand of Fireballs` self-cites |
| `item —references→ creature` | `Avatar of Death` (the only bolded creature name in the whole 282K file, prior report §4.2) | M:N | **UNCOUNTED** | PROSE | the book's own stated bold-type convention did not survive the scrape |

**⚠ The DMG's `| Item | Type | Attune? |` and `| Magic Item | Attunement |` tables (9 + 8 headers, all in the artificer chapters of TCoE/ERftLW) are a *second independent source* for item attunement.** Same free-oracle structure as the prior report's A/B spell-list pin. I did **not** diff them against the DMG descriptors — flagged, not measured.

---

## 2. FEATS

### 2.1 Prerequisite grammar

**2024 dialect (PHB 75 + EFotA 28 = 103 feats): a single italic descriptor line, exhaustively enumerated** (all 44 distinct strings):
```bash
grep -rhoP "^\*[^*]*Feat[^*]*\*$" --include='*.md' . | sort | uniq -c | sort -rn
```

Five prerequisite *kinds* appear inside `(Prerequisite: …)`:

| kind | verbatim sample | count |
|---|---|---|
| **level** | `*General Feat (Prerequisite: Level 4+)*` | 18 bare + all General/Epic variants |
| **ability score** | `*General Feat (Prerequisite: Level 4+, Strength or Dexterity 13+)*` | 6 |
| **ability score, semicolon-delimited alternative** | `*General Feat (Prerequisite: Level 4+; Intelligence, Wisdom, or Charisma 13+)*` | 1 |
| **class/subclass feature** | `*Fighting Style Feat (Prerequisite: Fighting Style Feature)*` · `*General Feat (Prerequisite: Level 4+, Spellcasting or Pact Magic Feature)*` | 10 + 3 + 1 |
| **another feat** | `*General Feat (Prerequisite: Level 4+, Mark of Warding Feat)*` (×12 dragonmark variants) · `*(…, Any Dragonmark Feat)*` · `*(…, Aberrant Dragonmark Feat)*` | 14 |
| **campaign setting** | `*Dragonmark Feat (Prerequisite: Eberron Campaign, Can't Have Another Dragonmark Feat)*` | 13 + 1 |
| **negative prerequisite** | `Can't Have Another Dragonmark Feat` | 13 |

⚠ **The separator is `,` in 17 of 18 multi-clause prerequisites and `;` in exactly one** (`Level 4+; Intelligence, Wisdom, or Charisma 13+`). Splitting on `,` alone turns that one into three bogus clauses. Splitting on `;` alone loses 17.

⚠ **`Can't Have Another Dragonmark Feat` is a NEGATIVE prerequisite** — an anti-edge. 13 occurrences. An extractor that stores prerequisites as "must have" edges will assert the exact opposite of the rule.

**2014 dialect — two further shapes, neither italic-descriptor:**

- **XGtE racial feats (15)**: a **bare unformatted paragraph** `Prerequisite: Halfling` (`Expanded/xgte/character-options-racial-feats.md:55`). Full enumeration of all 15 targets: Halfling ×2, Dragonborn ×2, `Elf (drow)`, Dwarf ×2, `Elf or half-elf`, Gnome, `Elf (high)`, Tiefling ×2, Half-orc, `Half-elf, half-orc, or human`, `Dwarf or a Small race`, `Elf (wood)`.
- **TCoE feats (16, of which 4 carry a prerequisite)**: italic `*Prerequisite: Spellcasting or Pact Magic feature*` (`Expanded/tcoe/feats.md:47`) — same semantics as the 2024 form but **lowercase `feature`** and no category tag.

**Catalog rows:**

| edge | evidence | multiplicity | count | grade | hazards |
|---|---|---|---|---|---|
| `feat —in_category→ feat_category` | `*General Feat*`; `| Ability Score Improvement\* | General |` (`feats.md:46`) | M:1 | **75** PHB + 28 EFotA, **two independent sources** (descriptor + `| Feat | Category |` table at `feats.md:44`) | **MECHANICAL** | build both and diff — same free-oracle pattern as the spell lists; I did **not** run this diff |
| `feat —requires_species→ species` | `Prerequisite: Halfling` (`xgte/…racial-feats.md:55`) | M:N | **15** | **MECHANICAL** | 2014 species names (`half-elf`, `Elf (drow)`, `a Small race`) do not map 1:1 onto the 10 PHB-2024 species; `Dwarf or a Small race` is a *size* predicate, not a species |
| `feat —requires_feat→ feat` | `(…, Mark of Warding Feat)` | M:N | **14 positive + 13 negative** | **MECHANICAL** | the 13 are NEGATIVE; also `Any Dragonmark Feat` is a *set* predicate, not a name |
| `feat —requires_feature→ class_feature` | `(Prerequisite: Fighting Style Feature)`, `(…, Spellcasting or Pact Magic Feature)`, `(…, Medium Armor Training)` | M:N | **10 + 3 + 1 + 5 armor/shield-training** = 19 | **GRAMMAR** | `Fighting Style Feature` / `Spellcasting` are cross-class abstractions, not one class's feature — resolving them to a single node is wrong. **Boundary: the class scout owns the target node.** |
| `feat —requires_ability→ ability_score` w/ threshold | `Strength or Dexterity 13+` | M:N | **17 descriptors** | **MECHANICAL** | disjunction (`or`) vs conjunction is carried by the separator only; `13+` is an edge *property* |
| `feat —requires_level→ (int)` | `Level 4+`, `Level 19+` | scalar | 18+11+29 variants | **MECHANICAL** | **FIELD, not edge** |
| `feat —requires_setting→ campaign` | `Eberron Campaign` | M:1 | **14** | **MECHANICAL** | one-off vocabulary; probably a tag not a node |

### 2.2 Feat → spell

**Two shapes.**

**Structured — `| Spell Level | Spells |` tables.** 28 table headers corpus-wide:
```bash
find . -name '*.md' | xargs grep -c "^| Spell Level | Spells |" | grep -v ':0$'
# efota/character-options.md:12  erftlw/character-creation-dragonmarks.md:12
# xgte/subclasses.md:2  tcoe/warlock.md:1  scag/classes.md:1
```
Data rows: **efota 60, erftlw 60, xgte 10, tcoe 5, scag 5 = 140 rows**, each row's `Spells` cell a comma list. Sample `Expanded/efota/character-options.md:530-537`:
```
#### Mark of Detection Spells

| Spell Level | Spells |
| --- | --- |
| 1 | Detect Evil and Good, Identify |
| 2 | Detect Thoughts, Find Traps |
```
⚠ `Detect Evil and Good` contains a comma-free `and` — but `Locate Animals or Plants` contains `or`, and rows are comma-separated. **A naive `,`-split is safe here; a naive `and`/`or`-split is not.**

**Prose — `you always have the <Spell> spell prepared`.** `Core/phb-2024/feats.md:432` (Fey Touched): *"You always have that spell and the **Misty Step** spell prepared."*

⚠ **Some feat→spell edges are PARAMETRIC, not named.** Same line: *"Choose one level 1 spell from the Divination or Enchantment school of magic."* `Core/phb-2024/feats.md:202` (Magic Initiate): *"two cantrips of your choice from the **Cleric, Druid, or Wizard** spell list."* **These are constraints over the spell set (school + level, or class-list + level), not edges to a named spell.** A graph that only models named edges will show Magic Initiate granting zero spells — which is exactly wrong.

| edge | evidence | multiplicity | count | grade | hazards |
|---|---|---|---|---|---|
| `feat —grants_spell→ spell` (structured) | `efota/character-options.md:530` | M:N | **140 table rows** ⇒ ~300 pairs (rows are comma lists; **pairs UNCOUNTED**) | **MECHANICAL** | 13 dragonmark feats duplicated between EFotA (2024) and ERftLW (2014) — 12+12 identical table counts. Cross-edition duplicate, prior report's H2 applies |
| `feat —grants_spell→ spell` (prose) | `feats.md:432` | M:N | **UNCOUNTED** (13 distinct names in `Core/phb-2024/feats.md`, of which 6 are common-word false positives — see §6.2) | PROSE | |
| `feat —grants_spell_from→ (class_list \| school, level)` | `feats.md:202`, `:432` | M:N | **UNCOUNTED** | PROSE | **parametric — cannot be a name edge at all** |

### 2.3 The reverse direction: background → feat (structured, and nobody has claimed it)

```bash
grep -rcP "^\*\*Feat:\*\*" --include='*.md' .   # efota/character-options.md:17  phb-2024/character-origins.md:16  => 33
```
`Core/phb-2024/character-origins.md:110`: `**Feat:** Magic Initiate (Cleric) (see chapter 5)`

| edge | evidence | multiplicity | count | grade | hazards |
|---|---|---|---|---|---|
| `background —grants_feat→ feat` | `character-origins.md:110` | M:1 | **33** | **MECHANICAL** | **`Magic Initiate (Cleric)` is not a feat name** — the feat is `Magic Initiate`; `(Cleric)` is an edge parameter. 3 such parameterised rows (Cleric/Druid/Wizard). Also carries a *semi-link* pointer: `(see chapter 5)` / `(see "Dragonmark Feats")` |

---

## 3. CONDITIONS & THE RULES GLOSSARY

### 3.1 Yes — and it is the best-designed entity set in the corpus

`Core/phb-2024/rules-glossary.md` — **161 glossary entries** at H3/H4, 155 `***` separators.
```bash
grep -cP "^#{1,4} " Core/phb-2024/rules-glossary.md    # 167 incl. H1/H2 scaffolding
```

**Headings carry an explicit bracketed TYPE TAG** — the corpus's only self-describing type system:
```bash
grep -ohP "^#{3,4} .*\[([^]]+)\]" Core/phb-2024/rules-glossary.md | grep -oP "\[[^]]+\]" | sort | uniq -c | sort -rn
# 15 [Condition]   12 [Action]   6 [Area of Effect]   5 [Hazard]   3 [Attitude]
```
And the file **states the convention explicitly** at `rules-glossary.md:22`: *"A tag—Action, Area of Effect, Attitude, Condition, or Hazard—indicates that a rule is part of a family of rules. **The tags also have glossary entries.**"* ⇒ `Condition` is itself entry #`:365`. **The taxonomy is self-hosting.**

**All 15 conditions, enumerated:** Blinded `:204`, Charmed `:329`, Deafened `:569`, Exhaustion `:669`, Frightened `:725`, Grappled `:735`, Incapacitated `:865`, Invisible `:915`, Paralyzed `:1057`, Petrified `:1087`, Poisoned `:1113`, Prone `:1133`, Restrained `:1173`, Stunned `:1374`, Unconscious `:1484`.

**Second independent source, agreeing exactly**: `Core/phb-2024/playing-the-game.md:1202` — `## Conditions` followed by a 15-item bullet list, *"The following conditions are defined in the rules glossary"*. **15 = 15, same names, same order.** Another free correctness oracle, same shape as the prior report's §6.4 pin.

**Condition entries have internal structure**: `***<Effect Name>.*** <text>` sub-traits. `rules-glossary.md:735` (Grappled) has three: `***Speed 0.***`, `***Attacks Affected.***`, `***Movable.***`. Poisoned has one. **Condition→condition edges exist in prose**: Grappled's `***Ending a Grapple.***` says *"if the grappler has the **Incapacitated** condition"*; `playing-the-game.md:1220` says *"some conditions apply other conditions."*

### 3.2 The reference surface — measured

**Command (this is the one you asked for, run over all 15 not 3):**
```bash
for c in Blinded Charmed Deafened Exhaustion Frightened Grappled Incapacitated Invisible \
         Paralyzed Petrified Poisoned Prone Restrained Stunned Unconscious; do
  n=$(grep -rhoP "(?<![A-Za-z])$c(?![A-Za-z])"  --include='*.md' . | wc -l)
  l=$(grep -rhoP "(?<![A-Za-z])${c,}(?![A-Za-z])" --include='*.md' . | wc -l)
  echo "$c Titlecase=$n lowercase=$l"
done
```

| condition | Titlecase | lowercase | | condition | Titlecase | lowercase |
|---|---|---|---|---|---|---|
| Poisoned | 316 | 77 | | Incapacitated | 184 | 80 |
| Charmed | 229 | 109 | | Restrained | 174 | 52 |
| Frightened | 219 | 88 | | Grappled | 164 | 25 |
| Prone | 210 | 72 | | Exhaustion | 162 | 60 |
| Paralyzed | 117 | 25 | | Blinded | 92 | 53 |
| Invisible | 87 | 48 | | Petrified | 76 | 27 |
| Unconscious | 63 | 25 | | Stunned | 62 | 26 |
| Deafened | 60 | 17 | | | | |

**Total ≈ 2,215 Titlecase + 764 lowercase ≈ 2,979 mentions across 15 names.**

High-precision subset (the canonical 2024 phrasing):
```bash
grep -rhoiP "(Blinded|Charmed|…|Unconscious) condition" --include='*.md' . | wc -l   # -> 988
```

Structured immunity edges:
```bash
grep -rhoP "^\*\*Immunities\*\* .*"           --include='*.md' . | wc -l   # -> 256  (2024 dialect)
grep -rhoP "^\*\*Condition Immunities\*\* .*" --include='*.md' . | wc -l   # ->  38  (2014 dialect)
```
2024 form packs **damage-type immunities and condition immunities on one line, separated by `;`**: `**Immunities** Poison; Paralyzed, Petrified, Poisoned` (`Core/mm-2024/monsters-*.md`). Splitting on `,` instead of `;` merges the two vocabularies. Occurrence tally after splitting: Poisoned 119, **Poison 118**, Charmed 92, Frightened 79, Exhaustion 79, …

⚠ **`Poison` (damage type) and `Poisoned` (condition) differ by two characters and appear adjacent on the same line, 118 and 119 times respectively.** A prefix-matching or stemming resolver conflates them and mis-types roughly 237 edges. This is the single most likely silent typing error in the corpus.

### 3.3 Case dialect — a clean, exploitable split with exactly one exception

```bash
for c in Poisoned Frightened Grappled; do for d in Core Expanded/efota MCDM Expanded/tcoe \
  Expanded/xgte Expanded/erftlw Expanded/scag; do
  echo "$c $d U=$(grep -rhoP "(?<![A-Za-z])$c(?![A-Za-z])" --include='*.md' $d|wc -l)" \
       "l=$(grep -rhoP "(?<![A-Za-z])${c,}(?![A-Za-z])" --include='*.md' $d|wc -l)"; done; done
```

| | Core | efota | MCDM | tcoe | xgte | erftlw | scag |
|---|---|---|---|---|---|---|---|
| Poisoned U/l | **300**/10 | **15**/0 | 0/**6** | 0/**21** | 1/**10** | 0/**30** | 0/0 |
| Frightened U/l | **210**/2 | **9**/0 | 0/**10** | 0/**23** | 0/**18** | 0/**33** | 0/**2** |
| Grappled U/l | **160**/0 | **4**/0 | 0/**4** | 0/**6** | 0/**1** | 0/**14** | 0/0 |

**Edition `'5.5'` ⇒ Title Case. Edition `'5.0'` ⇒ lowercase. Frontmatter predicts casing — except MCDM.**

⚠ **MCDM `tir` is frontmatter `edition: '5.5'` (verified, `MCDM/tir/tir.md:5`) but uses 2014-style lowercase conditions throughout (0 Titlecase / 20 lowercase across the three samples).** A resolver that branches on `edition` to pick a casing rule silently drops every MCDM condition edge. **Branch on nothing; case-fold always.**

### 3.4 Verdict: **CONDITION IS A NODE. Emphatically.**

Against your dividing line — *identity, attributes, inbound questions*:
- **Identity**: yes, 15 named entries with stable H3 headings, a bracketed type tag, and a second corroborating list.
- **Attributes**: yes — each has 1–3 named sub-effects (`***Speed 0.***`, `***Attacks Affected.***`).
- **Inbound questions**: ~2,979 mentions from spells, monsters, items, feats, and other conditions. "What imposes Frightened?" / "What is immune to Poisoned?" are exactly the questions a graph exists to answer, and both are answerable *only* via inbound edges.

The other glossary families grade differently:
- **`[Action]` (12)** — node. Same argument, weaker surface. `Dash`, `Dodge`, `Hide`, `Study`, `Utilize`, `Search`, `Ready`, `Help`, `Influence`, `Attack`, `Magic`(implied), etc. Heavily referenced by items and features.
- **`[Area of Effect]` (6: Cone, Cube, Cylinder, Emanation, Line, Sphere)** — **FIELD on spell, not node.** Every spell has exactly one; nobody asks "what else is a Cone?"
- **`[Hazard]` (5)**, **`[Attitude]` (3: Friendly, Hostile, Indifferent)** — node, thin.
- **Damage types (13)** — **NODE.** Closed vocabulary from a table (`rules-glossary.md:521-540`), reference surface measured: `Piercing 399, Slashing 312, Bludgeoning 283, Fire 267, Necrotic 234, Psychic 223, Force 211, Poison 180, Radiant 153, Cold 99, Lightning 87, Acid 73, Thunder 67` via `grep -rhoiP "(?<![A-Za-z])$t damage(?![A-Za-z])"`. **≈2,588 typed inbound references.** Both spells and monsters point at it — textbook cross-cutting node.
- **Creature types (14)** — NODE, but **owned by the monster scout**. Note the source is *not* a table: `rules-glossary.md:429-462` lists them as **14 bare one-word paragraphs separated by blank lines** (HTML→md conversion damage, same failure mode as the prior report's H5 ability-score collapse). A table-based extractor gets 0.
- **Schools of magic (8)** — FIELD on spell. Derived: `grep -rhoP "^\*(?:Level \d+|Cantrip) (\w+)"` → Conjuration 70, Transmutation 58, Abjuration 53, Evocation 52, Enchantment 39, Divination 31, Necromancy 27, Illusion 27. ⚠ the same regex also catches 39 `*Level N Bastion Facility*` lines — a 9th phantom "school" called `Bastion`. Anchor on the closed 8-name set.

### 3.5 The glossary contains the corpus's ONLY explicit cross-references

```bash
grep -rciP "\*See also\*" --include='*.md' .     # Core/phb-2024/rules-glossary.md:93  — and nothing else
```
**93 lines, 97 occurrences, 100% confined to one file.** Two target forms:
```bash
grep -rhoP '\*See also\*[^\n]*' Core/phb-2024/rules-glossary.md | grep -coP "chapter \d+"       # -> 50
grep -rhoP '\*See also\*[^\n]*' Core/phb-2024/rules-glossary.md | grep -oP '“[^”]+”' | wc -l    # -> 124
```
- **50 chapter pointers**: `*See also* chapter 1 ("D20 Tests" and "Proficiency").` — resolve to a *file*, not an entity.
- **124 curly-quoted entry pointers**: `*See also* "Friendly," "Hostile," "Indifferent," and "Influence."` (`rules-glossary.md:198`)

⚠ **The trailing punctuation is INSIDE the closing quote** (American style): `"Speed."` ×6, `"Influence."` ×4, `"Exhaustion."` ×2, `"Creature Type."` ×2, `"Social Interaction,"` ×1. **A naive `“([^”]+)”` capture yields `Speed.` — which matches no glossary entry.** Strip trailing `[.,]` before lookup or lose ~30% of the only genuine link set in the corpus.

| edge | evidence | multiplicity | count | grade | hazards |
|---|---|---|---|---|---|
| `glossary_term —see_also→ glossary_term` | `rules-glossary.md:198`, `:735` | M:N | **124** | **MECHANICAL** | trailing punctuation inside quotes; some targets are chapter *sections*, not glossary entries |
| `glossary_term —see_also→ chapter` | `rules-glossary.md:756` | M:N | **50** | **MECHANICAL** | target is a page/file |
| `entity —inflicts→ condition` | ubiquitous | M:N | **988** high-precision (`"X condition"`) of **~2,979** total mentions | **GRAMMAR** (the `X condition` suffix), **PROSE** otherwise | case dialect (§3.3); `Poison`/`Poisoned` (§3.2); `Invisible` doubles as adjective |
| `monster —immune_to→ condition` | `**Immunities** Poison; Exhaustion, Poisoned` | M:N | 294 lines (256 + 38); **pairs UNCOUNTED** | **MECHANICAL** | `;` vs `,`; 2014/2024 label split; parentheticals like `Charmed (except from its vampire master)` ×2 |
| `condition —applies→ condition` | `rules-glossary.md:756` (Grappled ends if grappler is Incapacitated) | M:N | **UNCOUNTED** | PROSE | |

---

## 4. EQUIPMENT / GEAR (NON-MAGIC)

**Verdict: ENTITIES, not chunks.** This is the second-cleanest structured region in the corpus after magic items, and it has the same two-independent-sources property as the spell lists.

`Core/phb-2024/equipment.md` — five master tables + per-item detail headings:

| table | header | line | data rows |
|---|---|---|---|
| Weapons | `| Name | Damage | Properties | Mastery | Weight | Cost |` | `:56` | **39** |
| Armor | `| Armor | Armor Class (AC) | Strength | Stealth | Weight | Cost |` | `:203` | **14** |
| Adventuring Gear | `| Item | Weight | Cost |` | `:525` | **84** |
| Mounts / Tack / Vehicles | `#### Mounts and Other Animals` `:1164`, `#### Tack, Harness…` `:1177`, `#### Airborne and Waterborne Vehicles` `:1217` | — | UNCOUNTED |
| Services (Food/Lodging, Travel, Hirelings, Spellcasting) | `| Service | Cost |` ×4 | `:1273`–`:1327` | UNCOUNTED |

```bash
awk 'NR>=56 && NR<=100 && /^\| [A-Z]/'  Core/phb-2024/equipment.md | wc -l   # 39 weapons
awk 'NR>=203 && NR<=222 && /^\| [A-Z]/' Core/phb-2024/equipment.md | wc -l   # 14 armor
awk 'NR>=525 && NR<=610 && /^\|/'       Core/phb-2024/equipment.md | wc -l   # 84 gear
grep -cP "^#### .*\((.*(GP|SP|CP|Varies)).*\)" Core/phb-2024/equipment.md    # 112 detail headings
```

**Second source, mechanically:** 112 `#### <Name> (<Price>)` detail headings, e.g. `#### Acid (25 GP)` `:612`, `#### Alchemist's Fire (50 GP)` `:618`. **Price appears in both the table and the heading → free A/B oracle for equipment, exactly parallel to the spell-list pin.** (I did not run the diff.)

**The Weapons table columns ARE edges to defined entities.** Both vocabularies close perfectly:
```bash
awk 'NR>=56&&NR<=100&&/^\| [A-Z]/{split($0,a,"|");print a[4]}' Core/phb-2024/equipment.md \
  | tr ',' '\n' | sed 's/([^)]*)//g;s/^ *//;s/ *$//' | sort | uniq -c | sort -rn
# Two-Handed 13, Heavy 9, Ammunition 9, Light 8, Versatile 7, Thrown 7, Loading 6, Finesse 6, Reach 5, — 3
awk 'NR>=56&&NR<=100&&/^\| [A-Z]/{split($0,a,"|");print a[5]}' Core/phb-2024/equipment.md \
  | sed 's/^ *//;s/ *$//' | sort | uniq -c | sort -rn
# Vex 8, Slow 7, Sap 6, Topple 5, Push 4, Nick 4, Graze 2, Cleave 2
```
Against the headings `#### Ammunition|Finesse|Heavy|Light|Loading|Range|Reach|Thrown|Two-Handed|Versatile` (`:109`–`:149`) and `#### Cleave|Graze|Nick|Push|Sap|Slow|Topple|Vex` (`:157`–`:185`): **weapon-property vocabulary 9/9 closes; mastery vocabulary 8/8 closes exactly.** No unknown tokens either direction.

**Catalog rows:**

| edge | evidence | multiplicity | count | grade | hazards |
|---|---|---|---|---|---|
| `weapon —has_property→ weapon_property` | `equipment.md:59` `| Dagger | 1d4 Piercing | Finesse, Light, Thrown (Range 20/60) | Nick | 1 lb. | 2 GP |` | M:N | **70 pairs** (sum of the property tally) over 39 weapons, 9 properties | **MECHANICAL** | `Thrown (Range 20/60)` and `Versatile (1d8)` carry an **edge parameter inside parens**; `—` = none, 3 rows |
| `weapon —has_mastery→ mastery_property` | same line, col 4 | M:1 | **38** (39 weapons, 1 header artefact) over 8 masteries | **MECHANICAL** | `Light`/`Heavy` appear in *both* the property vocabulary and as English adjectives elsewhere |
| `weapon —deals→ damage_type` | col 2 `1d4 Piercing` | M:1 | **39** | **MECHANICAL** | dice expression + type in one cell |
| `armor —requires→ ability_score` | `| Splint Armor | 17 | Str 15 | Disadvantage | …` col 3 | M:1 | ≤14 | **MECHANICAL** | `—` for most |
| `background —grants_proficiency→ skill` | `**Skill Proficiencies:** Insight and Religion` (`character-origins.md:112`) | M:N | **46 lines** (`grep -rcP "^\*\*Skill Proficiencies:\*\*"`: phb 16, efota 17, scag 12, erftlw 1); pairs UNCOUNTED | **MECHANICAL** | delimiter is **` and `** in 2024, **`, `** in 2014 SCAG (`Athletics, Insight` `backgrounds.md:32`) — two different splits |
| `background —grants→ equipment` | `**Equipment:** *Choose A or B:* (A) Calligrapher's Supplies, Book (prayers), … 8 GP; or (B) 50 GP` | M:N | **46 lines**; pairs UNCOUNTED | **GRAMMAR** | the A/B **choice** structure means the edges are *alternatives*, not conjuncts. Modelling them as flat edges asserts the character gets both bundles |
| `background —grants_proficiency→ tool` | `**Tool Proficiency:** Calligrapher's Supplies` | M:N | **34 + 8** (`Tool Proficiencies:`) | **MECHANICAL** | singular/plural label variants |
| **`monster —carries→ equipment`** | `**Gear** Half-Plate Armor, Longbow, Longsword, Shield` (MM 2024) | M:N | **92 lines, 191 tokens, 46 distinct** | **MECHANICAL** | see the resolution test below |

**Gear resolution test — an actual measurement of the bare-name problem, on a closed set:**
```python
# 46 distinct **Gear** tokens matched against equipment-table ∪ magic-item-heading index
#   exact match                          : 39
#   match only after singularise+lowercase: 5   ['Javelins','Daggers','Pistols','Light Hammers','Spears']
#   unresolved                            : 2   ['Half-Plate Armor','Handaxes']
```
`Handaxes` is a stemming artefact (`Handaxe`). **`Half-Plate Armor` is a genuine orthographic mismatch:**
```bash
grep -rhoiP "half[- ]plate\w*" --include='*.md' . | sort | uniq -c    # 4 Half-Plate · 2 Half Plate · 1 half plate
```
The canonical armor-table row (`equipment.md:213`) is **`Half Plate Armor`** — unhyphenated. Monster Gear lines write **`Half-Plate Armor`** — hyphenated. **⇒ 11% of a 46-name closed set fails exact matching; hyphen+plural+case normalisation takes it to 100%.** That is the cheapest possible empirical calibration of the resolver, and it is on a set small enough to hand-audit.

---

## 5. SPELL→SPELL AND FEATURE→SPELL IN PROSE

### 5.1 Spell → spell

Per-spell-body sweep of `Core/phb-2024/spell-descriptions.md`, longest-match-first over the 391 PHB spell names, self-mentions excluded:

```python
# 391 spells sliced on '### ' headings; each body swept with (?<![A-Za-z])NAME(?![A-Za-z]), longest first
# -> 176 distinct (source, target) pairs · 204 occurrences · 46 distinct targets · 35 self-mentions
```

**Top sources** (spells that cite other spells): `Prismatic Wall` 10, `Hallow` 9, `Guards and Wards` 8, `Summon Fiend` 5, `Symbol` 5, `Wish` 5, `Fire Shield` 4, `Giant Insect` 4, `Summon Dragon` 4.

⚠ **Of the 46 targets, the top five are false positives.** `Divination` 38, `Light` 34, `Resistance` 21, `Darkvision` 14, `Fly` 12 — 119 of the 204 occurrences, **58%**. `Divination` is overwhelmingly the *school* in `*Level 4 Divination*` descriptor lines; `Light` is `Bright Light`/`Dim Light`; `Resistance` is damage resistance; `Fly` is Fly Speed. **The honest spell→spell surface after removing the eight common-word names is on the order of 60–80 occurrences, and I did not hand-verify it: UNCOUNTED.**

Genuine, hand-checked examples: `Greater Restoration` 8, `Dispel Magic` 7, `Gust of Wind` 6, `Water Breathing` 3, `Remove Curse` 2, `Arcane Lock` 2.

### 5.2 The `X spell` suffix as a disambiguator

```bash
grep -rhoP "(?<![A-Za-z])[A-Z][A-Za-z’']+(?: (?:of|the|and|or|with|from|without)? ?[A-Z][A-Za-z’']+){0,4} spells?(?![A-Za-z])" --include='*.md' . | wc -l
```
→ **762 hits corpus-wide.** But the distinct-value tally shows the suffix is *itself* ambiguous:
- **sentence-start noise**: `The spell` 131, `This spell` 48, `The spells` 33, `Each spell` 15, `These spells` 10, `Some spells` 9, `Any spell` 9 = **255 (33%)**
- **class-list noise**: `Wizard spell(s)` 53, `Warlock` 22, `Sorcerer` 20, `Artificer` 17, `Cleric` 15, `Bard` 14, `Druid` 15, `Ranger` 17, `Paladin` 8 = **~181 (24%)** — these are `class —has_spell_list→` references, a *different* edge
- **genuine spell targets**: `Wish spell` 23, `Remove Curse` 10, `Greater Restoration` 9, `Lesser Restoration` 6, `Mending` 5, `Dispel Magic` 5, `Bless` 5, `Plane Shift` 4, `Identify` 4, `Etherealness` 4 … ≈ **300 (40%)**

**⇒ `<Name> spell` is a good *precision* filter and a bad *recall* filter** — items say `cast Fireball` with no suffix at all (§1.2).

### 5.3 Monster → spell (boundary edge; target is mine, source is the monster scout's)

```bash
# lines matching ^\*\*(At Will|N/Day( Each)?):\*\*, comma-split respecting parens
# -> 242 lines · 628 spell-name tokens · 148 distinct spells
grep -rhoP "^\*\*At Will:\*\*" --include='*.md' . | wc -l          # 115
grep -rhoP "^\*\*\d+/Day( Each)?:\*\*" --include='*.md' . | sort | uniq -c
# 79 **1/Day Each:**  ·  20 **1/Day:**  ·  16 **2/Day Each:**  ·  9 **2/Day:**  ·  2 **3/Day:**  ·  1 **3/Day Each:**
```
Sample `Core/mm-2024/monsters-*.md`: `**At Will:** Detect Magic, Etherealness, Magic Missile (level 4 version)`.

**This is the single largest MECHANICAL spell-targeting edge set in the corpus (628 pairs) and it is neither the class scout's nor, strictly, the monster scout's** — the source node is a stat block, the target is a spell entity, and the frequency label is an edge property.

⚠ **The parentheticals are edge properties with heterogeneous semantics** and must not be dropped: `level N version` (56, upcast level), `self only` (15, target restriction), `included in AC` (7, stacking note), `snakes only` (5, target restriction), `the hand is Invisible` (9, effect modifier), and one 130-character clause on Shapechange (12×). ⚠ **Comma-splitting must respect parentheses** — `Magic Missile (level 4 version)` contains no comma but several qualifiers do.

**Catalog rows:**

| edge | evidence | multiplicity | count | grade | hazards |
|---|---|---|---|---|---|
| `spell —references→ spell` | `spell-descriptions.md` bodies (Prismatic Wall, Hallow, Guards and Wards) | M:N | **204 raw occ / 176 pairs; ≥58% false-positive; true value UNCOUNTED** | PROSE | §6.2 common-word collision dominates |
| `monster —casts→ spell` w/ frequency + qualifier | `**At Will:** Detect Magic, …` | M:N | **628 pairs, 148 spells, 242 lines** | **MECHANICAL** | paren-aware split; qualifier semantics are heterogeneous; 2014-dialect stat blocks use a `***Spellcasting.***` prose paragraph instead (**UNCOUNTED**, prior report H5 territory) |
| `class —has_spell_list→ spell` via `X spell(s)` prose | 181 of the 762 suffix hits | M:N | already covered by prior report §4.3 (987 explicit) | — | prose form is redundant with the structured source; **do not double-count** |
| `subclass —grants_spell→ spell` (`| <Class> Level | Spells |`) | `character-classes.md`, `xgte/subclasses.md`, `tcoe/*` | M:N | **56 tables** across 15 files (`find . -name '*.md' \| xargs awk 'FNR>1 && /^\| *-+ *\|/ {print FILENAME": "prev} {prev=$0}' \| grep -P "\| \w+ Level \| (Spells?\|Circle Spells\|Prepared Spells)"`) | **MECHANICAL** | **BOUNDARY — class scout owns the source node.** This is the prior report's uncounted gap #3, now located and counted at the table level |

---

## 6. THE REFERENCE-RESOLUTION PROBLEM — beyond what the prior report noted

The prior report established: zero links; bare capitalized names; longest-match-first over a length-sorted index. **All true. Here are the six things it does not cover, each measured.**

### 6.1 Case is not cosmetic — it is a hard edition split, with an exception

Measured in §3.3: 5.5-edition books Title-Case game terms; 5.0-edition books lowercase them; **MCDM `tir` is `edition: '5.5'` and lowercases anyway.** ⇒ **Case-fold unconditionally. Do not branch on `edition`.** This also subsumes the prior report's H6 (XGtE sentence-case spell lists, 20/95 exact → 95/95 folded) — same disease, wider than one file.

Beyond casing, three further orthographic axes, each measured corpus-wide:

```bash
grep -rho "’" --include='*.md' . | wc -l      #  14,953  curly apostrophe U+2019
grep -rho "'" --include='*.md' . | wc -l      #     862  ASCII apostrophe
grep -rhoP "[“”]" --include='*.md' . | wc -l  #   2,860  curly double quotes
grep -rho '"'  --include='*.md' . | wc -l     #      72  ASCII double quote
grep -rhoP "[–—]" --include='*.md' . | wc -l  #   9,749  en/em dash
grep -rho "−" --include='*.md' . | wc -l      #   1,788  U+2212 MINUS SIGN (not hyphen!)
```
- **Apostrophes are 95% curly (U+2019) but 5% ASCII.** Every possessive spell name (`Bigby's Hand`, `Otiluke's Resilient Sphere`, `Tenser's Floating Disk`) and every possessive item/tool name (`Calligrapher's Supplies`, `Thieves' Tools`) is exposed to this. **A hand-typed user query will use ASCII and miss all 15 possessive spells.**
- **U+2212 MINUS SIGN, 1,788 occurrences** — used for negative ability modifiers (`| Int | 2 | −4 | −4 |`). Not a hyphen, not an en dash. Numeric parsers built on `-?\d+` return None.
- **Hyphenation is inconsistent within one book**: `Half Plate Armor` (canonical table) vs `Half-Plate Armor` (monster Gear) — §4. Also `shape-shift` 32 / `Shape-Shift` 28 / `shapeshifting` 6, and `half-elf` 47 / `Half-elf` 7 / `Half-Elf` 4 (three casings of one hyphenated token).

### 6.2 The dominant hazard: Title-Cased common vocabulary collides with entity names

**This is the finding I would most want the design lead to carry away.** The 2024 books Title-Case ordinary rules vocabulary (`Bright Light`, `Dim Light`, `Resistance`, `Advantage`, `Darkvision`, `Fly Speed`, `Magic action`, `Attunement`). Several spell names are exactly those words.

```python
# 391 PHB spell names swept over Core/dmg-2024/magic-items-a-z.md, longest-match-first, word-boundaried
# -> 160 distinct spells, 552 occurrences
# top: Light 59, Shield 41, Resistance 38, Wish 18, Darkvision 17, Fly 16, Command 14, Darkness 13, Fireball 10
```
Sampling the contexts proves almost all of the top hits are wrong:
```bash
grep -ohP "\b\w+ \w+ Light\b" Core/dmg-2024/magic-items-a-z.md | sort | uniq -c | sort -rn | head
#   15 "and Dim Light"  ·  6 "sheds Bright Light"  ·  2 "the Bright Light"  ·  2 "sheds Dim Light" …
grep -ohP "\b\w+ Resistance\b" Core/dmg-2024/magic-items-a-z.md | sort | uniq -c | sort -rn | head
#   19 "have Resistance"  ·  3 "of Resistance"  ·  2 "Spell Resistance"  ·  2 "ignores Resistance" …
grep -ohP ".{25}(?<![A-Za-z])Command(?![A-Za-z]).{20}" Core/dmg-2024/magic-items-a-z.md
#   "a *Ring of Elemental Command* (air)…"  ×2   vs   "…to cast Charm Person, Command, or Comprehend Lang…"  ×1
```

**I then tested the obvious fix, and it does not work.** Longest-match-first over a **unified 1,184-name index** (161 glossary ∪ 391 spells ∪ 410 magic items ∪ 77 feats ∪ 156 equipment):

| term | spell-index only | + glossary | + glossary + items + feats + equipment |
|---|---|---|---|
| `Light` | 59 | 16 | **16** |
| `Fly` | 16 | 6 | **5** |
| `Darkness` | 13 | 13 | **6** |
| `Command` | 14 | 14 | **9** |
| **`Shield`** | 41 | 41 | **33** |
| **`Resistance`** | 38 | 38 | **34** |
| **`Darkvision`** | 17 | 17 | **17** |
| `Fireball` | 10 | 10 | **10** ✅ |

Longest-match helps where the false positive is a **longer** phrase (`Bright Light`, `Fly Speed`, `Book of Vile Darkness`, `Ring of Elemental Command`). **It cannot help where the glossary term and the spell name are the same string** — `Resistance`, `Darkvision`, `Telepathy`, `Darkness` are *simultaneously* glossary entries and spell names (exact set intersection, computed: `{Darkness, Darkvision, Resistance, Telepathy}`), and `Shield` is simultaneously a spell, an armor row, and a mastery-adjacent noun.

**⇒ Verdict for the design lead: name-index disambiguation has a hard floor of roughly 80 false positives per major file. Type disambiguation must come from CONTEXT — a verb/suffix cue (`cast X`, `the X spell`, `X condition`, `X damage`) — not from the index.** The prior report's longest-match-first rule is necessary and **not sufficient**, and the gap is not small.

Precision-vs-recall of the cue approach, measured: restricting to `***Spells.***` bullets ∪ `| Spell | Charge Cost |` rows ∪ `cast (the )?X` yields **139 item→spell pairs over 61 item blocks with essentially zero false positives** — versus **552 raw occurrences** from bare-name matching. **~75% of the raw surface is noise.**

### 6.3 Plurals and possessives, measured

- **Plurals occur in real edge sources.** 5 of 46 monster-Gear tokens (`Javelins`, `Daggers`, `Pistols`, `Light Hammers`, `Spears`) and 3 of 29 spell-derived item names (`Wand of Fireballs`, `Wand of Lightning Bolts`, `Wand of Magic Missiles`). ⚠ `Handaxes` → naive `e?s$` stripping gives `handax`, but the index holds `Handaxe`. **Stemming must be `s|es` with an `e`-restore, or use a lemma table for the ~150-name equipment set.**
- **Possessives**: 15 PHB-2024 spells carry a `<Name>'s` prefix. All use **curly U+2019**. Enumerated with both casings present in the corpus:
```bash
grep -rhoiP "(Bigby|Tasha|Otiluke|Mordenkainen|Leomund|Melf|Evard|Rary|Drawmij|Nystul|Otto|Tenser)[’']s [A-Z][a-z]+( [A-Z][a-z]+)?" --include='*.md' . | sort | uniq -c | sort -rn
# Bigby's Hand 5 / Bigby's hand 5 · Mordenkainen's Faithful Hound 4 / …faithful hound 4
# Rary's Telepathic Bond 4 / …telepathic bond 4 · Otiluke's Resilient Sphere 4 / …resilient sphere 5 …
```
**Every one of them appears in BOTH casings** — Title Case in the 2024 books, sentence case in the 2014 books. ⚠ **And `Tasha's Cauldron of Everything` (30 occurrences) is a *book title*, not a spell — while `Tasha's Bubbling Cauldron` (5) and `Tasha's Hideous Laughter` (10) are spells.** The `Tasha's Cauldron…` prefix is 6 characters from being wrong.

### 6.4 "See chapter X" and the other pointer forms

```bash
grep -rhoiP "\(?see (also )?(chapter|appendix|the) [^).,;]{0,40}" --include='*.md' . | sed 's/[0-9]\+/N/g' | sort | uniq -c | sort -rn | head -20
```
| form | count | resolves to |
|---|---|---|
| `(see chapter N` | 148 | a file within the same book |
| `(see the rules glossary` | 20 | `Core/phb-2024/rules-glossary.md` (whole file) |
| `See chapter N for the rules on spellcasting` | 10 | file + topic |
| `(see the Dungeon Master's Guide` | 7 | **another book** |
| `(see the Monster Manual` | 5 (+5 variants "for its stat block") | **another book — a genuine cross-book entity pointer** |
| `(see appendix B` | 5 | file |
| `See the Sacred Oath class feature …` | 4 (+3 Channel variant) | **a named class feature** |
| `See the Divine Domain class feature …` | 4 | **a named class feature** |
| `See the "Crafting Magic Items" section in chapter N` | 4 | quoted section title + file |
| `(see "Dragonmark Feats")` | 13 (via `**Feat:**` lines) | quoted section title |

⚠ **`see` is also an ordinary English verb**: `see the world` 2, `see the sun` 2, `see the daelkyr` 2, `see the cursed target` 2, `see the attacker` 2. **A bare `see the X` pattern is unusable; only `see chapter/appendix N`, `see the <Book Title>`, and `see "<Quoted Section>"` are reliable.**

⚠ **`(see the Monster Manual for its stat block)` is the *only* cross-book creature pointer form in the corpus**, and there are ~10 of them. Every other creature cross-reference relies on the bold-type convention that the scrape destroyed (prior report §4.2).

### 6.5 A resolver's minimum required normalisation, derived from the above

Every item below is backed by a measurement in this report:

1. Unicode fold: `’→'`, `“”→"`, `–—→-`, **`−`(U+2212)`→-`** (1,788 occurrences — required for *numeric* parsing, not just names)
2. Case-fold unconditionally, never branching on `edition` (MCDM counterexample, §3.3)
3. Hyphen/space equivalence (`Half Plate` ≡ `Half-Plate`; `shape-shift` ≡ `shapeshift`)
4. Plural folding with `e`-restore (`Handaxes`→`Handaxe`, not `handax`)
5. Strip trailing `[.,]` before glossary `"…"` lookup (§3.5 — ~30% of the only real links)
6. Longest-match-first over a **unified** index across ALL entity types, not per-type (§6.2 — halves the error, does not eliminate it)
7. **Require a context cue for the residual ambiguous set.** Minimum cue table: `cast (the )?X` → spell · `X spell` → spell · `X condition` → condition · `X damage` → damage type · `(Requires Attunement by X)` → class/species. The ambiguous residue is small and enumerable: `{Light, Shield, Resistance, Darkvision, Fly, Command, Darkness, Divination, Telepathy, Fear, Heal, Sleep, Blight, Gate, Web}` — **a 15-name deny-list would capture most of the damage, and it is short enough to hand-curate.**
8. Mask an entity's **own heading** before sweeping its body (self-mentions measured: 35 in `spell-descriptions.md`; 29 items self-cite via `Wand of Fireballs`-style names)

---

## 7. THE UNCLAIMED ENTITY SETS — cross-cutting, and nobody has counted them

Neither scout owns these; the prior report's gap list §9.2/§9.5 flagged some as uncounted. All counts below are new.

| entity set | file | count | derivation | grade | verdict |
|---|---|---|---|---|---|
| **Lore glossary** (heroes, villains, places, materials, organizations) | `Core/dmg-2024/lore-glossary.md` | **74** | `grep -cP "^## " Core/dmg-2024/lore-glossary.md` | **MECHANICAL** (flat H2, alphabetical) | **NODE — highest-value uncatalogued set for a *lore* RAG.** Acererak, Bahamut, Baldur's Gate, Drizzt Do'Urden, Elminster, the Harpers, Menzoberranzan, Strahd von Zarovich, Tiamat, Vecna, Waterdeep, Xanathar … Entries carry `*(pronunciation)*` italics and dense `(see chapter N)` pointers |
| **Rules glossary** | `Core/phb-2024/rules-glossary.md` | **161** | `grep -cP "^#{3,4} "` minus H1/H2 | **MECHANICAL** (+ bracketed type tags) | NODE — §3 |
| **Conditions** | ↑ + `playing-the-game.md:1202` | **15** | two sources agreeing exactly | **MECHANICAL** | NODE — §3.4 |
| **Damage types** | `rules-glossary.md:521` | **13** | table | **MECHANICAL** | NODE (~2,588 typed refs) |
| **Deities** | `Expanded/scag/welcome-to-the-realms.md:494–617` (7 pantheons) + `Core/dmg-2024/greyhawk.md:187` | **99 SCAG rows** + Greyhawk table (UNCOUNTED) | `awk '/^#### /{h=$0} /^\| \*\*/{c[h]++} END{…}'` → Faerûnian 48, Dwarven 13, Elven 12, Gnomish 9, Orc 6, Halfling 6, Drow 5 | **MECHANICAL** | **NODE.** `| Deity | Alignment | Domains | Symbol |` — gives `deity—has_domain→domain` (a *cleric subclass* — cross-cutting into the class scout's territory) and `deity—has_alignment→alignment`. ⚠ Greyhawk's table is a *different* schema: `| Name and Epithet | Home Plane | Typical Worshipers | Symbol |` — **`deity—resides_on→plane`**, not alignment |
| **Planes** | `Core/dmg-2024/cosmology.md:81` + `:233` "Tour of the Multiverse" | **17** Outer Planes (table) + **32** `###` tour entries | `sed -n '81,100p'`; `awk 'NR>233 && /^### /{n++} END{print n}'` | **MECHANICAL** | **NODE.** `| Outer Plane | Alignment |` is a clean closed edge table; each plane has `#### Layers of X` and `#### X Adventures` sub-structure |
| **Backgrounds** | `phb-2024/character-origins.md:106–346`; `efota/character-options.md:98`; `scag/backgrounds.md`; `erftlw` | **16 + 17 + 12 + 1 = 46** | `grep -rcP "^\*\*Skill Proficiencies:\*\*"` | **MECHANICAL** | **NODE** — 5 outbound edge types (§4) |
| **Species** | `character-origins.md:360–669`; `efota/character-options.md:336` | **10 + 5** (2024, via `**Creature Type:**`) + 2014 sets in `scag/races-of-the-realms.md`, `erftlw/character-creation.md` (**UNCOUNTED**) | `grep -rcP "^\*\*Creature Type:\*\*"` | **MECHANICAL** (2024) / GRAMMAR (2014) | **NODE.** Has sub-lineages at `####` (Drow/High Elf/Wood Elf under Elf) — a species→lineage hierarchy |
| **Bastion facilities** | `Core/dmg-2024/bastions.md`, `Expanded/efota/bastions-in-khorvaire.md` | **39** | `grep -rhoP "^\*(?:Level \d+) Bastion Facility\*"` → L5 ×10, L9 ×13, L13 ×11, L17 ×5 | **MECHANICAL** | NODE, thin. Fields `**Prerequisite:**` 39, `**Space:**` 39, `**Order:**` 39, `**Hirelings:**` 39, `**Craft:**` 20 — the last is a **facility→item** edge |
| **Artificer infusions** | `tcoe/artificer.md`, `erftlw/character-creation-class-artificer.md` | ~20 (`grep -c "Item: A "`) | UNCOUNTED precisely | GRAMMAR | **feature→creates→magic_item** — a relationship type that exists nowhere else. Also duplicated across TCoE and ERftLW |
| **Locations / gazetteer** | `scag/the-sword-coast-and-the-north.md` (307K), `erftlw/khorvaire-gazeteer*.md`, `erftlw/sharn-city-of-towers.md` | **111 in the SCAG file alone** (46 H3 + 65 H4 under 5 H2 regions) | `grep -oP "^#{1,5} " … \| sort \| uniq -c` | GRAMMAR (hierarchy from heading depth) / PROSE (relationships) | NODE for a lore RAG. ⚠ prior report H4 warns heading depth is not stable — verify per file |
| **Habitat / Treasure** | `Core/mm-2024/*` `**Habitat:** X, Y; **Treasure:** Z` ×247 | 12-ish closed habitat vocab (Forest 39, Hill 24, Desert 22, Underdark 20, Grassland 20, Coastal 20, Mountain 17, Swamp 12, Arctic 9, Urban, `Planar (Shadowfell)`, Any) | `grep -rhoP "^\*\*Habitat:\*\* .*" \| sed … \| tr ',' '\n' \| sort \| uniq -c` | **MECHANICAL** | **BOUNDARY — hand to the monster scout**, but note **two fields share one line separated by `;`**, same trap as `**Immunities**` |
| **NOISE — not entities** | `Core/phb-2024/*` example-of-play sidebars | `**Jared:**` 79, `**Phillip:**` 24, `**Russell:**` 23, `**Amy:**` 20, `**Maeve:**` 19 | `grep -rhoP "^\*\*[A-Z][^*]{0,40}:?\*\*" \| sort \| uniq -c \| sort -rn` | — | **⚠ These are dialogue speakers in a play-example sidebar. They occupy 165 lines with exactly the `**Label:**` shape used by real field grammars.** A generic `**X:**` field extractor mints five fictional player-characters as entities |

---

## 8. Bounds — what I did NOT look at

Per the honesty rules, stated so nobody inherits a false clear.

1. **I did not run any of the A/B correctness diffs I identified.** Three exist and all three are free: feat category (descriptor vs `| Feat | Category |` table, `feats.md:44`); equipment price (master table vs `#### Name (Price)` heading); item attunement (DMG descriptor vs `| Magic Item | Attunement |` / `| Item | Type | Attune? |`, 17 tables in the artificer chapters). I located and counted the sources; **I proved agreement for none of them.** The condition list is the one exception — I did verify 15=15 across two sources.
2. **I did not count (feat, spell) pairs** from the 140 `| Spell Level | Spells |` rows, only the rows. Cells are comma lists of 1–2 names, so the pair count is roughly 200–280, but that is an estimate, not a derivation.
3. **I did not count (background, skill) or (background, item) pairs** — only the 46 field lines. The `*Choose A or B:*` alternation in `**Equipment:**` needs a decision before counting is meaningful.
4. **I did not hand-verify the spell→spell surface** after removing common-word false positives. I know ≥58% of the 204 raw occurrences are wrong; I do not know the true number. Labelled UNCOUNTED in §5.1.
5. **I did not examine 2014-dialect spellcasting on stat blocks** (`***Spellcasting.***` prose paragraphs). My 628-pair monster→spell count is **2024-dialect only** — the 68 degraded 2014 blocks (prior report H5) contribute an unmeasured additional surface.
6. **I did not enumerate ERftLW/SCAG species, ERftLW locations, or XGtE's 205K subclass file.** The prior report already flagged XGtE `subclasses.md` as the largest uncounted population; I confirmed it holds 2 `| Spell Level | Spells |` tables and 7 `| <Class> Level | Spells |` tables but did not count its entities. That remains the corpus's biggest single blind spot and it now has two scouts who have not opened it.
7. **I did not count Mounts/Vehicles/Services equipment rows** — I located the tables (`equipment.md:1164, :1177, :1217, :1273, :1302, :1315, :1327`) and stopped.
8. **I did not test the resolver rules of §6.5 end-to-end.** Each is individually backed by a measurement, but I did not build a resolver and score it. The one place I *did* score a full pipeline is the 46-name monster-Gear set (39 exact / 5 plural / 2 orthographic), which is small and closed — it is a calibration point, not a validation.
9. **I did not check whether the 13 dragonmark feats duplicated between EFotA (2024) and ERftLW (2014) have identical spell tables.** Both files show exactly 12 `| Spell Level | Spells |` headers and 60 data rows, which is suspicious enough to be worth a diff and I did not run it. If they differ, prior report H2 (2014-vs-2024 same-name divergence) applies to feats as well as spells and stat blocks — which nobody has yet asserted.
10. **Everything here is over the 141 files on disk.** I inherited the prior report's manifest/disk verification rather than re-running it.