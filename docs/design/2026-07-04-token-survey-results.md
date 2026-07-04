# Token-Calibration Survey — Summary

## Recommended ceiling

**CLAUDE_PER_VOYAGE_CEILING = 1.78** — max over surveyed projects of each project's token-weighted p95 ratio, rounded up to 2 decimals.

Per-project token-weighted p95 (the inputs to the max):

- `lore`: 1.7041
- `odoo`: 1.7760
- `di`: 1.7291

## Per project

| scope | N | voyage tok | claude tok | tok-wt ratio | file mean | file median | file p5 | file p95 | file max | tok-wt p95 |
|---|---|---|---|---|---|---|---|---|---|---|
| lore | 39 | 151201 | 245470 | 1.6235 | 1.6318 | 1.6376 | 1.4762 | 2.0000 | 2.0909 | 1.7041 |
| odoo | 933 | 1184936 | 1874016 | 1.5815 | 1.7227 | 1.7009 | 1.5074 | 2.0000 | 2.6250 | 1.7760 |
| di | 144 | 479054 | 735437 | 1.5352 | 1.5793 | 1.5824 | 1.3331 | 1.7833 | 2.0611 | 1.7291 |
| **overall** | 1116 | 1815191 | 2854923 | 1.5728 | 1.7010 | 1.6851 | 1.4716 | 1.9952 | 2.6250 | 1.7464 |

## Per extension (within project)

| scope | N | voyage tok | claude tok | tok-wt ratio | file mean | file median | file p5 | file p95 | file max | tok-wt p95 |
|---|---|---|---|---|---|---|---|---|---|---|
| lore .md | 11 | 32027 | 48654 | 1.5192 | 1.5101 | 1.5041 | 1.4390 | 1.5621 | 1.5621 | 1.5621 |
| lore .py | 28 | 119174 | 196816 | 1.6515 | 1.6796 | 1.6674 | 1.5182 | 2.0000 | 2.0909 | 1.7057 |
| odoo .py | 933 | 1184936 | 1874016 | 1.5815 | 1.7227 | 1.7009 | 1.5074 | 2.0000 | 2.6250 | 1.7760 |
| di .md | 32 | 201186 | 288632 | 1.4347 | 1.4392 | 1.4729 | 1.2448 | 1.5832 | 1.6164 | 1.5832 |
| di .py | 90 | 259406 | 414821 | 1.5991 | 1.5927 | 1.6072 | 1.3753 | 1.7197 | 1.8158 | 1.7348 |
| di .sql | 14 | 12187 | 22187 | 1.8205 | 1.8067 | 1.7802 | 1.6323 | 2.0611 | 2.0611 | 2.0611 |
| di .toml | 2 | 863 | 1339 | 1.5516 | 1.5546 | 1.5546 | 1.5382 | 1.5710 | 1.5710 | 1.5710 |
| di .yaml | 6 | 5412 | 8458 | 1.5628 | 1.6016 | 1.5945 | 1.4640 | 1.7500 | 1.7500 | 1.7500 |

## Discovery / skip / failure counts

| project | discovered | sampled | measured | disc-skips | count-skips | failures |
|---|---|---|---|---|---|---|
| lore | 198 | 39 | 39 | 3 | 0 | 0 |
| odoo | 9236 | 933 | 933 | 30 | 0 | 0 |
| di | 1244 | 144 | 144 | 87 | 0 | 0 |
