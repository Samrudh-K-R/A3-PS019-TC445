"""Two-pass detection. Pass 1: regex candidate. Pass 2: checksum/format validator.
Contextual PII uses column-name hints + value shape. Column-name hints add confidence."""
import re
from .validators import VALIDATORS


def mask(value: str) -> str:
    v = value.strip()
    if len(v) <= 4:
        return "*" * len(v)
    return "*" * (len(v) - 4) + v[-4:]


class Detector:
    def __init__(self, rules):
        self.min_conf = rules.get("min_confidence", 0.5)
        self.ignore = {str(v).lower() for v in rules.get("ignore_values", [])}
        self.classes = {}
        for key, spec in rules["classes"].items():
            self.classes[key] = {
                "label": spec.get("label", key),
                "category": spec.get("category", key),
                "require_hint": bool(spec.get("require_hint")),
                "re": re.compile(spec["pattern"]) if spec.get("pattern") else None,
                "validator": VALIDATORS[spec.get("validator", "none")],
                "hints": [h.lower() for h in spec.get("column_hints", [])],
                "suppress": [h.lower() for h in spec.get("suppress_column_hints", [])],
                "base": spec.get("base_confidence", 0.5),
                "shape": re.compile(spec["value_shape"]) if spec.get("value_shape") else None,
            }

    def hint_match(self, cls, column):
        c = column.lower()
        return any(h in c for h in self.classes[cls]["hints"])

    def scan_cell(self, column, value):
        """Return list of (class, confidence, masked_value) for one cell."""
        out = []
        if value is None or not str(value).strip():
            return out
        value = str(value)
        consumed = []  # spans already claimed by a validated, more specific class (rules.yaml order = priority)
        for key, spec in self.classes.items():
            hint = self.hint_match(key, column)
            # configurable: columns named like order/ref/tracking IDs are not scanned for this class
            if (not hint or spec["re"] is None) and any(x in column.lower() for x in spec["suppress"]):
                continue
            if spec["require_hint"] and not hint:      # ambiguous patterns (bank a/c, PIN...) need the column name
                continue
            if spec["re"] is None:
                # contextual: needs column hint, and value must look like text/date
                if hint and spec["shape"] and value.strip().lower() not in self.ignore and spec["shape"].search(value.strip()):
                    out.append((key, min(1.0, spec["base"] + 0.3), mask(value)))
                continue
            for m in spec["re"].finditer(value):                      # pass 1
                a, b = m.span()
                if any(a < e and s_ < b for s_, e in consumed):         # digits already claimed
                    continue
                cand = m.group(0)
                if spec["validator"](cand):                             # pass 2
                    conf = min(1.0, spec["base"] + 0.3 + (0.1 if hint else 0))
                    out.append((key, conf, mask(cand)))
                    consumed.append((a, b))
                    break
        return [o for o in out if o[1] >= self.min_conf]
