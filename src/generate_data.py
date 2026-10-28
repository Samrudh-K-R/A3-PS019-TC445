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
def gender(r): return r.choice(["Male", "Female", "Male", "Female", "Other", "M", "F"])
def age(r): return str(r.randint(18, 72))
def pin(r): return f"{r.choice('56789')}{r.randint(0, 99999):05d}"
def geo(r): return f"{r.uniform(8, 30):.4f}, {r.uniform(70, 88):.4f}"
def _letters(r, k): return "".join(r.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(k))
def pan(r): return _letters(r, 3) + "P" + _letters(r, 1) + f"{r.randint(0, 9999):04d}" + _letters(r, 1)
def pan_decoy(r): return _letters(r, 3) + "X" + _letters(r, 1) + f"{r.randint(0, 9999):04d}" + _letters(r, 1)   # 4th letter invalid
def passport(r): return r.choice("ABCDEFGHJKLMNPRSTUVWY") + str(r.randint(1, 9)) + f"{r.randint(0, 999999):06d}"
def voter(r): return _letters(r, 3) + f"{r.randint(0, 9999999):07d}"
def dl(r):
    base = f"{r.choice(['KA', 'TN', 'MH', 'DL', 'AP'])}{r.randint(1, 60):02d}"
    tail = f"{r.randint(1995, 2024)}{r.randint(0, 9999999):07d}"
    return r.choice([base + tail, f"{base} {tail}"])
def acct(r): return str(r.randint(10**10, 10**r.choice([12, 13, 14]) - 1))
def ifsc(r): return r.choice(["SBIN", "HDFC", "ICIC", "UTIB", "CNRB"]) + "0" + "".join(r.choice("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(6))
def upi(r, n): return f"{n.lower().replace(' ', '.')}{r.randint(1, 99)}@{r.choice(['oksbi', 'okaxis', 'ybl', 'paytm', 'okhdfcbank'])}"
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
        gd, ag, pc = gender(r), age(r), pin(r)
        rows.append([f"C{1000+i}", nm, em, ph, ad, d_, a, order_ref(r), note, gd, ag, pc])
        L("customers.csv", i, "full_name", "name"); L("customers.csv", i, "email", "email")
        L("customers.csv", i, "mobile", "phone"); L("customers.csv", i, "aadhaar_no", "aadhaar")
        L("customers.csv", i, "dob", "dob"); L("customers.csv", i, "address", "address")
        L("customers.csv", i, "gender", "gender"); L("customers.csv", i, "age", "age"); L("customers.csv", i, "pin_code", "pin_code")
    with open(os.path.join(syn, "customers.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["customer_id","full_name","email","mobile","aadhaar_no","dob","address","order_ref","notes","gender","age","pin_code"]); w.writerows(rows)

    # ---- payments.csv
    rows = []
    for i in range(n):
        nm = name(r)
        rows.append([txn(r), card(r), tracking(r), f"{r.randint(100,99999)/100:.2f}", email(r, nm)])
        L("payments.csv", i, "card_number", "credit_card"); L("payments.csv", i, "contact_email", "email")
    with open(os.path.join(syn, "payments.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["txn_id","card_number","tracking_no","amount","contact_email"]); w.writerows(rows)

    # ---- kyc.csv (government identifiers) + look-alikes
    rows = []
    for i in range(n):
        has_pp = r.random() < 0.7
        rows.append([f"C{1000+i}", pan(r), passport(r) if has_pp else "", voter(r), dl(r), pan_decoy(r), "T" + str(r.randint(1000000, 9999999))])
        L("kyc.csv", i, "pan_no", "pan"); L("kyc.csv", i, "voter_id", "voter_id"); L("kyc.csv", i, "dl_no", "driving_licence")
        if has_pp: L("kyc.csv", i, "passport_no", "passport")
    with open(os.path.join(syn, "kyc.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["customer_id","pan_no","passport_no","voter_id","dl_no","employee_code","ticket_ref"]); w.writerows(rows)

    # ---- finance.csv (bank account, IFSC, UPI) + look-alikes
    rows = []
    for i in range(n):
        nm = name(r)
        rows.append([f"C{1000+i}", acct(r), ifsc(r), upi(r, nm), order_ref(r), f"BR-{r.randint(1000, 9999)}"])
        L("finance.csv", i, "acct_no", "bank_account"); L("finance.csv", i, "ifsc_code", "ifsc"); L("finance.csv", i, "upi_id", "upi")
    with open(os.path.join(syn, "finance.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["customer_id","acct_no","ifsc_code","upi_id","invoice_no","branch_ref"]); w.writerows(rows)

    # ---- locations.csv (geo, PIN, address) + look-alikes
    rows = []
    for i in range(n):
        rows.append([f"V{i}", geo(r), pin(r), addr(r), f"{r.uniform(100, 400):.3f}, {r.uniform(200, 500):.3f}", str(r.randint(1, 120)), str(r.randint(100000, 999999))])
        L("locations.csv", i, "geo_point", "geo"); L("locations.csv", i, "pin_code", "pin_code"); L("locations.csv", i, "address", "address")
    with open(os.path.join(syn, "locations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["visit_id","geo_point","pin_code","address","range_km","page_no","dispatch_code"]); w.writerows(rows)

    # ---- legacy_export.csv : unhelpful column names, no hints
    rows = []
    for i in range(n // 2):
        nm = name(r)
        rows.append([f"R{i}", aadhaar(r), phone(r), nm, r.choice(["A","B","C"])])
        L("legacy_export.csv", i, "col_b", "aadhaar"); L("legacy_export.csv", i, "col_c", "phone")
        L("legacy_export.csv", i, "col_d", "name")  # present in data, but no column hint -> expected miss
    with open(os.path.join(syn, "legacy_export.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["col_a","col_b","col_c","col_d","col_e"]); w.writerows(rows)

    # ---- demo.db
    db = os.path.join(syn, "demo.db")
    if os.path.exists(db): os.remove(db)
    con = sqlite3.connect(db); cur = con.cursor()
    cur.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, phone TEXT, aadhaar TEXT, signup_ts TEXT, gender TEXT, age INTEGER, pincode TEXT, upi_id TEXT)")
    cur.execute("CREATE TABLE orders (order_id INTEGER PRIMARY KEY, user_id INTEGER, order_ref TEXT, amount REAL, is_paid INTEGER)")
    cur.execute("CREATE TABLE audit_log (id INTEGER PRIMARY KEY, message TEXT)")
    cur.execute("CREATE TABLE products (sku TEXT, title TEXT, price REAL)")
    for i in range(n):
        nm = name(r)
        cur.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)", (i+1, nm, email(r, nm), phone(r), aadhaar(r), f"2025-{r.randint(1,12):02d}-{r.randint(1,28):02d} 10:00:00", gender(r), int(age(r)), pin(r), upi(r, nm)))
        L("demo.db:users", i, "name", "name"); L("demo.db:users", i, "email", "email")
        L("demo.db:users", i, "phone", "phone"); L("demo.db:users", i, "aadhaar", "aadhaar")
        L("demo.db:users", i, "gender", "gender"); L("demo.db:users", i, "age", "age"); L("demo.db:users", i, "pincode", "pin_code"); L("demo.db:users", i, "upi_id", "upi")
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
        "customers.csv.gender": {"purpose": "Personalisation", "retention": "24 months"},
        "customers.csv.age": {"purpose": "Age verification", "retention": "24 months"},
        "customers.csv.pin_code": {"purpose": "Delivery", "retention": "24 months"},
        "kyc.csv.pan_no": {"purpose": "Tax reporting", "retention": "7 years"},
        "kyc.csv.passport_no": {"purpose": "Identity proof"},                              # partial: no retention
        "kyc.csv.dl_no": {"purpose": "Identity proof", "retention": "5 years"},
        "finance.csv.acct_no": {"purpose": "Refund payout", "retention": "7 years"},
        "finance.csv.ifsc_code": {"purpose": "Refund payout", "retention": "7 years"},
        "locations.csv.address": {"purpose": "Site visits", "retention": "12 months"},
        "locations.csv.pin_code": {"purpose": "Site visits", "retention": "12 months"},
        # undeclared on purpose (orphans): kyc.voter_id, finance.upi_id, locations.geo_point, demo.db users gender/age/pincode/upi_id
        # legacy_export.csv, demo.db:users.aadhaar, notes, audit_log.message: undeclared -> orphan
    }
    with open(os.path.join("config", "declarations.json"), "w", encoding="utf-8") as f: json.dump(decl, f, indent=2)
    with open(os.path.join(lab, "cell_labels.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["source", "row", "column", "class"]); w.writerows(labels)
    print(f"Generated synthetic data in {syn}; {len(labels)} labelled cells")
