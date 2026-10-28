"""Scan driver: ingest -> detect -> aggregate per column -> link."""
import glob
import os
from collections import defaultdict
from .detect import Detector
from .ingest import iter_csv, iter_db
from .link import link


def scan(csv_dir, db_path, rules, declarations):
    det = Detector(rules)
    ratio = rules.get("column_ratio_threshold", 0.2)
    cell_hits = []                                   # (source,row,column,class,confidence,masked)
    col_total = defaultdict(int)                     # (source,column) -> non-empty cells
    col_hits = defaultdict(lambda: defaultdict(list))  # (source,column) -> class -> confidences

    streams = [iter_csv(p) for p in sorted(glob.glob(os.path.join(csv_dir, "*.csv")))]
    if db_path and os.path.exists(db_path):
        streams.append(iter_db(db_path))
    for stream in streams:
        for src, col, row, val in stream:
            if val.strip():
                col_total[(src, col)] += 1
            for cls, conf, masked in det.scan_cell(col, val):
                cell_hits.append((src, row, col, cls, round(conf, 2), masked))
                col_hits[(src, col)][cls].append(conf)

    findings = []
    for (src, col), classes in col_hits.items():
        total = col_total[(src, col)]
        for cls, confs in classes.items():
            share = len(confs) / total if total else 0
            if share < ratio:
                continue
            findings.append({
                "source": src, "column": col, "category": det.classes[cls]["category"], "class": cls, "class_label": det.classes[cls]["label"],
                "matches": len(confs), "non_empty_cells": total, "match_share": round(share, 3),
                "confidence": round(sum(confs) / len(confs), 2),
                "column_name_hint": det.hint_match(cls, col),
            })
    findings.sort(key=lambda f: (f["source"], f["column"], f["class"]))
    return link(findings, declarations), cell_hits
