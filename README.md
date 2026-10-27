# AIORI-3-HACKATHON-PROJECTS

This repository will contain the code and resources for the AIORI-3 hackathon that will be developed during the AIORI-3.

**PS-019: Personal-Data Discovery and Privacy Evidence Inventory**

---

## Team A3-PS019-TC445: Subnet Sovereigns

AIORI Hackathon 3 | Problem PS-019 (Cybersecurity) | PES University, Electronic City Campus

| Name | Role | Email |
|---|---|---|
| Samrudh K R | Scanner core and detection engine | samrudhsamrudh7@gmail.com |
| Pranav Sarpangala | Metadata linking, evaluation, repository | spranav1214@gmail.com |
| Dr. Animesh Giri | Mentor, PES University (EC Campus) | animeshgiri@pes.edu |

| Item | Link |
|---|---|
| GitHub repository | https://github.com/aiori-hackathon/A3-PS019-TC445 |
| Team introduction video (YouTube) | `<paste YouTube link here>` |
| Project report (PDF) | [`docs/A3-PS019-TC445.pdf`](docs/A3-PS019-TC445.pdf) |

## What it does

A command-line scanner that finds candidate personal data in **synthetic CSV files and one SQLite database**, links each finding to **declared purpose and retention** metadata, flags what is missing, and reports **per-class precision and recall**.

**Evidence, not verdicts.** The output is a technical evidence inventory for a human reviewer. The tool makes no legal compliance decision, no lawful-basis determination and no universal data-flow inference.

```
CSV files + SQLite DB -> Ingest -> Detect (2 passes) -> Link -> Report / Evaluate
                                      ^                  ^
                              config/rules.yaml   config/declarations.json
```

| Phase | Module | What it does |
|---|---|---|
| Ingest | `src/ingest.py` | CSV in 10,000-row chunks (pandas); SQLite via `PRAGMA table_info`, skipping columns whose declared type cannot hold the target classes |
| Detect | `src/detect.py`, `src/validators.py` | Pass 1 regex candidate, pass 2 checksum or format validator; column-name hints add confidence; validated digits are claimed by the most specific class first |
| Link | `src/link.py` | Compares column findings with declarations: **matched** (purpose and retention), **partial** (one missing), **orphan** (none) |
| Report | `src/report.py` | `inventory.json/csv`, `gap_report.csv`, `cell_hits.csv` (values are masked), `metrics.json` |

## Data classes

The organisers fixed **five official classes** (clarification email, PS-019). Each is detected through one or more **sub-types**, all configured in `config/rules.yaml` (no code change to tune them). Anything matching none of them is reported as **not personal data** (i.e. never flagged; a flag on a non-personal cell counts as a false alarm).

| Official class | Sub-types we detect | Pass 1: candidate | Pass 2: validation |
|---|---|---|---|
| Personal identity | name, date of birth, gender, age | column-name hint (name, dob, gender, age) | value-shape check; placeholder values (N/A, Anonymous...) ignored |
| Contact information | email, phone | email pattern; Indian mobile with optional +91 | format check; E.164-compatible |
| Government identifiers | Aadhaar, PAN, passport, voter ID, driving licence | 12 digits; 5 letters+4 digits+letter; letter+7 digits; 3 letters+7 digits; state+RTO+year+serial | Verhoeff; PAN holder-type letter; DL year range; passport/voter/DL need a column hint |
| Financial information | card number, bank account, IFSC, UPI ID | 13-19 digits; 9-18 digits; 4 letters+0+6 chars; handle@bank | Luhn; bank account needs a column hint; UPI handle whitelist |
| Location / address | postal address, PIN code, geo-coordinates | column-name hint; 6 digits; lat, lon decimals | value-shape; PIN needs a column hint; coordinates must be in range |

## Quick start

Python 3.10 or newer. Expected: 13 tests pass.

```bash
pip install -r requirements.txt
python -m src.main generate     # regenerate synthetic data, declarations and labels
python -m src.main run          # scan + evaluate
python -m pytest -q tests       # unit tests
```

Separate commands: `scan` writes the reports to `output/`; `evaluate` scores `output/cell_hits.csv` against `data/labelled/cell_labels.csv`.

## Results on our synthetic set

Default seed (42): 6 CSV files and 4 database tables, **4,630 labelled cells** (evaluation-set size; every official class has well over 20 labelled fields per class). The set includes deliberate look-alikes: order and invoice numbers, tracking numbers, PAN-like employee codes with an invalid holder letter, passport-like ticket references, out-of-range coordinate pairs, page numbers and 6-digit dispatch codes.

| Official class | Labelled cells | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| Contact information | 921 | 921 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Financial information | 750 | 750 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Government identifiers | 934 | 934 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Location / address | 900 | 900 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Personal identity | 1125 | 1050 | 0 | 75 | 1.000 | 0.933 | 0.966 |
| **All (micro)** | 4630 | 4555 | 0 | 75 | 1.000 | 0.984 | 0.992 |

Per sub-type numbers are in `output/metrics.json` and printed by `run`.

**Read these numbers carefully.**
- The data is synthetic, generated by us, and we tuned the rules on it. Near-perfect scores here do **not** predict accuracy on real data.
- How the first run looked: bank account numbers that happen to pass Luhn were reported as cards (25 false alarms), 12-digit order references starting with 91 passed the phone check, and licence numbers lost their digits to the card rule. We fixed these with column-name suppression and by requiring hints for ambiguous formats.
- The 75 personal-identity misses are by design: `legacy_export.csv` has names in a column called `col_d`, and names need a column-name hint.
- Known limit: a type found in under 20% of a column (for example phone numbers inside `audit_log.message`) appears in `cell_hits.csv` but is not reported as a column finding. Tune `column_ratio_threshold`.

### Link results

Out of 34 column findings: 18 matched, 3 partial, 13 orphan (16 gaps). Examples: `kyc.csv.passport_no` (missing retention), `payments.csv.card_number` (missing purpose), and undeclared `kyc.voter_id`, `finance.upi_id`, `locations.geo_point` and `legacy_export` columns.

## Small manually labelled test set

`data/manual/` holds a 70-row test set with a hand-checked answer key (see `data/manual/LABELLING_GUIDE.md`). It covers personal identity, contact, Aadhaar and card numbers only; the other classes are evaluated on the larger synthetic set.

```bash
python -m src.main run --csv data/manual --db none --labels data/manual/manual_labels.csv --out output_manual
```

| Official class | Labelled cells | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| Contact information | 47 | 47 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Financial information | 12 | 6 | 0 | 6 | 1.000 | 0.500 | 0.667 |
| Government identifiers | 14 | 12 | 0 | 2 | 1.000 | 0.857 | 0.923 |
| Personal identity | 66 | 64 | 0 | 2 | 1.000 | 0.970 | 0.985 |
| **All (micro)** | 139 | 129 | 0 | 10 | 1.000 | 0.928 | 0.963 |

The earlier false alarms on `N/A` and `Anonymous` disappeared after we added the `ignore_values` list, so this figure is tuned on cases we had already seen. Recall misses are names/DOBs written inside note sentences and checksum-failing card look-alikes.

## Deployment (hosted web demo)

The scanner is wrapped in a small Streamlit web app (`app.py`). It lets a reviewer scan the built-in synthetic sample, the hand-checked set, or their own uploaded CSV/SQLite files, then shows the inventory, gap report, masked flagged cells and per-class precision and recall, with CSV downloads.

**Live demo:** `<paste hosted URL here>`

### Run locally (what a mentor needs)

```bash
git clone https://github.com/aiori-hackathon/A3-PS019-TC445.git
cd A3-PS019-TC445
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.main generate        # optional: regenerates the synthetic data (seed 42)
streamlit run app.py               # opens http://localhost:8501
```

Command-line only (no web page): `python -m src.main run`. Tests: `python -m pytest -q tests`.

### Host it (Streamlit Community Cloud, free)

1. Push the repo to GitHub (it contains synthetic data only).
2. Go to https://share.streamlit.io, sign in with GitHub and choose **Create app**.
3. Pick the repository and branch, set **Main file path** to `app.py`, and deploy.
4. Copy the app URL into this README (line above) and into the presentation.

If the repository must stay private, grant the Streamlit GitHub app access to it, or host from a public copy that holds only the synthetic data. Render or any host that runs `streamlit run app.py --server.port $PORT` also works.

### Notes
- Uploaded files are written to a temporary folder for one scan and deleted afterwards; masked values only are shown. Still, **do not upload real personal data to a public demo**.
- Database engine: SQLite (`data/synthetic/demo.db`, regenerated by `python -m src.main generate`); no server setup is needed.
- File formats: CSV is UTF-8 with a header row; declarations are JSON `{"file.csv.column": {"purpose": "...", "retention": "..."}}` (see `config/declarations.json`).

## Repository layout

```
config/          rules.yaml, declarations.json
data/synthetic/  customers, payments, kyc, finance, locations, legacy_export (.csv) and demo.db  (synthetic only)
data/labelled/   cell_labels.csv (auto-generated labels for the large synthetic set)
data/manual/     small manually labelled test set + labelling guide
app.py          Streamlit web demo
src/             ingest, detect, validators, link, report, scan, main, generate_data
tests/           unit tests (validators, detector, linker)
docs/            report PDF
```

## Pseudocode

```text
for each source (CSV chunk or DB table, schema-first):
    for each cell:
        for each class in priority order:
            candidate = regex(cell)                       # pass 1
            if candidate not already claimed and validator(candidate):   # pass 2
                record (source, row, column, class, confidence, masked value)
aggregate per column; keep classes found in >= column_ratio_threshold of non-empty cells
for each column finding:
    status = matched | partial | orphan   # from declarations.json
write inventory, gap report; evaluate cell hits against labels (P / R / F1)
```

## Limitations and next steps

- Detection is rule-based; passport, voter ID, driving licence, bank account and PIN need a column-name hint because their formats are ambiguous.
- Hosted demo: see the Deployment section.
- Detection is rule-based. Names and addresses depend on column naming; a value-based name detector is future work.
- Synthetic data only. No real personal data is stored; hit values are masked in outputs.
- Declarations are a simple JSON map keyed `source.column`.

## References

1. Government of India. *The Digital Personal Data Protection Act, 2023.* Act No. 22 of 2023.
2. Press Information Bureau. "DPDP Rules, 2025 Notified." 17 Nov 2025.
3. ISO/IEC 27701:2019. Privacy information management.
4. NIST. *Privacy Framework, Version 1.0.* 2020.
5. Microsoft Presidio. microsoft.github.io/presidio
6. J. Verhoeff. "Error Detecting Decimal Codes." *Mathematical Centre Tracts* 29, 1969.
7. H. P. Luhn. "Computer for Verifying Numbers." US Patent 2,950,048, 1960.
8. IETF RFC 5322. *Internet Message Format.* 2008.
9. ITU-T Recommendation E.164. 2010.
10. SQLite. `PRAGMA table_info`.

Thanks to our mentor, Dr. Animesh Giri, PES University.
