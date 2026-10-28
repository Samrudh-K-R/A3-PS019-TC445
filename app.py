"""Web demo (Streamlit): upload CSV/SQLite files or use the built-in synthetic sample.
Shows the evidence inventory, gap report, masked cell hits and per-class precision/recall.
Evidence for human review only: no legal or compliance decision is made."""
import os
import tempfile
import json
import pandas as pd
import streamlit as st

from src.config import load_rules, load_declarations
from src.scan import scan
from src.report import evaluate, FIELDS

HERE = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(HERE, "config", "rules.yaml")
DECL_PATH = os.path.join(HERE, "config", "declarations.json")
SAMPLE_CSV = os.path.join(HERE, "data", "synthetic")
SAMPLE_DB = os.path.join(HERE, "data", "synthetic", "demo.db")
SAMPLE_LABELS = os.path.join(HERE, "data", "labelled", "cell_labels.csv")
MANUAL_CSV = os.path.join(HERE, "data", "manual")
MANUAL_LABELS = os.path.join(HERE, "data", "manual", "manual_labels.csv")

NAMES = {"personal_identity": "Personal identity", "contact": "Contact information",
         "government_id": "Government identifiers", "financial": "Financial information", "location": "Location / address"}

st.set_page_config(page_title="Personal-Data Discovery", page_icon=None, layout="wide")
st.title("Personal-Data Discovery and Privacy Evidence Inventory")
st.caption("Team Subnet Sovereigns | A3-PS019-TC445 | AIORI Hackathon 3, PS-019")
st.info("Technical evidence for human review. This tool does not make legal compliance or lawful-basis decisions. "
        "Use synthetic data only: do not upload real personal data to a public demo.")

rules = load_rules(RULES_PATH)

with st.sidebar:
    st.header("1. Choose data")
    mode = st.radio("Source", ["Built-in synthetic sample", "Hand-checked test set (70 rows)", "Upload my own files"])
    csvs = db = decl_file = None
    if mode == "Upload my own files":
        csvs = st.file_uploader("CSV files (UTF-8, header row)", type=["csv"], accept_multiple_files=True)
        db = st.file_uploader("SQLite database (optional)", type=["db", "sqlite", "sqlite3"])
        decl_file = st.file_uploader("Declarations JSON (optional)", type=["json"])
        st.caption('Declarations format: {"file.csv.column": {"purpose": "...", "retention": "..."}}')
    st.header("2. Settings")
    min_conf = st.slider("Minimum confidence", 0.3, 0.95, float(rules.get("min_confidence", 0.5)), 0.05)
    ratio = st.slider("Column threshold (share of cells)", 0.05, 0.9, float(rules.get("column_ratio_threshold", 0.2)), 0.05)
    run = st.button("Run scan", type="primary")

rules["min_confidence"] = min_conf
rules["column_ratio_threshold"] = ratio


def do_scan():
    """Returns (findings, hits, labels_path or None, source description)."""
    decl = load_declarations(DECL_PATH)
    if mode == "Built-in synthetic sample":
        f, h = scan(SAMPLE_CSV, SAMPLE_DB, rules, decl)
        return f, h, SAMPLE_LABELS, "synthetic sample (6 CSV files + SQLite database)"
    if mode.startswith("Hand-checked"):
        f, h = scan(MANUAL_CSV, None, rules, {})
        return f, h, MANUAL_LABELS, "hand-checked set (manual_test_set.csv)"
    if not csvs and not db:
        return None
    with tempfile.TemporaryDirectory() as tmp:            # files live only for this scan, then are deleted
        for u in csvs or []:
            with open(os.path.join(tmp, os.path.basename(u.name)), "wb") as fh:
                fh.write(u.getbuffer())
        dbp = None
        if db:
            dbp = os.path.join(tmp, "upload.db")
            with open(dbp, "wb") as fh:
                fh.write(db.getbuffer())
        d = json.load(decl_file) if decl_file else {}
        f, h = scan(tmp, dbp, rules, d)
    return f, h, None, "your uploaded files"


if run:
    try:
        res = do_scan()
    except Exception as e:                                 # show a readable error instead of a stack trace
        st.error(f"Scan failed: {e}")
        res = None
    if res is None:
        st.warning("Please upload at least one CSV file or a database.")
    else:
        st.session_state["res"] = res

if "res" not in st.session_state:
    st.write("Pick a source on the left and press **Run scan**. Start with the built-in synthetic sample.")
    st.stop()

findings, hits, labels, src = st.session_state["res"]
inv = pd.DataFrame(findings, columns=FIELDS) if findings else pd.DataFrame(columns=FIELDS)
status = inv["link_status"].value_counts() if len(inv) else {}

st.subheader(f"Results for the {src}")
c = st.columns(5)
c[0].metric("Column findings", len(inv))
c[1].metric("Matched", int(status.get("matched", 0)))
c[2].metric("Partial", int(status.get("partial", 0)))
c[3].metric("Orphan", int(status.get("orphan", 0)))
c[4].metric("Flagged cells", len(hits))

t1, t2, t3, t4, t5 = st.tabs(["Inventory", "Gap report", "Flagged cells (masked)", "Precision / recall", "About"])
with t1:
    if len(inv):
        inv_show = inv.copy(); inv_show["category"] = inv_show["category"].map(NAMES)
        st.dataframe(inv_show, width="stretch", hide_index=True)
        st.bar_chart(inv_show.groupby("category")["matches"].sum())
        st.download_button("Download inventory.csv", inv.to_csv(index=False), "inventory.csv", "text/csv")
    else:
        st.write("No personal-data columns found.")
with t2:
    gaps = inv[inv["link_status"] != "matched"] if len(inv) else inv
    st.write("Columns where personal data was found but the written purpose and/or retention is missing. "
             "**orphan** = nothing written, **partial** = one of the two is missing.")
    st.dataframe(gaps, width="stretch", hide_index=True)
    if len(gaps):
        st.download_button("Download gap_report.csv", gaps.to_csv(index=False), "gap_report.csv", "text/csv")
with t3:
    h = pd.DataFrame(hits, columns=["source", "row", "column", "class", "confidence", "masked_value"])
    st.write("Values are masked: only the last 4 characters are kept. Row numbers start at 0.")
    st.dataframe(h.head(2000), width="stretch", hide_index=True)
with t4:
    if labels:
        rows = pd.DataFrame(evaluate(hits, labels, rules))
        rows["class"] = rows["class"].replace(NAMES)
        n_labels = int(rows[rows["level"] == "category"]["support"].sum())
        st.write(f"Scored against the answer key ({n_labels:,} labelled cells). TP = caught, FP = false alarm, FN = missed.")
        st.markdown("**Per official class**")
        st.dataframe(rows[rows["level"].isin(["category", "overall"])].drop(columns="level"), width="stretch", hide_index=True)
        st.markdown("**Per sub-type**")
        st.dataframe(rows[rows["level"] == "subtype"].drop(columns="level"), width="stretch", hide_index=True)
        st.caption("The sample data is synthetic and was used to tune the rules, so these scores are optimistic. "
                   "Real data would score lower.")
    else:
        st.write("Precision and recall need an answer key, so they are shown only for the built-in sample sets.")
with t5:
    st.markdown("""
**How it works**: Ingest (CSV in chunks, SQLite schema first) -> Detect (pass 1 regex candidate, pass 2 checksum/format validator, column-name hints add confidence) ->
Link (compare with declared purpose and retention) -> Report.

**Five official classes**: personal identity, contact information, government identifiers, financial information, location / address.
Anything matching none of them is simply not flagged ("not personal data").

**Statuses**: *matched* = purpose and retention written; *partial* = one missing; *orphan* = none written.
""")
