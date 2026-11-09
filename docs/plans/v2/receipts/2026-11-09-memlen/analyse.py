"""Tabulate probe_results.json: LONG (offline copy) vs ATOMIC, per query."""
import json, sys
R = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'probe_results.json'))
A, B = '6d16f7f4-9a98-51d4-b4b9-bdb8824fd96e', 'd53e4404-74f5-58e7-af2b-b2a386292cb5'
print('controls', R['controls'])
for arm, v in R['arms'].items():
    print(arm, 'rows_expected', v['rows_expected'], 'seeded', v['rows_seeded'], 'db', v['database'][:14])
    print('  hnsw:', [x for x in (v.get('indexes') or {}).values() if 'HNSW' in x])
print('dropped', len(R['databases_dropped']))
def pos(fused, pred):
    for i, r in enumerate(fused):
        if pred(r['id']): return i + 1, r['score']
    return None, None
print('\nqid | LONG rank score cos_rank cos | ATOM best: piece rank score | ATOM target rank score cos_rank cos | bm25_arm_size subj_in_bm25')
for q in R['arms']['LONG']['results']:
    subj = q[0]
    L = R['arms']['LONG']['results'][q]
    for s, lid, arm in (('A', A, 'ATOM_A'), ('B', B, 'ATOM_B')):
        if subj not in (s, 'D'): continue
        lr, ls = pos(L['fused'], lambda i: i == lid)
        lc = L['cosine_rank'][lid]
        T = R['arms'][arm]['results'][q]
        br, bs = pos(T['fused'], lambda i: i.startswith(f'piece-{s}'))
        bp = next((r['id'] for r in T['fused'] if r['id'].startswith(f'piece-{s}')), '-')
        tgt = f'piece-{q}' if subj == s else None
        tr, ts = pos(T['fused'], lambda i: i == tgt) if tgt else (None, None)
        tc = T['cosine_rank'][tgt] if tgt else ('-', '-')
        top_piece_cos = min((v for k, v in T['cosine_rank'].items() if k.startswith(f'piece-{s}')), key=lambda x: x[0])
        print(f"{q}/{s} | {lr} {ls} {lc[0]} {lc[1]} | {bp} {br} {bs} (best-piece cos_rank {top_piece_cos[0]} {top_piece_cos[1]}) | {tr} {ts} {tc[0]} {tc[1]} | bm25 {len(L['bm25_arm'])} {lid in L['bm25_arm']} / atom {len(T['bm25_arm'])} {[x for x in T['bm25_arm'] if x.startswith('piece')]}")
    print(f"   LONG top3: {[(r['id'][:8], round(r['score'],4)) for r in L['fused'][:3]]}")
