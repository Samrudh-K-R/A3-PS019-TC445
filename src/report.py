"""Evidence inventory, gap report and evaluation. Wording stays 'candidate'/'evidence'."""
import csv
import json
import os

FIELDS = ["source", "column", "category", "class", "class_label", "matches", "non_empty_cells", "match_share",
          "confidence", "column_name_hint", "declared_purpose", "declared_retention", "link_status", "gap"]


def write_reports(findings, cell_hits, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "inventory.json"), "w", encoding="utf-8") as f:
        json.dump({"note": "Candidate findings: technical evidence for human review, not a legal determination.",
                   "findings": findings}, f, indent=2)
    with open(os.path.join(out_dir, "inventory.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(findings)
    gaps = [x for x in findings if x["link_status"] != "matched"]
    with open(os.path.join(out_dir, "gap_report.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(gaps)
    with open(os.path.join(out_dir, "cell_hits.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["source", "row", "column", "class", "confidence", "masked_value"]); w.writerows(cell_hits)
    return gaps


def _score(truth, pred, keyfn, level):
    """Cell-level TP/FP/FN, precision, recall, F1 per group (keyfn maps a cell to its group)."""
    groups = sorted({keyfn(t) for t in truth} | {keyfn(p) for p in pred})
    rows, tot = [], [0, 0, 0]
    for k in groups:
        t = {x for x in truth if keyfn(x) == k}; p = {x for x in pred if keyfn(x) == k}
        tp, fp, fn = len(t & p), len(p - t), len(t - p)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        rows.append({"level": level, "class": k, "tp": tp, "fp": fp, "fn": fn, "support": len(t),
                     "precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3)})
        tot[0] += tp; tot[1] += fp; tot[2] += fn
    tp, fp, fn = tot
    prec = tp / (tp + fp) if tp + fp else 0.0; rec = tp / (tp + fn) if tp + fn else 0.0
    rows.append({"level": "overall", "class": "ALL (micro)", "tp": tp, "fp": fp, "fn": fn, "support": tp + fn,
                 "precision": round(prec, 3), "recall": round(rec, 3),
                 "f1": round(2 * prec * rec / (prec + rec), 3) if prec + rec else 0.0})
    return rows


def evaluate(cell_hits, labels_path, rules=None):
    """Score against the answer key. Labels use sub-type names; rules map each sub-type to one of the
    five official classes. Anything flagged but not in the key counts as a false alarm ('not personal data')."""
    truth = set()
    with open(labels_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            truth.add((r["source"], int(r["row"]), r["column"], r["class"]))
    pred = {(s, r, c, k) for s, r, c, k, *_ in cell_hits}
    cat = {k: v.get("category", k) for k, v in (rules or {}).get("classes", {}).items()}
    by_cat = _score(truth, pred, lambda x: cat.get(x[3], x[3]), "category")
    by_type = _score(truth, pred, lambda x: x[3], "subtype")[:-1]
    return by_cat + by_type
