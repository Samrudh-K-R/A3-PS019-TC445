"""CLI: generate | scan | evaluate | run (scan + evaluate)."""
import argparse
import json
import os
from .config import load_rules, load_declarations
from .generate_data import build
from .scan import scan
from .report import write_reports, evaluate


def cmd_scan(a):
    rules, decl = load_rules(a.rules), load_declarations(a.declarations)
    findings, hits = scan(a.csv, a.db, rules, decl)
    gaps = write_reports(findings, hits, a.out)
    from collections import Counter
    st = Counter(f["link_status"] for f in findings)
    print(f"{len(findings)} column findings | matched {st['matched']} partial {st['partial']} orphan {st['orphan']} | gaps {len(gaps)}")
    return hits


def cmd_eval(a, hits=None):
    if hits is None:
        import csv
        with open(os.path.join(a.out, "cell_hits.csv"), newline="", encoding="utf-8") as f:
            hits = [(r["source"], int(r["row"]), r["column"], r["class"]) for r in csv.DictReader(f)]
    rows = evaluate(hits, a.labels, load_rules(a.rules))
    with open(os.path.join(a.out, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    last = None
    for r in rows:
        if r["level"] != last:
            last = r["level"]
            print(f"\n[{'per official class' if last == 'category' else 'per sub-type' if last == 'subtype' else 'overall'}]")
            print(f"{'class':<20}{'TP':>5}{'FP':>5}{'FN':>5}{'prec':>8}{'rec':>8}{'f1':>8}")
        print(f"{r['class']:<20}{r['tp']:>5}{r['fp']:>5}{r['fn']:>5}{r['precision']:>8}{r['recall']:>8}{r['f1']:>8}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m src.main")
    p.add_argument("command", choices=["generate", "scan", "evaluate", "run"])
    p.add_argument("--csv", default="data/synthetic")
    p.add_argument("--db", default="data/synthetic/demo.db")
    p.add_argument("--rules", default="config/rules.yaml")
    p.add_argument("--declarations", default="config/declarations.json")
    p.add_argument("--labels", default="data/labelled/cell_labels.csv")
    p.add_argument("--out", default="output")
    a = p.parse_args(argv)
    if a.command == "generate":
        build()
    elif a.command == "scan":
        cmd_scan(a)
    elif a.command == "evaluate":
        cmd_eval(a)
    else:
        cmd_eval(a, cmd_scan(a))


if __name__ == "__main__":
    main()
