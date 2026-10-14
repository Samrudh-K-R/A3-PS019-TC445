# A3-PS019-TC445

This repository contains the code and resources for **PS-019: Personal-Data Discovery and Privacy Evidence Inventory** developed by Team Subnet Sovereigns for the AIORI-3 Hackathon.

**PS-019: Personal-Data Discovery and Privacy Evidence Inventory**

---

## Team A3-PS019-TC445: Subnet Sovereigns

AIORI Hackathon 3 | Problem PS-019 (Cybersecurity)

> **Stage 1: Orientation.** This repository currently holds our problem understanding, proposed solution and team introduction. The prototype will be built in the next stage.

| Name | Role | Email |
|---|---|---|
| Samrudh K R | Scanner core and detection engine | samrudhsamrudh7@gmail.com |
| Pranav Sarpangala | Metadata linking, evaluation, repository | spranav1214@gmail.com |
| Dr. Animesh Giri | Mentor, PES University (EC Campus) | animeshgiri@pes.edu |

**Team ID:** A3-PS019-TC445  
**Institution:** PES University, Electronic City Campus, Bengaluru

### Submission links

| Item | Link |
|---|---|
| Team introduction video (YouTube) | [https://youtu.be/7M6-GzHDf4o](https://youtu.be/7M6-GzHDf4o) |
| GitHub repository | [https://github.com/aiori-hackathon/A3-PS019-TC445](https://github.com/aiori-hackathon/A3-PS019-TC445) |
| Project report (PDF, organisers' format) | [`Proposed-structure-hackathon-A3-PS019-TC445.pdf`](Proposed-structure-hackathon-A3-PS019-TC445.pdf) |

### 1. Problem understanding

Organisations keep personal data in database tables and legacy CSV files, often with no record of why it is held or for how long. Regex-only scanners make this worse: any 12-digit order ID looks like an Aadhaar number, so reviewers drown in false positives.

PS-019 asks for a scanner that:
- finds five predefined classes of personal data in synthetic CSV files and one SQL database;
- uses configurable detection rules;
- links each finding to declared purpose and retention metadata, and flags what is missing;
- reports per-class precision and recall on a small labelled set;
- keeps **evidence** (what the scanner found) separate from **legal interpretation** (what it means).

**Out of scope, by design:** no legal compliance decision, no lawful-basis determination and no universal data-flow inference. The output is a technical evidence inventory for a human reviewer.

### 2. Proposed solution

A modular Python pipeline with four phases.

```
CSV files + SQLite DB
        |
        v
 1. Ingest  ->  2. Detect (two passes)  ->  3. Link  ->  4. Report
                       ^                        ^
                 rules (YAML)          declarations (JSON)
```

| Phase | Plan |
|---|---|
| **Ingest** | Read the SQLite schema (`PRAGMA table_info`) and stream CSV files in chunks, so memory stays flat. |
| **Detect** | Pass 1: regex finds candidates. Pass 2: a checksum or context check validates them. Rules and thresholds are configured in YAML. |
| **Link** | Compare findings with a declarations file (purpose, retention). Mark each finding matched, partial or orphan, and flag missing metadata. |
| **Report** | Produce an evidence inventory, a gap report, and per-class precision and recall. |

#### Data classes (working assumption: to be confirmed with our mentor)

| Class | Pass 1: candidate | Pass 2: validation |
|---|---|---|
| Aadhaar number | 12 digits, first digit 2-9 | Verhoeff checksum |
| Credit card number | 13-19 digit string | Luhn checksum |
| Email address | RFC 5322-style regex | Domain syntax checks |
| Phone number | Digit string plus column-name hint | E.164 parse |
| Contextual PII (name, address, date of birth) | Column name and column type | Confidence weighting |

The problem statement does not list the five classes, so this table may change after mentor confirmation.

### 3. Architecture

See slide 4 of the report for the component diagram. Inputs (CSV, SQLite) flow through ingestion, detection and linking into an evidence inventory. Human-supplied rules, declarations and a labelled test set feed the pipeline, and no lawful-basis logic exists anywhere in it.

### 4. Plan

| Phase | Milestone |
|---|---|
| 1 | Private repository; add `aiori-hackathon`; transfer ownership (this stage) |
| 2 | Synthetic CSV and SQLite data, declarations JSON, labelled test set |
| 3 | Ingestion and dual-pass detection with YAML rules |
| 4 | Metadata linker, gap flags, evidence inventory |
| 5 | Precision and recall evaluation; rule tuning |
| 6 | Prototype demo with pseudocode shared with the mentor |

### 5. Stage 1 checklist

- [x] Problem understanding and proposed solution documented
- [x] Report PDF prepared in the organisers' template
- [x] Private repository created and named `A3-PS019-TC445`
- [x] `aiori-hackathon` added as collaborator, then ownership transferred
- [x] Report PDF uploaded to the repository
- [x] Team introduction video recorded and uploaded to YouTube
- [x] YouTube link added to this README
- [x] Mentor confirmation of the five data classes

### 6. References

1. Government of India. *The Digital Personal Data Protection Act, 2023.* Act No. 22 of 2023.
2. Press Information Bureau. "DPDP Rules, 2025 Notified." 17 Nov 2025.
3. MeitY. Data Protection Framework. meity.gov.in/data-protection-framework
4. ISO/IEC 27701:2019. Privacy information management.
5. NIST. *Privacy Framework, Version 1.0.* 2020.
6. Microsoft Presidio. microsoft.github.io/presidio
7. J. Verhoeff. "Error Detecting Decimal Codes." *Mathematical Centre Tracts* 29, 1969.
8. H. P. Luhn. "Computer for Verifying Numbers." US Patent 2,950,048, 1960.
9. IETF RFC 5322. *Internet Message Format.* 2008.
10. ITU-T Recommendation E.164. 2010.
11. SQLite. `PRAGMA table_info`. sqlite.org/pragma.html

---
Built for AIORI Hackathon 3. Thanks to our mentor, Dr. Animesh Giri, PES University.
