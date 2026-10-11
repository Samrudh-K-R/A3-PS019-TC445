# AIORI-3-HACKATHON-PROJECTS

This repository will contain the code and resources for the AIORI-3 hackathon that will be developed during the AIORI-3.

## PS-019: Personal-Data Discovery and Privacy Evidence Inventory

### Project Overview
Our solution is a data discovery scanner designed to identify stored Personally Identifiable Information (PII) within synthetic structured datasets and link it to declared business purposes and retention schedules[cite: 2]. The tool generates a technical privacy evidence inventory for human review, clearly distinguishing technical evidence from legal interpretation without making automated compliance decisions[cite: 2].

### Team Members
* Samrudh K R
* Pranav Sarpangala

### Core Capabilities
* **Multi-Format Scanning:** Inspects synthetic CSV files and one structured SQL database[cite: 2].
* **PII Classification:** Uses configurable rules to identify candidate personal-data fields across 5 predefined data classes[cite: 2].
* **Metadata Mapping:** Links discovered fields directly to their declared business purposes and retention metadata[cite: 2].
* **Gap Analysis:** Automatically flags any missing purpose or retention information within the inventory report[cite: 2].
* **Performance Evaluation:** Evaluates the scanner using a manually labelled test set to report per-class precision and recall metrics[cite: 2].

### Tech Stack
* **Language:** Python
* **Data Processing:** Pandas (CSV), SQLAlchemy/SQLite (SQL database)
* **Detection:** Custom RegEx and heuristic rules
