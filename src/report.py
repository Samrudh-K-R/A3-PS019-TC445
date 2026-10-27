"""Evidence inventory, gap report and evaluation. Wording stays 'candidate'/'evidence'."""
import csv
import json
import os

FIELDS = ["source", "column", "class", "class_label", "matches", "non_empty_cells", "match_share",
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


def evaluate(cell_hits, labels_path):
    truth = set()
    with open(labels_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            truth.add((r["source"], int(r["row"]), r["column"], r["class"]))
    pred = {(s, r, c, k) for s, r, c, k, *_ in cell_hits}
    classes = sorted({t[3] for t in truth} | {p[3] for p in pred})
    rows, tot = [], [0, 0, 0]
    for k in classes:
        t = {x for x in truth if x[3] == k}; p = {x for x in pred if x[3] == k}
        tp, fp, fn = len(t & p), len(p - t), len(t - p)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        rows.append({"class": k, "tp": tp, "fp": fp, "fn": fn, "precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3)})
        tot[0] += tp; tot[1] += fp; tot[2] += fn
    tp, fp, fn = tot
    prec = tp / (tp + fp) if tp + fp else 0.0; rec = tp / (tp + fn) if tp + fn else 0.0
    micro = {"class": "ALL (micro)", "tp": tp, "fp": fp, "fn": fn, "precision": round(prec, 3), "recall": round(rec, 3),
             "f1": round(2 * prec * rec / (prec + rec), 3) if prec + rec else 0.0}
    return rows + [micro]
