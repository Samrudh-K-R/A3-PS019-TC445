"""Checksum and format validators. Pure functions, no I/O."""
import re

# Verhoeff tables (dihedral group D5)
_D = [[0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],[3,4,0,1,2,8,9,5,6,7],
      [4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],[6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],
      [8,7,6,5,9,3,2,1,0,4],[9,8,7,6,5,4,3,2,1,0]]
_P = [[0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],[8,9,1,6,0,4,3,5,2,7],
      [9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],[2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8]]
_INV = [0,4,3,2,1,5,6,7,8,9]


def verhoeff_valid(number: str) -> bool:
    if not number.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def verhoeff_check_digit(payload: str) -> str:
    c = 0
    for i, ch in enumerate(reversed(payload)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return str(_INV[c])


def luhn_valid(number: str) -> bool:
    if not number.isdigit() or not 13 <= len(number) <= 19:
        return False
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def luhn_check_digit(payload: str) -> str:
    for d in "0123456789":
        if luhn_valid(payload + d):
            return d
    raise ValueError("no digit")


def aadhaar_valid(text: str) -> bool:
    digits = re.sub(r"[\s-]", "", text)
    return len(digits) == 12 and digits[0] in "23456789" and verhoeff_valid(digits)


def card_valid(text: str) -> bool:
    return luhn_valid(re.sub(r"[\s-]", "", text))


_PHONE_IN = re.compile(r"^(?:\+?91[\s-]?)?[6-9]\d{9}$")


def phone_valid(text: str) -> bool:
    """Indian mobile in E.164-compatible form: optional +91 then 10 digits starting 6-9."""
    t = re.sub(r"[\s()-]", "", text)
    return bool(_PHONE_IN.match(t))


_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")


def email_valid(text: str) -> bool:
    return bool(_EMAIL.match(text)) and ".." not in text


_PAN_TYPES = "ABCFGHLJPT"   # 4th letter = holder type (P=person, C=company, ...)


def pan_valid(text: str) -> bool:
    return bool(re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]", text)) and text[3] in _PAN_TYPES


def dl_valid(text: str) -> bool:
    """Indian driving licence: state(2 letters) RTO(2) year(4) serial(7); year must be plausible."""
    t = re.sub(r"[\s-]", "", text)
    return bool(re.fullmatch(r"[A-Z]{2}\d{13}", t)) and 1950 <= int(t[4:8]) <= 2030


def geo_valid(text: str) -> bool:
    try:
        lat, lon = [float(x) for x in text.split(",")]
    except ValueError:
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


VALIDATORS = {
    "verhoeff": aadhaar_valid,
    "luhn": card_valid,
    "e164": phone_valid,
    "email": email_valid,
    "pan": pan_valid,
    "dl": dl_valid,
    "geo": geo_valid,
    "none": lambda s: True,
}
