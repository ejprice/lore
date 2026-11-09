"""Diff the dump's DDL (before boot) against INFO FOR DB/TABLE (after boot), normalising rendering-only noise."""
import sys, json, re
c = sys.argv[1]
after = json.load(open(f"{c}/ddl_after.json"))
defs = set(after["db"]["tables"].values())
for info in after["tables"].values():
    for kind in ("fields", "indexes", "events"):
        defs.update(info.get(kind, {}).values())
for k in ("analyzers", "sequences", "functions", "params"):
    defs.update(after["db"].get(k, {}).values())
def norm(s):
    s = re.sub(r"\s+", " ", s.strip().rstrip(";"))
    s = re.sub(r"^DEFINE (\w+) (OVERWRITE |IF NOT EXISTS )", r"DEFINE \1 ", s)
    return s
B = {norm(l) for l in open(f"{c}/ddl_before_dump.surql")}; A = {norm(x) for x in defs}
key = lambda s: " ".join(s.split()[:5])
ka = {key(x): x for x in A - B}; kb = {key(x): x for x in B - A}
print(f"before={len(B)} after={len(A)} identical={len(A & B)} changed={len(set(ka)&set(kb))} added={len(set(ka)-set(kb))} gone={len(set(kb)-set(ka))}")
out = []
for k in sorted(set(ka) | set(kb)):
    tag = "CHANGED" if k in ka and k in kb else ("ADDED" if k in ka else "GONE")
    out.append({"tag": tag, "key": k, "before": kb.get(k), "after": ka.get(k)})
json.dump(out, open(f"{c}/ddl_diff.json", "w"), indent=1)
for o in out:
    print(o["tag"], o["key"])
    if o["tag"] == "CHANGED":
        print("   before:", o["before"][:400]); print("   after: ", o["after"][:400])
