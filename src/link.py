"""Metadata linker: compare column findings with declared purpose/retention.
Status: matched (both), partial (one), orphan (no declaration)."""


def link(findings, declarations):
    for f in findings:
        key = f"{f['source']}.{f['column']}"
        d = declarations.get(key, {})
        purpose, retention = d.get("purpose"), d.get("retention")
        f["declared_purpose"], f["declared_retention"] = purpose or "", retention or ""
        if purpose and retention:
            f["link_status"], f["gap"] = "matched", ""
        elif purpose or retention:
            f["link_status"] = "partial"
            f["gap"] = "missing retention" if purpose else "missing purpose"
        else:
            f["link_status"], f["gap"] = "orphan", "missing purpose and retention"
    return findings
