"""Drafts data/manual/manual_test_set.csv and manual_labels.csv (60 rows) for the team to REVIEW and correct by hand.
Every value is invented. Labels list only cells that truly contain PII; unlisted cells mean 'no PII'."""
import csv, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.validators import verhoeff_check_digit, luhn_check_digit, aadhaar_valid, card_valid

r = random.Random(7)
NAMES = ["Asha Rao","Bharath Kumar","Chitra Nair","Dev Malhotra","Esha Gupta","Farhan Sheikh","Gauri Joshi","Harish Babu",
         "Indu Menon","Jayant Pillai","Kiran Hegde","Lakshmi Iyer","Manoj Tiwari","Nisha Verma","Om Prakash","Pooja Desai",
         "Qasim Ali","Ritu Sharma","Suresh Naik","Tara Bose"]
CITY = ["12 MG Road, Bengaluru","7 Park Street, Kolkata","88 Anna Salai, Chennai","3 FC Road, Pune","41 Banjara Hills, Hyderabad"]

def aad(sp=False):
    p = r.choice("23456789") + "".join(r.choice("0123456789") for _ in range(10))
    n = p + verhoeff_check_digit(p)
    return f"{n[:4]} {n[4:8]} {n[8:]}" if sp else n
def card(sp=False):
    p = r.choice("45") + "".join(r.choice("0123456789") for _ in range(14))
    n = p + luhn_check_digit(p)
    return " ".join(n[i:i+4] for i in range(0, 16, 4)) if sp else n
def decoy12():
    while True:
        n = str(r.randint(10**11, 10**12 - 1))
        if not aadhaar_valid(n): return n
def decoy16():
    while True:
        n = str(r.randint(10**15, 10**16 - 1))
        if not card_valid(n): return n
def ph(): return r.choice(["9","8","7","6"]) + "".join(r.choice("0123456789") for _ in range(9))

rows, labels = [], []
def add(name, contact, doc, note, order_ref, truth):
    i = len(rows)
    rows.append([name, contact, doc, note, order_ref])
    for col, cls in truth: labels.append(("manual_test_set.csv", i, col, cls))

for k in range(60):
    nm = NAMES[k % len(NAMES)]; truth = []
    contact = doc = note = ""; oref = str(r.randint(10**11, 10**12 - 1)) if k % 2 == 0 else ""
    if nm: truth.append(("full_name", "contextual_pii"))
    t = k % 10
    if t == 0: contact = f"{nm.split()[0].lower()}{r.randint(1,99)}@example.com"; truth.append(("contact", "email"))
    elif t == 1: contact = ph(); truth.append(("contact", "phone"))
    elif t == 2: contact = "+91 " + ph(); truth.append(("contact", "phone"))
    elif t == 3: contact = "1234567890"                       # looks like a phone, is not (starts with 1)
    elif t == 4: contact = f"{nm.split()[0].lower()}.at.example.com"   # malformed email
    elif t == 5: contact = f"+91-{ph()[:5]}-{ph()[:5]}"; truth.append(("contact", "phone"))
    if t in (6, 7): doc = aad(sp=(t == 7)); truth.append(("doc_number", "aadhaar"))
    elif t == 8: doc = card(sp=bool(k % 4)); truth.append(("doc_number", "credit_card"))
    elif t == 9: doc = r.choice([decoy12(), decoy16()])         # decoy: fails checksum, not PII
    if k % 6 == 1: note = f"Please email {nm.split()[0].lower()}{r.randint(1,9)}@mail.test for updates"; truth.append(("note", "email"))
    elif k % 6 == 3: note = f"Call on {ph()} after 5pm"; truth.append(("note", "phone"))
    elif k % 6 == 5: note = f"Order {decoy12()} shipped on 12-03-2025"
    elif k % 6 == 0: note = "Customer prefers morning delivery"
    add(nm, contact, doc, note, oref, truth)
# drop a few names to test blanks, and add a tricky non-name value
rows[5][0] = ""; labels = [l for l in labels if not (l[1] == 5 and l[2] == "full_name")]
rows[11][0] = "N/A"; labels = [l for l in labels if not (l[1] == 11 and l[2] == "full_name")]

os.makedirs("data/manual", exist_ok=True)
with open("data/manual/manual_test_set.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["full_name", "contact", "doc_number", "note", "order_ref"]); w.writerows(rows)
with open("data/manual/manual_labels.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["source", "row", "column", "class"]); w.writerows(labels)
print(len(rows), "rows,", len(labels), "labelled cells")
