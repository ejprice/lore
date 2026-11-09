"""Drop row #15 (C): does SDK 3.0.0's parse_query_error still raise each of _SDK_PARSE_FAILURES's three arms?
Arms (store/_txn.py comment): AttributeError (non-dict cause), TypeError (unhashable kind / cause code),
RecursionError (cause chain deeper than the recursion limit). Prints, per arm, RAISES <class> or RETURNS <class>.
Control: a well-formed entry RETURNS a typed QueryError (so a 'returns' verdict is not a broken probe)."""
import importlib.metadata as m, sys
from surrealdb.errors import parse_query_error
print("surrealdb", m.version("surrealdb"))
def leg(name, raw):
    try:
        r = parse_query_error(raw); print(f"{name}: RETURNS {type(r).__name__}")
    except Exception as e:  # noqa: BLE001
        print(f"{name}: RAISES {type(e).__name__}: {str(e)[:80]}")
leg("control well-formed", {"kind": "Query", "result": "x", "details": {"kind": "TransactionConflict"}})
leg("AttributeError arm: non-dict cause", {"kind": "Query", "result": "x", "cause": "a bare string"})
leg("AttributeError arm: list cause", {"kind": "Query", "result": "x", "cause": ["x"]})
leg("TypeError arm: unhashable kind", {"kind": ["Query"], "result": "x"})
leg("TypeError arm: unhashable cause code", {"kind": "Query", "result": "x", "cause": {"code": [1], "message": "m"}})
deep = {"kind": "Internal", "message": "leaf"}
for _ in range(sys.getrecursionlimit() + 50):
    deep = {"kind": "Internal", "message": "m", "cause": deep}
leg("RecursionError arm: deep cause chain", {"kind": "Query", "result": "x", "cause": deep})
