<!-- ARCHIVED 2026-08-02: read-only Explore scout, graph-scope deep pass (monster side — stat-block fields, type/CR, Beast census, casts-spell).
     Spawned by the D&D slot-in planning session at fa12c11; corpus = dndlorescraper
     output, 2026-07-31 scrape. Extends (does not supersede) the 2026-08-01 scoping
     reports in ../2026-08-01-dnd-rag-scoping/. Every count carries its derivation. -->

# REPORT — corpus scout 2: the MONSTER side

**Scope:** `/home/ejprice/code/python/dndlorescraper/output`, measured 2026-08-01. Read-only; every count below carries its derivation. Prior report (`REPORT-corpus-scout-1.md`) read in full; I do not re-derive its 667/596/599/68 headline or the H7b nesting result.

**Headline finding, ahead of everything else:** `Core/mm-2024/monster-lists.md` (Appendix B: Monster Lists, 2,581 lines) is an **unexploited second independent source for creature type, CR, and habitat**, and I verified it agrees with the stat blocks essentially perfectly — **CR: 500 agree / 0 mismatch**, **Beast type: sets identical (85 = 85)**, **habitat: 337/341 exact after one documented normalization**. This is the monster-side twin of the spell A/B pin the prior report recommended. It also contains a **2014→2024 stat-block rename table (59 rows)** that is a first-class edge nobody has costed.

---

## 1. Stat-block field extractability

### 1.1 The clean 2024 dialect — line grammar

```
<heading | bare>  Name
                                  <- blank
Size Type[ (Tags)], Alignment     <- META LINE (may be *italicised* in EFotA)
**AC** N **Initiative** ±N (NN)   <- COMPOUND: two fields on one line
**HP** N (NdX + N)
**Speed** N ft.[, Fly N ft. (hover)][, Swim N ft.][, Burrow N ft.][, Climb N ft.]
| Ability | Score | Mod | Save |  <- TABLE 1: Str/Dex/Con
| Ability | Score | Mod | Save |  <- TABLE 2: Int/Wis/Cha
[**Skills** …] [**Resistances** …] [**Immunities** dmg…; conditions…]
[**Vulnerabilities** …] [**Gear** …]
**Senses** <sense N ft.>; Passive Perception N
**Languages** …
**CR** N (XP N; PB +N)
Traits / Actions / Bonus Actions / Reactions / Legendary Actions   <- plain paragraphs
***Trait Name.*** body
```

**Field-line census, corpus-wide** — `for f in AC HP Speed Senses Languages CR Skills Immunities Resistances Vulnerabilities Gear; do grep -rh "^\*\*$f\*\* " --include='*.md' . | wc -l; done`

| field | count | note |
|---|---|---|
| `**AC**` | 599 | 100% of 2024 blocks |
| `**HP**` | 599 | 100% |
| `**Speed**` | **667** | label shared with 2014 dialect ⇒ 599 + 68 |
| `**Senses**` | **667** | ditto |
| `**Languages**` | **667** | ditto |
| `**CR**` | 599 | 100% |
| `**Skills**` | 441 | = 394 (2024) + 47 (2014) |
| `**Immunities**` | 256 | 2024-only vocabulary |
| `**Resistances**` | 137 | 2024-only |
| `**Vulnerabilities**` | 24 | 2024-only |
| `**Gear**` | 92 | 2024-only |
| `**Initiative**` standalone | **0** | it is *inside* the AC line: `grep -rh '^\*\*AC\*\* .*\*\*Initiative\*\*' … | wc -l` → **582** (17 blocks have no Initiative at all) |

⚠ My `**Immunities**` = 256 and `**Skills**` (2024) = 394 vs the prior report's 244/394. The 394 reconciles; **the Immunities figure does not** — mine is a direct line-start grep over all 141 files. Treat 244 as superseded, or re-derive before relying on either.

**Meta-line grammar parses 597/599 (99.7%)** with

```
^\*?((?:Tiny|Small|Medium|Large|Huge|Gargantuan)(?: or (?:…))?) ([A-Za-z]+(?: of [A-Za-z ]+)?|[A-Za-z]+ or [A-Za-z]+)(?: \(([^)]*)\))?, ([^*]+?)\*?$
```

The 2 misses are the ones the prior report already named (the `how-to-use-a-monster.md:54` teaching example; `spell-descriptions.md:206` `Huge or Smaller Construct, Unaligned`). **My regex must tolerate a leading/trailing `*`** — EFotA italicises the whole meta line (7 blocks), which the prior report's regex silently dropped.

### 1.2 Four verbatim samples, four different books

**(a) `Core/mm-2024/animals.md:1483-1503` — MM, Beast**
```
### Giant Hyena

Large Beast, Unaligned

**AC** 12 **Initiative** +2 (12)

**HP** 45 (6d10 + 12)

**Speed** 50 ft.

| Ability | Score | Mod | Save |
| --- | --- | --- | --- |
| Str | 16 | +3 | +3 |
```

**(b) `Core/mm-2024/monsters-f.md:190-215` — MM, with a family-level habitat tag two headings up**
```
## Fire Giant
Giant of the Smoldering Depths
**Habitat:** Mountain, Underdark; **Treasure:** Armaments
…
### Fire Giant
Huge Giant, Lawful Evil
**AC** 18 **Initiative** +3 (13)
**HP** 162 (13d12 + 78)
**Speed** 30 ft.
```

**(c) `Expanded/efota/sharn-inquisitives.md:110-134` — EFotA, 2024 dialect but ITALIC meta and `#### `-depth name, plus a Gear line**
```
#### Boromar Smuggler

*Small Humanoid (Halfling), Neutral Evil*

**AC** 13 **Initiative** +4 (14)

**HP** 27 (6d6 + 6)

**Speed** 40 ft.
…
**Gear** Leather Armor, Pistol, Shortsword
```

**(d) `Core/dmg-2024/magic-items-a-z.md:1107-1122` — DMG, `#####`-depth, non-numeric HP, and a MALFORMED ability table**
```
##### Avatar of Death

Medium Undead, Neutral Evil

**AC** 20 **Initiative** +3 (13)

**HP** Half the HP maximum of its summoner

**Speed** 60 ft., Fly 60 ft. (hover)

| Mod | Save |
| --- | --- |
| STR | 16 | +3 | +3 |
```

### 1.3 The 68 degraded 2014-dialect blocks — what survives

`grep -rc '^\*\*Armor Class\*\* '` → 68 in 11 files (ERftLW `friends-and-foes.md` 38, TCoE 18, MCDM 10 [the 5×2 duplicate pair], ERftLW artificer 2).

**Per-field survival sweep — this is the gap the prior report explicitly left open (its §9.1).** Derivation: parse forward from each `**Armor Class**` line to the next, collecting `^\*\*(label)\*\* `.

| field | 2014 count | 2024 equivalent | survives? |
|---|---|---|---|
| `**Armor Class**` | **68/68** | `**AC**` | ✅ renamed |
| `**Hit Points**` | **68/68** | `**HP**` | ✅ renamed |
| `**Speed**` | **68/68** | same | ✅ same label, **lowercase modes** (`fly 40 ft. (hover)` vs `Fly`) |
| `**Senses**` | **68/68** | same | ✅ but `passive perception 23` (lowercase) |
| `**Languages**` | **68/68** | same | ✅ |
| `**Challenge**` | **58/68** | `**CR**` | ⚠ **10 blocks have NO CR line at all**; 19 of the 58 are `— **Proficiency Bonus** equals your bonus` ⇒ **only 39 of 68 carry a numeric CR** |
| `**Skills**` | 47/68 | same | ✅ |
| `**Saving Throws**` | 31/68 | (folded into ability table) | ⚠ **separate field in 2014, a table column in 2024** |
| `**Damage Resistances**` | 27/68 | `**Resistances**` | ✅ renamed |
| `**Damage Immunities**` | 24/68 | (merged) | ⚠ **2024 merges damage + condition immunity into ONE `**Immunities**` line split by `;`** |
| `**Condition Immunities**` | 38/68 | (merged) | ⚠ same |
| `**Damage Vulnerabilities**` | 4/68 | `**Vulnerabilities**` | ✅ renamed |
| `**Proficiency Bonus (PB)**` | 10/68 | (in CR parenthetical) | ⚠ |
| `**Gear**` | **0/68** | `**Gear**` | ❌ **does not exist in 2014** |
| `**Habitat:**` / `**Treasure:**` | **0/68** | 247 lines | ❌ **does not exist in 2014** |
| ability scores | 0 tables | 2 tables | ❌ **collapsed to vertical one-token paragraphs** |

**Meta line: 67/68 parse if and only if alignment is made OPTIONAL** (19 blocks have none — companions/summons). One miss: `Large or smaller construct` (lowercase size range). **2014 type is LOWERCASE** (`Medium aberration`) — an exact-case join to the 2024 taxonomy loses everything.

**Name addressability:** `BARE PARAGRAPH 52 · H3 10 · H4 6` — i.e. **52/68 (76%) are not headings** (confirms prior H5).

**What "degraded" concretely looks like — `Expanded/erftlw/friends-and-foes.md:207-240`, verbatim:**
```
Belashyrra

Medium aberration, chaotic evil

**Armor Class** 19 (natural armor)

**Hit Points** 304 (32d8 + 160)

**Speed** 40 ft., fly 40 ft. (hover)

STR

24 (+7)

DEX

21 (+5)

CON

20 (+5)
```
The name `Belashyrra` is a bare paragraph indistinguishable from body prose; the six ability scores are twelve separate one-token paragraphs where the 2024 tier uses two markdown tables. **69 bare `^STR$` lines exist** (`grep -rh '^STR$' --include='*.md' . | wc -l` → 69, across 12 files) — that is 69 collapsed ability blocks vs 68 stat blocks, the extra being one in `xgte/spells.md`. This is HTML→markdown conversion damage, not a book difference.

**One nuance the prior report did not have:** MCDM's 10 blocks are *less* degraded — they carry a proper Title-Case meta line (`MCDM/tir/tir.md:1359` `Medium Humanoid, Any Alignment`) under a real `### Agent (Shadowmaster)` heading, while still using the 2014 field vocabulary and the collapsed STR runs. **"2014 dialect" is at least two sub-dialects, not one.**

---

## 2. The type taxonomy — is it a closed set?

**Derivation** (the instrument, pasted; run from corpus root):

```python
import re, pathlib, collections
SIZES = 'Tiny|Small|Medium|Large|Huge|Gargantuan'
pat = re.compile(r'^\*?((?:'+SIZES+r')(?: or (?:'+SIZES+r'))?) '
                 r'([A-Za-z]+(?: of [A-Za-z ]+)?|[A-Za-z]+ or [A-Za-z]+)'
                 r'(?: \(([^)]*)\))?, ([^*]+?)\*?$')
t = collections.Counter()
for f in sorted(pathlib.Path('.').rglob('*.md')):
    L = f.read_text().splitlines()
    for i, l in enumerate(L):
        if l.startswith('**AC** '):
            j = i-1
            while j >= 0 and not L[j].strip(): j -= 1
            m = pat.match(L[j])
            t[m.group(2) if m else None] += 1
for k, v in t.most_common(): print(f'{v:5d}  {k}')
```

| type | 2024 blocks | Appendix B (distinct names) |
|---|---|---|
| Beast | **134** | 91 |
| Humanoid | 70 | 45 |
| Monstrosity | 60 | 59 |
| Fiend | 52 | 54 |
| Dragon | 52 | 20 † |
| Undead | 41 | 38 |
| Aberration | 37 | 35 |
| Elemental | 33 | 32 |
| Fey | 27 | 25 |
| Construct | 23 | 20 |
| Celestial | 18 | 17 |
| Plant | 17 | 17 |
| Giant | 14 | 14 |
| Ooze | 6 | 6 |
| *Swarm of Tiny Beasts* | 6 | — |
| *Swarm of Medium Fiends* | 2 | — |
| *Celestial or Fiend* | 2 | — |
| *Swarm of Tiny Undead* | 1 | — |
| *Swarm of Small Fiends* | 1 | — |
| *Swarm of Tiny Monstrosities* | 1 | — |
| unparsed | 2 | — |

† Appendix B collapses true dragons to `Black dragons (all)` family rows; the 50 MM Dragon stat blocks are the 4 age categories × 10 colours + strays.

**Verdict: type is a closed set of 14 — *after* two normalizations, and it is NOT closed as written.**

1. **11 blocks are `Swarm of <Size> <PluralType>`**, a composite the meta line encodes in the type slot. Appendix B files them under the singular base type. A design must decide: `type=Beast, is_swarm=true` (Appendix B's model) or a 20-value enum.
2. **2 blocks are `Celestial or Fiend`** (a disjunction), and 1 alignment value is `Fey, or Fiend (Your Choice), Neutral` — the type slot can hold a *choice*, not a value.
3. **2014 types are lowercase** and add nothing new (10 distinct: aberration, beast, celestial, construct, elemental, fey, fiend, humanoid, monstrosity, undead) — a `.title()` fold makes the union exactly 14.

**⚠ My counts differ from the prior report's on 8 of 14 types** (Beast 134 vs 129, Humanoid 70 vs 63, Dragon 52 vs 51, Undead 41 vs 39, Aberration 37 vs 36, Elemental 33 vs 32, Fey 27 vs 26, Construct 23 vs 20, Celestial 18 vs 16). Its published buckets sum to **573 of 599**; mine sum to **597 of 599**. The difference is the italic-meta EFotA blocks and `(Tags)` handling. **Use mine, or re-derive; do not average them.**

---

## 3. THE BEAST CENSUS — the wild-shape target set

### 3.1 Counts

- **134 Beast-typed 2024 stat blocks / 91 distinct names** (`type=='Beast'`, above).
- **85 distinct Beast names live in the 2024 Monster Manual** — this is the wild-shape universe.
- The other 6 distinct names are **not monsters**: `Beast of the Land`/`of the Sea`/`of the Sky` (PHB ranger companions), `Bestial Spirit` + `Giant Insect` (PHB spell-embedded summons), `Giant Fly` (a DMG magic-item summon). All 6 carry `**CR** None`.
- The 134−91 = 43 surplus blocks are **PHB `creature-stat-blocks.md` reprints of MM animals** — `Core/phb-2024/creature-stat-blocks.md` contributes **43 Beast blocks and ZERO new Beast names**. A naive count says 134; the truth is 85.
- **6 `Swarm of Tiny Beasts`** blocks are typed separately in the meta line but filed under Beast by Appendix B (Swarm of Bats/Insects/Piranhas/Rats/Ravens/Venomous Snakes).

### 3.2 CR distribution — 85 distinct MM Beasts

| CR | 0 | 1/8 | 1/4 | 1/2 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| n | **24** | 9 | 15 | 8 | 8 | 8 | 3 | 3 | 3 | 2 | 1 | 1 |

**56 of 85 (66%) are CR ≤ 1/2.** CR 2+ = 21. Ceiling is **CR 8 (Tyrannosaurus Rex)**; the CR ≥ 1 roster is exactly 29 creatures, enumerable in one line. (Over all 134 blocks incl. duplicates and non-MM: CR 0→40, 1/8→16, 1/4→23, 1/2→15, 1→13, 2→8, 3→3, 4→4, 5→3, 6→2, 7→1, 8→1, None→5.)

Size: Large 28 · Medium 21 · Tiny 16 · Huge 12 · Small 8. Tags: 78 untagged, **7 `(Dinosaur)`**.

### 3.3 Speeds — the wild-shape restriction axis

Over the 85 distinct MM Beasts: **walk-only 28 · Swim 26 · Climb 20 · Fly 10 · Burrow 2.**

- **Fly (10):** Bat, Blood Hawk, Eagle, Giant Bat, Giant Wasp, Hawk, Owl, Pteranodon, Raven, Vulture.
- **Swim (26):** Archelon, Black Bear, Constrictor Snake, Crab, Crocodile, Frog, Giant Constrictor Snake, Giant Crab, Giant Crocodile, Giant Frog, Giant Octopus, Giant Seahorse, Giant Shark, Giant Squid, Giant Toad, Giant Venomous Snake, Hippopotamus, Hunter Shark, Killer Whale, Octopus, Piranha, Plesiosaurus, Polar Bear, Reef Shark, Seahorse, Venomous Snake.
- **Burrow (2)** — Badger and Giant Badger.

**Speed grammar is fully mechanical in the 2024 dialect**: `N ft.` base plus comma-separated `<Mode> N ft.[ (rider)]` where Mode ∈ {Fly, Swim, Climb, Burrow} (Title Case) and rider ∈ {`(hover)`, `(snake form only)`, `(tiger form only)`, `(wolf form only)`, `( when rolling downhill)`}. **45 blocks carry `Fly N ft. (hover)`** — hover is a rider, not a mode.

⚠ **Case hazard:** 9 blocks use lowercase `fly … (hover)`, 8 `fly`, 3 `climb`, 1 `swim` — a case-sensitive mode match loses ~21 speed entries silently.

### 3.4 2014-era expansion Beasts — counted separately as asked

**6 Beast-typed 2014-dialect blocks**, and **none of them is a monster you can wild-shape into**:

| file:line | meta | Speed | CR |
|---|---|---|---|
| `Expanded/erftlw/friends-and-foes.md:464` | `Medium beast, unaligned` | `40 ft.` | 1 (200 XP) |
| `Expanded/erftlw/friends-and-foes.md:524` | `Medium beast, unaligned` | `50 ft.` | 1/4 (50 XP) |
| `Expanded/tcoe/magical-miscellany.md:310` | `Small beast` | `30 ft.; climb 30 ft. (Land only); fly 60 ft. (Air only); swim 30 ft. (Water only)` | — (PB) |
| `Expanded/tcoe/ranger.md:344` | `Medium beast` | `40 ft., climb 40 ft.` | — (PB) |
| `Expanded/tcoe/ranger.md:394` | `Medium beast` | `5 ft., swim 60 ft.` | — (PB) |
| `Expanded/tcoe/ranger.md:444` | `Small beast` | `10 ft., fly 60 ft.` | — (PB) |

The 4 TCoE ones are the *Summon Beast* spirit and the *Beast of the Land/Sea/Sky* companions — i.e. **cross-edition duplicates of PHB-2024 entries** (prior §7.3), not new content. **The 2014 expansions add exactly 2 real Beasts** (both ERftLW). ⚠ Note `magical-miscellany.md:310`'s speed uses **semicolons** and `(Land only)` mode gates — a comma-splitting speed parser mangles it.

---

## 4. Monster → spell references

### 4.1 The structural pattern — three distinct mechanisms

**(i) 2024 `***Spellcasting.***` trait + frequency-bucket list lines.** `Core/mm-2024/monsters-l.md:377-385` (Lich), verbatim:

```
***Spellcasting.*** The lich casts one of the following spells, using Intelligence as the spellcasting ability (spell save DC 20):

**At Will:** Detect Magic, Detect Thoughts, Dispel Magic, Fireball (level 5 version), Invisibility, Lightning Bolt (level 5 version), Mage Hand, Prestidigitation

**2/Day Each:** Animate Dead, Dimension Door, Plane Shift

**1/Day Each:** Chain Lightning, Finger of Death, Power Word Kill, Scrying
```

Bucket label vocabulary is a **closed 8-value set**: `At Will:` 115 · `1/Day Each:` 79 · `1/Day:` 20 · `2/Day Each:` 16 · `2/Day:` 9 · `3/Day:` 2 · `3/Day Each:` 1 · `1/Day Each (Sage Only):` 1. (`grep -rhoP '^\*\*[^*]+\:\*\* '` inside block spans.)

**(ii) 2024 inline "casts X" in an action/reaction body.** `monsters-l.md:389`:
> `***Protective Magic.*** The lich casts Counterspell or Shield in response to the spell's trigger, using the same spellcasting ability as Spellcasting.`

`monsters-l.md:397`:
> `***Frightening Gaze.*** The lich casts Fear, using the same spellcasting ability as Spellcasting.`

**(iii) 2014 dialect — a completely different, LOWERCASE grammar.** `Expanded/erftlw/friends-and-foes.md:1155-1161`:
```
***Spellcasting.*** Illmarrow is a 20th-level spellcaster. Her spellcasting ability is Intelligence (spell save DC 23, +15 to hit with spell attacks). Illmarrow has the following wizard spells prepared:

Cantrips (at will): chill touch (see "Actions" below), fire bolt, mage hand, prestidigitation, ray of frost

1st level (4 slots): magic missile, shield, sleep
```
Line grammar `^(Cantrips \(at will\)|\d+(st|nd|rd|th) level \(\d+ slots?\)|At will|\d+/day( each)?):` — **44 such lines corpus-wide**, all with **lowercase spell names**, plus per-line **slot counts** the 2024 dialect does not carry.

### 4.2 Counts (derived)

Instrument (span each block from its `**AC**`/`**Armor Class**` line to the next one or the next heading, whichever is first):

```python
sc     = [b for b in blocks if '***Spellcasting' in b['body']]
lists  = [b for b in blocks if re.search(r'^\*\*(At Will|\d+/Day[^*]*)\:\*\*', b['body'], re.M)]
inline = [b for b in blocks if re.search(r'\bcasts? [A-Z*]', b['body'])]
```

| mechanism | blocks | 2024 | 2014 |
|---|---|---|---|
| `***Spellcasting…***` trait | **129** | 124 | 5 |
| frequency-bucket list lines | **124** | 124 | 0 |
| inline `casts X` sentence | **91** | 91 | 0 |
| **UNION — any spell reference** | **152 of 667 (22.8%)** | 147 | 5 |

### 4.3 Is the list mechanically parseable? — YES, at 100%

With a **paren-aware comma splitter** (commas at nesting depth 0 only):

- **630 monster→spell edge tokens** over **150 distinct spell names**.
- **630/630 resolve exactly (case-sensitive) to a `### <name>` heading in `Core/phb-2024/spell-descriptions.md`. Zero unresolved.**
- **114 edges carry a rider in parentheses** that is itself structured: `Hold Person (level 4 version)` (upcast level), `Invisibility (self only)` (target restriction), `Mage Armor (included in AC)`.
- Bucket split: At Will 332 · 1/Day Each 248 · 2/Day Each 40 · 1/Day 20 · 2/Day 9 · 3/Day 2 · 3/Day Each 2 · Sage Only 2.
- Top targets: Detect Magic 46 · Mage Hand 32 · Detect Thoughts 25 · Minor Illusion 20 · Plane Shift 19 · Thaumaturgy 18 · Invisibility 17. Top casters: Lich 15 · Archmage 14 · Ancient Bronze Dragon / Couatl / Sphinx of Lore 11.

⚠ **A naive `split(',')` gives 655 tokens with 38 garbage** — every one from a comma *inside* the rider parenthetical, e.g. `Shapechange (Beast or Humanoid form only, no Temporary Hit Points gained from the spell, and no Concentration…)` shreds into three fake spells. **That is the single sharpest trap in this section, and it is silent** (the garbage tokens look like plausible names in a count).

For inline `casts X`: **118 mentions across 87 blocks, 40 distinct spell strings, 118/118 resolve to a PHB spell name.** ⚠ Recall bound: `\bcasts? [A-Z*]` fires **125** times in block bodies, so my 118 is **~94% recall, not 100%** — the 7 shortfall are multi-spell sentences (`casts Counterspell or Shield`) where the second spell is after an `or`. Grammar, not prose, but a designed one.

---

## 5. Monster → condition / mechanic references (lighter pass)

**Two structurally different channels, and only one is edge-worthy.**

**(a) `**Immunities**` / `**Resistances**` / `**Vulnerabilities**` — MECHANICAL and semicolon-delimited.** 2024 merges damage types and conditions into one line split by `;`: `144 of 256` Immunities lines contain a semicolon. Verbatim (`grep -rh '^\*\*Immunities\*\* ' . | sort -u`):
```
**Immunities** Acid, Necrotic, Poison; Charmed, Exhaustion, Frightened, Grappled, Paralyzed, Petrified, Poisoned, Prone, Restrained, Stunned, Unconscious
```
Vocabulary is closed: **10 damage types** (Poison 129, Fire 49, Necrotic 28, Cold 22, Lightning 19, Acid 18, Psychic 17, Thunder 4, Radiant 3, Slashing 2) and **14 conditions** (Poisoned 132, Charmed 103, Exhaustion 88, Frightened 87, Paralyzed 63, Petrified 53, Prone 43, Restrained 34, Grappled 33, Deafened 26, Stunned 22, Unconscious 21, Blinded 14, Incapacitated 2).

**(b) Conditions *inflicted* in trait/action prose — GRAMMAR, via one stable idiom.** `grep -c 'has the .* condition'` over block bodies → **457 occurrences**, and the phrase `has the <X> condition` is used consistently (Prone 92, Grappled 60, Poisoned 56, Restrained 53, Incapacitated 42, Frightened 35, Paralyzed 32, Charmed 16, Blinded 16, Unconscious 12, Stunned 11, Petrified 7, Invisible 5, Deafened 4). **22 of the 457 are conjunctions** — `has the Blinded and Restrained condition` (8), `Charmed or Poisoned` (2), etc. **402 of 667 blocks (60%) reference ≥1 condition by name.**

**(c) Monster → monster: MOSTLY NOISE. Do not build this edge from name matching.** Longest-match-first over the 596-name index inside block bodies yields 62 (source, target) pairs across 54 blocks — and the top hits are **false**: `Spider` ×21 is 18 × the trait `***Spider Climb.***` + `Spider Queen` (a deity); `Shadow` ×12 is `Shadow Stealth` / `Shadow Strike` / `Shadow Shapes`. Genuine references are rare and phrase-marked: `'stat block'` 10, `'see its entry'` 3, `'Monster Manual'` 3 (e.g. `friends-and-foes.md`: *"transforms into a spectator (see its entry in the Monster Manual)"*).

**(d) Named mechanics that ARE stable enough to be a shared node:** `Magic Resistance` 98 · `Legendary Resistance` 53 · `Pack Tactics` 31 · `uses Spellcasting` 26. **2,419 `***Name.***` trait/action entries** exist across all 667 blocks — that is the reusable-trait population, uncharacterised beyond this count.

---

## 6. THE FIND — `Core/mm-2024/monster-lists.md` is a free correctness oracle

Structure (`grep -n '^#\{2,3\} ' Core/mm-2024/monster-lists.md`):

| section | shape | content |
|---|---|---|
| `## Monster Conversions` → `### Stat Block Conversions` | 2-col table | **59 rows, 2014 name → 2024 name** |
| `## Monsters by Habitat` | 12 × `| CR | Monsters |` table | 877 (name, habitat) pairs, 439 distinct monsters |
| `## Monsters by Creature Type` | 14 × bullet-free name lists | 473 (name, type) pairs |
| `## Monsters by Group` | 12 × name lists | 71 (name, group) pairs |
| `## Monsters by Challenge Rating` | 30 × name lists | **501 (name, CR) pairs** |

### Oracle results (each diffed against the stat-block-derived values)

**CR: `agree 500 · mismatch 0 · appendix-name-with-no-block 1`.** The single miss is `Yuan-ti Malison`, which the MM prints as three blocks `##### Yuan-ti Malison (Type 1|2|3)` under `### Yuan-ti Malisons` (`monsters-y.md:299/357/413`) — a genuine 1-name→3-blocks fan-out, not a defect.

**Creature type — Beast: sets are IDENTICAL.** Appendix B lists 91 Beasts; my derivation finds 91 distinct Beast names. The 6-each-way set difference is fully explained: Appendix B includes the 6 `Swarm of …` blocks (which the meta line types as `Swarm of Tiny Beasts`), and my side includes the 6 non-MM summons/companions. **Restricted to the MM and with swarms removed, the sets are equal: 85 = 85, `(apB - swarms) == sbMM_Beasts` → `True`.**

**Habitat: 337/341 exact match** after dropping `Planar (…)` tokens from the inline side (Appendix B has no Planar table — that axis is inline-only, 124 blocks). Remaining 4 real conflicts: `Dust Mephit` (inline Planar-only / appendix Desert), `Ice Mephit` (/Arctic), `Mud Mephit` (/Swamp), `Stone Giant` (appendix adds Hill).

**Habitat coverage is complementary, not redundant** — inline `**Habitat:**` lines appear **247 times, all 247 under an H2 family heading** (`depth == 2`, exactly), covering **406 of 599 blocks** by inheritance. **`animals.md`'s 96 blocks — the entire Beast core — have NO inline habitat line.** For Beasts, **Appendix B is the only habitat source in the corpus.** That is decisive if habitat-filtered wild-shape queries are in scope.

Habitat vocabulary: 11 natural (Underdark 73, Forest 48, Urban 35, Hill 32, Mountain 30, Grassland 27, Desert 27, Coastal 21, Swamp 19, Arctic 13, Underwater 10) + `Any` 36 + `Planar (<plane>)` with ~18 plane values. Treasure vocabulary is closed at 7: None 67 · Any 51 · Armaments 43 · Individual 32 · Relics 29 · Arcana 29 · Implements 19.

⚠ **`Planar (Acheron, Feywild)` contains a comma inside parentheses** and shreds under naive splitting — the *same* hazard as the spell riders in §4.3. One paren-aware splitter fixes both.

---

## 7. CATALOG — every field and relationship, with verdicts

Legend: **MECHANICAL** = regex on a fixed line shape, no ambiguity · **GRAMMAR** = needs a designed per-dialect parser · **PROSE** = semantic inference. `E` = edge, `F` = field, per the stated dividing line.

| # | name | E/F | evidence (file:line) | mult. | count (derivation) | grade | hazards |
|---|---|---|---|---|---|---|---|
| 1 | **creature TYPE** | **F** | `mm-2024/monsters-f.md:213` `Huge Giant, Lawful Evil` | 1 per block | 597/599 (meta regex §2) | MECHANICAL | 11 `Swarm of …` composites; 2 `X or Y` disjunctions; 2014 lowercase; EFotA italic wrapper |
| 2 | **CR** | **F** | `monsters-f.md:229` `**CR** 9 (XP 5,000; PB +4)` | 1 | 599/599; **oracle 500/0** vs Appendix B | MECHANICAL | 18 blocks are `CR None`; 2014 only 39/68 numeric |
| 3 | **size** | **F** | same meta line | 1 | 597/599 | MECHANICAL | `Huge or Smaller` / `Medium or Small` ranges (3 blocks) |
| 4 | **alignment** | **F** | same meta line | 1 | 578/599 (11 values) | MECHANICAL | 19 of 68 in 2014 have none; 1 value is `Fey, or Fiend (Your Choice), Neutral` |
| 5 | **creature TAGS** | F or E | `sharn-inquisitives.md:112` `*Small Humanoid (Halfling), …*` | 0..n | **144/599 tagged, 23 distinct tags** | MECHANICAL | overlaps `Monsters by Group` (13 groups) but is not identical to it |
| 6 | **speed (base)** | **F** | `monsters-f.md:219` `**Speed** 30 ft.` | 1 | 599 | MECHANICAL | — |
| 7 | **speed MODES (fly/swim/burrow/climb)** | **F** (map) | `animals.md` Bat `**Speed** 5 ft., Fly 30 ft.` | 0..4 | Fly 128 · Swim 94 · Climb 89 · Burrow 33 (2024 blocks); MM Beasts: 10/26/20/2 | MECHANICAL | ~21 lowercase mode tokens; `(hover)` is a rider not a mode; TCoE uses `;` + `(Land only)` gates |
| 8 | **AC** | **F** | `**AC** 18 **Initiative** +3 (13)` | 1 | 599 | MECHANICAL | **compound line — Initiative is on it** |
| 9 | **Initiative** | **F** | same | 1 | **582** (`grep -c '^\*\*AC\*\* .*\*\*Initiative\*\*'`) | MECHANICAL | 17 blocks lack it; 0 standalone lines |
| 10 | **HP** | **F** | `**HP** 162 (13d12 + 78)` | 1 | 599 | MECHANICAL | non-numeric values exist: `Half the HP maximum of its summoner` (`magic-items-a-z.md:1113`) |
| 11 | **ability scores + saves** | **F** ×6 | `monsters-f.md:221` two `| Ability | Score | Mod | Save |` tables | 6 | 562 blocks × 2 tables | MECHANICAL | **THREE header shapes: `| Ability | Score | Mod | Save |` ×1124, `|  |  | Mod | Save |` ×72 (36 blocks), `| Mod | Save |` ×2 (malformed, 4 cells under 2 headers).** Row labels also split `Str` 580 / `STR` 19. 2014 has no table at all |
| 12 | **senses** | **F** (map) | `**Senses** Darkvision 60 ft.; Passive Perception 10` | 1..n | 599; Darkvision 277 · Blindsight 62 · Truesight 36 · Tremorsense (semicolon-split) | MECHANICAL | 2014 lowercases (`passive perception 23`) |
| 13 | **languages** | **F** or **E** | `**Languages** Primordial (Ignan)` | 0..n | 599; None 191 · Common 182 · Draconic 61 · telepathy 120 ft. 39 | GRAMMAR | mixes languages with **telepathy ranges** and with prose (`Common plus one other language` ×30, `understands the languages you speak` ×17) — three different things in one field |
| 14 | **damage immunity / resistance / vulnerability** | **F** (set) | `**Immunities** Acid, Necrotic, Poison; Charmed, …` | 0..n | Imm 256 · Res 137 · Vuln 24 | MECHANICAL | **`;` splits damage from conditions in 2024 but they are TWO SEPARATE FIELDS in 2014** |
| 15 | **condition immunity** | **E**→Condition | same line, after `;` | 0..n | 14 distinct conditions, 700 tokens (§5a) | MECHANICAL | as above |
| 16 | **HABITAT (inline)** | **E**→Habitat | `monsters-f.md:194` `**Habitat:** Mountain, Underdark; **Treasure:** Armaments` | 1..n | **247 lines → 406/599 blocks by H2 inheritance** | MECHANICAL | **family-level, not block-level**; `Planar (Acheron, Feywild)` comma-in-paren; **zero coverage of `animals.md`** |
| 17 | **HABITAT (Appendix B)** | **E**→Habitat | `monster-lists.md:88-368` | 1..n | **877 pairs / 439 monsters**; 337/341 agree with #16 | MECHANICAL | no Planar axis; 4 real conflicts (3 mephits + Stone Giant) |
| 18 | **TREASURE class** | **F** | same line as #16 | 0..n | 247 lines, **7-value closed set** | MECHANICAL | co-located with Habitat |
| 19 | **GEAR** | **E**→Equipment | `sharn-inquisitives.md:130` `**Gear** Leather Armor, Pistol, Shortsword` | 0..n | **92 blocks · 191 tokens · 46 distinct** | MECHANICAL | **does not exist in 2014 (0/68)**; counts in parens (`Daggers (10)`); I did **not** join these to the PHB equipment list |
| 20 | **CASTS-SPELL (frequency lists)** | **EDGE** ✅ | `monsters-l.md:379` `**At Will:** Detect Magic, …` | 0..n | **630 tokens / 150 spells / 124 blocks; 630/630 resolve to PHB headings** | MECHANICAL | **naive `split(',')` yields 38 garbage tokens**; bucket + upcast rider must be edge properties |
| 21 | **CASTS-SPELL (inline action)** | **EDGE** | `monsters-l.md:397` `The lich casts Fear, using the same spellcasting ability` | 0..n | **118 mentions / 87 blocks; 118/118 resolve — but ~94% recall (125 candidates)** | GRAMMAR | `casts A or B` drops B; must exclude the boilerplate `casts one of the following spells` (201 of 319 `cast` tokens) |
| 22 | **CASTS-SPELL (2014 dialect)** | **EDGE** | `friends-and-foes.md:1157` `Cantrips (at will): chill touch …` | 0..n | **44 list lines / 5 blocks** — spell tokens **UNCOUNTED** | GRAMMAR | **lowercase names ⇒ exact-case join fails** (same shape as prior report's H6); carries slot counts 2024 lacks |
| 23 | **INFLICTS-CONDITION** | **EDGE** | `monsters-l.md:375` `the target has the Paralyzed condition until…` | 0..n | **457 `has the X condition` occurrences; 402/667 blocks touch ≥1 condition** | GRAMMAR | 22 conjunctive (`Blinded and Restrained`); 2014 lowercases and drops the idiom entirely |
| 24 | **2014→2024 EQUIVALENT-OF** | **EDGE** | `monster-lists.md:29-88` `| Gynosphinx | Sphinx of Lore |` | 1:1 | **59 rows** | MECHANICAL | left side has no stat block in this corpus (the 2014 MM is not scraped) — it is a *name alias*, useful for retrieval, not a monster node |
| 25 | **MEMBER-OF-GROUP** | **E**→Group | `monster-lists.md:1351` `### Angels` → `Deva` | 0..n | **71 pairs / 12 groups** | MECHANICAL | 10 rows are family placeholders (`Black dragons (all)`), not stat-block names |
| 26 | **type/CR via Appendix B** | oracle | `monster-lists.md:369`, `:1517` | 1 | **473 type pairs · 501 CR pairs** | MECHANICAL | Dragon section lists families not blocks (20 vs 50) |
| 27 | **REFERENCES-MONSTER** | ~~edge~~ | `friends-and-foes.md:275` `(see its entry in the Monster Manual)` | 0..n | 62 candidate pairs, **majority false** (§5c) | PROSE | **`Spider` 21/21 hits are `Spider Climb`.** Recommend NOT building |
| 28 | **named mechanics** | F (tag) | `Legendary Resistance (3/Day)` | 0..n | Magic Resistance 98 · Legendary Resistance 53 · Pack Tactics 31 | MECHANICAL | 2,419 `***Name.***` entries total, otherwise uncharacterised |
| 29 | **block section structure** | F | `monsters-f.md:231` bare `Traits` | — | Actions 597 · Traits 377 · Bonus Actions 159 · Reactions 70 · **Legendary Actions 43** | MECHANICAL | plain paragraphs, not headings (prior H10); **zero `Lair Actions` in this scrape** |
| 30 | **name addressability** | key | — | — | 2024: H3 315 · H4 216 · H2 52 · H5 15 · bare 1. 2014: **bare 52** · H3 10 · H4 6 | GRAMMAR | confirms "never key on heading depth"; **2024 blocks span H2–H5** |

### Verdicts against your stated expectation

- **Type and CR are FIELDS — confirmed.** Both are single scalars on one entity, both are ~100% mechanical, and both have an independent oracle. Neither has attributes of its own.
- **Casts-spell is an EDGE — confirmed, and it is the strongest edge on the monster side.** Both endpoints are first-class entities with inbound questions ("what casts Fireball?" / "what does a Lich cast?"), and the edge itself carries two properties (frequency bucket, upcast rider) — which is definitionally an edge, not a field.
- **Two your brief did not name, and I judge them EDGES:** **habitat** (#16/#17 — Underdark and Forest each have 70–130 inbound members and an obvious "what lives in the Underdark at CR ≤ 2" question) and **gear** (#19 — `Longbow` is already a PHB equipment entity). **Condition** (#15/#23) is a borderline edge: `Poisoned` is a rules-glossary entity with real inbound questions, but the *inflicts* side is GRAMMAR-grade, so I would build the immunity edge (mechanical) and defer the inflicts edge.
- **Creature tag (#5) is a FIELD that wants to be an edge** and I would leave it a field: `Demon`/`Devil`/`Dinosaur` duplicate `Monsters by Group` imperfectly, and reconciling them is work with no query behind it yet.

---

## 8. Hazards new to this pass (not in prior H1–H10)

| id | hazard | why it fails silently |
|---|---|---|
| **M1** | **Comma inside parentheses**, in *three* places: spell riders (`Shapechange (Beast or Humanoid form only, …)`), habitat (`Planar (Acheron, Feywild)`), gear (`Daggers (10)` is safe, but the pattern isn't). | naive `split(',')` turns 630 clean spell edges into 655 with 38 fakes that look like real names in a count |
| **M2** | **THREE ability-table header shapes.** Prior H8 says "two tables not one" — true, but incomplete: 36 blocks use `|  |  | Mod | Save |` and 1 uses a malformed `| Mod | Save |` with 4 body cells. | an extractor keyed on the literal `| Ability | Score | Mod | Save |` loses all six scores for 37 blocks and reports 562 clean parses that look like 100% |
| **M3** | **`**Initiative**` has zero standalone lines** — it is embedded in the `**AC**` line in 582 blocks. | a line-start field parser returns 0 Initiative values and the field looks "not in the corpus" |
| **M4** | **`animals.md` has no `**Habitat:**` line** — the whole Beast core is habitat-less inline. Only Appendix B has it. | a habitat-filtered Beast query returns empty and looks like "no beasts in forests" |
| **M5** | **Case, in four independent places**: 2014 types lowercase, 2014 senses lowercase, 2014 spell names lowercase, and 21 lowercase speed-mode tokens *in the 2024 tier*. | every one is an exact-string join that returns fewer rows, never an error |
| **M6** | **EFotA italicises the whole meta line** (7 blocks) and uses `####` depth. This is a 2024-edition book behaving unlike the other 2024 books. | a meta regex without `\*?` anchors drops them; the prior report's type histogram is short by 26 blocks, partly for this reason |
| **M7** | **`**Immunities**` merges two 2014 fields.** `Damage Immunities` + `Condition Immunities` → one `;`-split line. | a naive cross-edition union produces monsters "immune to Poisoned" and "immune to poison" as distinct facts |
| **M8** | **Beast dedup: 134 blocks, 91 names, 85 real MM monsters.** PHB reprints 43 animals verbatim with zero new names. | "how many beasts can I wild-shape into" answers 134, or 91, and both are wrong |
| **M9** | **`Yuan-ti Malison` is one Appendix-B name over three stat blocks** (`(Type 1|2|3)`). | the only CR-oracle miss; a strict oracle assertion would fail the build on a correct corpus |
| **M10** | **`Swarm of Tiny Beasts` is in the type slot.** The meta line and Appendix B disagree on modeling by design. | any Beast query silently includes or excludes 6 swarms depending on which source you read |

---

## 9. BOUNDS — what I did NOT look at

1. **I did not read the bodies of any trait or action.** All 2,419 `***Name.***` entries are counted, not characterised. Damage types dealt, save DCs, attack bonuses, recharge notation, and reach/range are **UNCOUNTED**.
2. **I did not join `**Gear**` (46 distinct tokens) to `phb-2024/equipment.md`.** Whether every gear token resolves to an equipment entity is **untested** — I am asserting the field is mechanical, not that the edge closes.
3. **I did not join `**Languages**` to any language entity list,** and I did not separate its three co-mingled contents (languages / telepathy ranges / prose clauses).
4. **I did not count spell tokens in the 44 2014-dialect spell-list lines** (row #22). I established the grammar and the lowercase hazard; the edge count is **UNCOUNTED**.
5. **I did not verify Appendix B's `Monsters by Group` (71 pairs) or `Stat Block Conversions` (59 rows) against anything.** The CR/type/habitat oracles are verified; those two are counted only.
6. **I did not check whether the 2014 stat blocks have an Appendix-B analogue** in TCoE/ERftLW/XGtE. Everything in §6 is MM-2024-only.
7. **I did not measure legendary/lair/regional structure beyond section-label counts.** Note `Lair Actions` returns **zero** occurrences inside stat-block spans corpus-wide — whether the MM has lair actions elsewhere (under a `### <Monster> Lair` H3 outside the block span) I **did not check**, and that is the most likely place I have a false negative.
8. **The Habitat→block inheritance rule I measured (`hab` resets at each H2) is my model, not the book's.** It yields 406/599 and agrees with Appendix B at 337/341, which is strong evidence but not proof; I did not audit the 65 inline-only monsters individually.
9. **Beast speeds are measured on the 85 distinct MM names.** I did not check whether any PHB reprint disagrees with its MM twin on speed, CR, or AC — the prior report asserts "identical meta lines" for the ~48 reprints, and I **did not re-verify that** for the non-meta fields.
10. **Every count is over the 141 files present**, and the MCDM `tir.md` / `the-illrigger-revised.md` duplicate pair (prior D1) is **included, undeduplicated**, in every 2014-dialect figure here — so the 68 is really **63 distinct blocks + 5 duplicated**.