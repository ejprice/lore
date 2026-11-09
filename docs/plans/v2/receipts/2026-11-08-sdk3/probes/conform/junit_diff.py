"""Both-ways diff of failing node ids between two pytest junit files (failure OR error = red)."""
import sys, xml.etree.ElementTree as ET
def load(path):
    reds, all_ids = {}, set()
    for tc in ET.parse(path).getroot().iter("testcase"):
        nid = f"{tc.get('classname')}::{tc.get('name')}"
        all_ids.add(nid)
        for kind in ("failure", "error"):
            el = tc.find(kind)
            if el is not None:
                reds[nid] = (kind, (el.get("message") or "")[:300])
    return reds, all_ids
base, base_all = load(sys.argv[1]); new, new_all = load(sys.argv[2]); out = sys.argv[3]
only_new = sorted(set(new) - set(base)); only_base = sorted(set(base) - set(new))
print(f"base_tests={len(base_all)} base_red={len(base)} new_tests={len(new_all)} new_red={len(new)} common_red={len(set(new)&set(base))}")
print(f"red_in_image_not_in_audit={len(only_new)} red_in_audit_not_in_image={len(only_base)}")
print(f"collected_only_in_audit={len(base_all-new_all)} collected_only_in_image={len(new_all-base_all)}")
with open(out + "/inimage_failing_ids.txt", "w") as f: f.write("\n".join(sorted(new)) + "\n")
with open(out + "/diff_new_reds.tsv", "w") as f:
    for n in only_new: f.write(f"{n}\t{new[n][0]}\t{new[n][1]}\n")
with open(out + "/diff_audit_only_reds.txt", "w") as f: f.write("\n".join(only_base) + "\n")
with open(out + "/collected_only_in_audit.txt", "w") as f: f.write("\n".join(sorted(base_all-new_all)) + "\n")
