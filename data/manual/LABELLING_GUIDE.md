# Manual test set: how to label

Files
- `manual_test_set.csv`: 60 rows of invented data (columns: full_name, contact, doc_number, note, order_ref).
- `manual_labels.csv`: the answer key. One line per cell that **really contains** personal data: `source,row,column,class`.
  `row` is the data row number starting at 0 (the first data row under the header is 0). A cell not listed = no PII.

Classes: `aadhaar`, `credit_card`, `email`, `phone`, `contextual_pii`.

What to do (both teammates, about 30 minutes)
1. Open `manual_test_set.csv` in Excel or Sheets and read every row yourselves.
2. Compare with `manual_labels.csv`. Fix any wrong, missing or extra label. Do this by eye, not by running the scanner first.
3. Make the set harder on purpose: add 10-20 rows of your own tricky cases, for example
   an Aadhaar in a column called `remarks`, a card number with dashes, an email with a typo, a 10-digit number that is a
   pincode plus code (not a phone), a name inside a note, a date of birth written as 5 March 1999.
   Add the matching lines to `manual_labels.csv` (or leave the cell out if it is NOT personal data).
4. Run:
   ```bash
   python -m src.main scan --csv data/manual --db none --out output_manual
   python -m src.main evaluate --labels data/manual/manual_labels.csv --out output_manual
   ```
5. Put the printed per-class precision and recall in the README and the report. If a class scores below 1.0, look at
   `output_manual/cell_hits.csv` to see which cell was wrong. Tuning the rules after that is fine, but say so.

Rule: labels are decided by people reading the data, never copied from scanner output.
