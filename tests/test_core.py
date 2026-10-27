from src.validators import (verhoeff_valid, verhoeff_check_digit, luhn_valid, aadhaar_valid, card_valid,
                            phone_valid, email_valid, pan_valid, dl_valid, geo_valid)
from src.detect import Detector
from src.config import load_rules
from src.link import link

RULES = load_rules("config/rules.yaml")


def test_verhoeff_roundtrip_and_reject():
    p = "23456789012"
    assert verhoeff_valid(p + verhoeff_check_digit(p))
    assert not verhoeff_valid(p + str((int(verhoeff_check_digit(p)) + 1) % 10))


def test_luhn_known_values():
    assert luhn_valid("4111111111111111")
    assert not luhn_valid("4111111111111112")
    assert not luhn_valid("1234")


def test_aadhaar_rules():
    p = "23456789012"; num = p + verhoeff_check_digit(p)
    assert aadhaar_valid(num) and aadhaar_valid(f"{num[:4]} {num[4:8]} {num[8:]}")
    assert not aadhaar_valid("123456789012")      # first digit 1 is not allowed


def test_phone_and_email():
    assert phone_valid("+91 9876543210") and phone_valid("9876543210") and not phone_valid("1234567890")
    assert email_valid("a.b@example.com") and not email_valid("a@@b.com") and not email_valid("no-at.example.com")


def test_detector_dual_pass_rejects_order_id():
    d = Detector(RULES)
    p = "23456789012"; good = p + verhoeff_check_digit(p)
    bad = "234567890123" if good != "234567890123" else "234567890124"
    assert [h[0] for h in d.scan_cell("aadhaar_no", good)] == ["aadhaar"]
    assert d.scan_cell("aadhaar_no", bad) == []


def test_card_digits_not_double_counted_as_aadhaar():
    d = Detector(RULES)
    classes = [h[0] for h in d.scan_cell("data", "4111 1111 1111 1111")]
    assert classes == ["credit_card"]


def test_masking_never_stores_full_value():
    d = Detector(RULES)
    hit = d.scan_cell("email", "someone@example.com")[0]
    assert "someone" not in hit[2] and hit[2].endswith(".com")


def test_contextual_needs_column_hint():
    d = Detector(RULES)
    assert d.scan_cell("full_name", "Asha Rao")[0][0] == "name"
    assert d.scan_cell("col_d", "Asha Rao") == []


def test_linker_statuses():
    f = [{"source": "a.csv", "column": c} for c in ("x", "y", "z")]
    decl = {"a.csv.x": {"purpose": "p", "retention": "r"}, "a.csv.y": {"purpose": "p"}}
    out = link(f, decl)
    assert [o["link_status"] for o in out] == ["matched", "partial", "orphan"]
    assert out[1]["gap"] == "missing retention"


def test_new_validators():
    assert pan_valid("ABCPE1234F") and not pan_valid("ABCXE1234F") and not pan_valid("ABCPE12345")
    assert dl_valid("KA0120110012345") and not dl_valid("KA0118000012345")
    assert geo_valid("12.9716, 77.5946") and not geo_valid("120.250, 77.500")


def test_hint_required_for_ambiguous_numbers():
    d = Detector(RULES)
    assert [h[0] for h in d.scan_cell("acct_no", "12345678901234")] == ["bank_account"]
    assert d.scan_cell("misc", "12345678901234") == []          # no hint -> not reported
    assert [h[0] for h in d.scan_cell("pin_code", "560100")] == ["pin_code"]


def test_placeholder_names_ignored():
    d = Detector(RULES)
    assert d.scan_cell("full_name", "N/A") == [] and d.scan_cell("full_name", "Anonymous") == []


def test_every_type_has_official_category():
    cats = set(RULES["categories"])
    assert all(v["category"] in cats for v in RULES["classes"].values())
