"""Generate SYNTHETIC data only: CSV files, a SQLite DB, declarations and cell-level labels.
All values are random. Nothing here is real personal data."""
import csv, json, random, sqlite3, os
from .validators import verhoeff_check_digit, luhn_check_digit

FIRST = ["Aarav","Vivaan","Ananya","Diya","Rohan","Priya","Karthik","Sneha","Arjun","Meera","Rahul","Kavya","Ishaan","Neha","Vikram","Divya"]
LAST = ["Sharma","Reddy","Iyer","Nair","Gowda","Patel","Singh","Rao","Menon","Kulkarni","Das","Shetty"]
STREETS = ["MG Road","Brigade Road","Residency Road","Hosur Road","Outer Ring Road","4th Cross","Church Street"]
CITIES = ["Bengaluru","Mysuru","Chennai","Hyderabad","Pune"]
DOMAINS = ["example.com","mail.test","demo.org","sample.in"]


def name(r): return f"{r.choice(FIRST)} {r.choice(LAST)}"
def email(r, n): return f"{n.lower().replace(' ', '.')}{r.randint(1,99)}@{r.choice(DOMAINS)}"
def phone(r, fmt=None):
    d = f"{r.choice('6789')}{r.randint(0,999999999):09d}"
    return r.choice([d, f"+91 {d}", f"+91-{d[:5]}-{d[5:]}"]) if fmt is None else d
def aadhaar(r):
    p = f"{r.choice('23456789')}{r.randint(0,99999999999-0):010d}"[:11]
    p = p.ljust(11, "0")
    full = p + verhoeff_check_digit(p)
    return r.choice([full, f"{full[:4]} {full[4:8]} {full[8:]}"])
def card(r):
    p = r.choice(["4","5"]) + f"{r.randint(0,10**14-1):014d}"
    full = p + luhn_check_digit(p)
    return r.choice([full, " ".join(full[i:i+4] for i in range(0, 16, 4))])
def dob(r): return f"{r.randint(1,28):02d}-{r.randint(1,12):02d}-{r.randint(1975,2004)}"
def addr(r): return f"{r.randint(1,250)} {r.choice(STREETS)}, {r.choice(CITIES)}"
def order_ref(r): return str(r.randint(10**11, 10**12 - 1))      # decoy: 12 digits, not PII
def tracking(r): return str(r.randint(10**15, 10**16 - 1))       # decoy: 16 digits, not PII
def txn(r): return f"TXN{r.randint(10**8,10**9-1)}"


def build(out_dir="data", seed=42, n=150):
    r = random.Random(seed)
    syn, lab = os.path.join(out_dir, "synthetic"), os.path.join(out_dir, "labelled")
    os.makedirs(syn, exist_ok=True); os.makedirs(lab, exist_ok=True)
    labels = []  # (source, row, column, class)

    def L(src, row, col, cls): labels.append((src, row, col, cls))

    # ---- customers.csv
    rows = []
    for i in range(n):
        nm = name(r); em = email(r, nm); ph = phone(r); ad = aadhaar(r)
        note = ""
        k = r.random()
        if k < 0.15: note = f"Call back on {phone(r, 'plain')} after 6pm"; L("customers.csv", i, "notes", "phone")
        elif k < 0.30:
            alt = email(r, name(r)); note = f"Alternate contact: {alt}"; L("customers.csv", i, "notes", "email")
        elif k < 0.6: note = r.choice(["Prefers WhatsApp", "VIP customer", "Address verified", "Ref no 4521 logged", "Follow up next week"])
        a, d_ = addr(r), dob(r)
        rows.append([f"C{1000+i}", nm, em, ph, ad, d_, a, order_ref(r), note])
        L("customers.csv", i, "full_name", "contextual_pii"); L("customers.csv", i, "email", "email")
        L("customers.csv", i, "mobile", "phone"); L("customers.csv", i, "aadhaar_no", "aadhaar")
        L("customers.csv", i, "dob", "contextual_pii"); L("customers.csv", i, "address", "contextual_pii")
    with open(os.path.join(syn, "customers.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["customer_id","full_name","email","mobile","aadhaar_no","dob","address","order_ref","notes"]); w.writerows(rows)

    # ---- payments.csv
    rows = []
    for i in range(n):
        nm = name(r)
        rows.append([txn(r), card(r), tracking(r), f"{r.randint(100,99999)/100:.2f}", email(r, nm)])
        L("payments.csv", i, "card_number", "credit_card"); L("payments.csv", i, "contact_email", "email")
    with open(os.path.join(syn, "payments.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["txn_id","card_number","tracking_no","amount","contact_email"]); w.writerows(rows)

    # ---- legacy_export.csv : unhelpful column names, no hints
    rows = []
    for i in range(n // 2):
        nm = name(r)
        rows.append([f"R{i}", aadhaar(r), phone(r), nm, r.choice(["A","B","C"])])
        L("legacy_export.csv", i, "col_b", "aadhaar"); L("legacy_export.csv", i, "col_c", "phone")
        L("legacy_export.csv", i, "col_d", "contextual_pii")  # present in data, but no column hint -> expected miss
    with open(os.path.join(syn, "legacy_export.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["col_a","col_b","col_c","col_d","col_e"]); w.writerows(rows)

    # ---- demo.db
    db = os.path.join(syn, "demo.db")
    if os.path.exists(db): os.remove(db)
    con = sqlite3.connect(db); cur = con.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, phone TEXT, aadhaar TEXT, signup_ts TEXT)")
    cur.execute("CREATE TABLE orders (order_id INTEGER PRIMARY KEY, user_id INTEGER, order_ref TEXT, amount REAL, is_paid INTEGER)")
    cur.execute("CREATE TABLE audit_log (id INTEGER PRIMARY KEY, message TEXT)")
    cur.execute("CREATE TABLE products (sku TEXT, title TEXT, price REAL)")
    for i in range(n):
        nm = name(r)
        cur.execute("INSERT INTO users VALUES (?,?,?,?,?,?)", (i+1, nm, email(r, nm), phone(r), aadhaar(r), f"2025-{r.randint(1,12):02d}-{r.randint(1,28):02d} 10:00:00"))
        L("demo.db:users", i, "name", "contextual_pii"); L("demo.db:users", i, "email", "email")
        L("demo.db:users", i, "phone", "phone"); L("demo.db:users", i, "aadhaar", "aadhaar")
        cur.execute("INSERT INTO orders VALUES (?,?,?,?,?)", (i+1, r.randint(1, n), order_ref(r), r.randint(100, 9999)/10, r.randint(0, 1)))
    for i in range(80):
        k = r.random()
        if k < 0.3: msg = f"password reset sent to {email(r, name(r))}"; L("demo.db:audit_log", i, "message", "email")
        elif k < 0.45: msg = f"OTP delivered to {phone(r, 'plain')}"; L("demo.db:audit_log", i, "message", "phone")
        else: msg = r.choice(["login ok", "export started", "config changed", "job completed", "token refreshed"])
        cur.execute("INSERT INTO audit_log VALUES (?,?)", (i+1, msg))
    for i in range(30): cur.execute("INSERT INTO products VALUES (?,?,?)", (f"SKU{i:04d}", f"Product {i}", r.randint(10, 999)))
    con.commit(); con.close()

    # ---- declarations (purpose + retention). Deliberately incomplete to exercise the linker.
    decl = {
        "customers.csv.full_name": {"purpose": "Order fulfilment", "retention": "24 months"},
        "customers.csv.email": {"purpose": "Order communication", "retention": "24 months"},
        "customers.csv.mobile": {"purpose": "Delivery updates"},                         # partial: no retention
        "customers.csv.aadhaar_no": {"purpose": "KYC verification", "retention": "5 years"},
        "customers.csv.dob": {"purpose": "Age verification", "retention": "24 months"},
        "customers.csv.address": {"purpose": "Delivery", "retention": "24 months"},
        "payments.csv.card_number": {"retention": "12 months"},                          # partial: no purpose
        "payments.csv.contact_email": {"purpose": "Payment receipts", "retention": "12 months"},
        "demo.db:users.name": {"purpose": "Account management", "retention": "Account lifetime"},
        "demo.db:users.email": {"purpose": "Account management", "retention": "Account lifetime"},
        "demo.db:users.phone": {"purpose": "Two-factor authentication", "retention": "Account lifetime"},
        # legacy_export.csv, demo.db:users.aadhaar, notes, audit_log.message: undeclared -> orphan
    }
    with open(os.path.join("config", "declarations.json"), "w", encoding="utf-8") as f: json.dump(decl, f, indent=2)
    with open(os.path.join(lab, "cell_labels.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["source", "row", "column", "class"]); w.writerows(labels)
    print(f"Generated synthetic data in {syn}; {len(labels)} labelled cells")
