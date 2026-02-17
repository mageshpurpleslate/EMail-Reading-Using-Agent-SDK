import re
from datetime import datetime, timedelta

from models import AttendanceException

# Exception type keywords mapped to canonical names
_EXCEPTION_TYPES = [
    (r"\blate[\s-]?in\b", "Late-In"),
    (r"\blate\s+arrival\b", "Late-In"),
    (r"\bcoming\s+late\b", "Late-In"),
    (r"\barriv(?:ing|e|al)\s+late\b", "Late-In"),
    (r"\bhours?\s+late\b", "Late-In"),
    (r"\bearly[\s-]?out\b", "Early-Out"),
    (r"\bleav(?:ing|e)\s+early\b", "Early-Out"),
    (r"\bhalf[\s-]?day\b", "Half-Day"),
    (r"\bwork[\s-]?from[\s-]?home\b", "Work-From-Home"),
    (r"\bwfh\b", "Work-From-Home"),
    (r"\bleave\s+request\b", "Leave"),
    (r"\bsick\s+leave\b", "Leave"),
    (r"\bcasual\s+leave\b", "Leave"),
    (r"\bday\s+off\b", "Leave"),
]

# Date patterns
_DATE_PATTERNS = [
    # DD/MM/YYYY or DD-MM-YYYY
    (r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b", "dmy"),
    # YYYY-MM-DD
    (r"\b(\d{4})-(\d{2})-(\d{2})\b", "ymd"),
    # 18th Feb, 18 February, Feb 18 etc.
    (r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b", "dm"),
    (r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?\b", "md"),
]

_MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

# Reason extraction patterns
_REASON_PATTERNS = [
    r"(?:reason|because|due\s+to|on\s+account\s+of)\s*[:\-]?\s*(.+?)(?:[.,;]\s|$)",
]

# Employee ID pattern
_EMPID_PATTERN = r"\b(EMP\d{3,})\b"

# Duration patterns
_DURATION_PATTERNS = [
    r"(\d+\s+hours?\s+late)",
    r"(approximately\s+\d+\s+hours?\s+late)",
    r"(?:expected\s+arrival|arriving\s+at|reach\s+by)\s*[:\-]?\s*(\d{1,2}[:\.]?\d{0,2}\s*(?:AM|PM|am|pm)?)",
]

# Name patterns: "- Name (EMP...)" or "Regards, Name" or "Name (EMP...)"
_NAME_PATTERNS = [
    r"-\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(",
    r"(?:regards|thanks|sincerely)\s*,?\s*\n?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(\s*EMP\d+",
]


def _extract_exception_type(text: str) -> str:
    lower = text.lower()
    for pattern, exc_type in _EXCEPTION_TYPES:
        if re.search(pattern, lower):
            return exc_type
    return ""


def _extract_date(text: str) -> str:
    lower = text.lower()

    # Relative dates
    today = datetime.now()
    if re.search(r"\btoday\b", lower):
        return today.strftime("%d/%m/%Y")
    if re.search(r"\btomorrow\b", lower):
        return (today + timedelta(days=1)).strftime("%d/%m/%Y")
    if re.search(r"\byesterday\b", lower):
        return (today - timedelta(days=1)).strftime("%d/%m/%Y")

    # Explicit date patterns
    for pattern, fmt in _DATE_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            if fmt == "dmy":
                return f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{m.group(3)}"
            elif fmt == "ymd":
                return f"{int(m.group(3)):02d}/{int(m.group(2)):02d}/{m.group(1)}"
            elif fmt == "dm":
                day = int(m.group(1))
                month = _MONTH_MAP.get(m.group(2).lower(), 0)
                year = today.year
                return f"{day:02d}/{month:02d}/{year}"
            elif fmt == "md":
                month = _MONTH_MAP.get(m.group(1).lower(), 0)
                day = int(m.group(2))
                year = today.year
                return f"{day:02d}/{month:02d}/{year}"
    return ""


def _extract_employee_id(text: str) -> str:
    m = re.search(_EMPID_PATTERN, text)
    return m.group(1) if m else ""


def _extract_reason(text: str) -> str:
    for pattern in _REASON_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            reason = m.group(1).strip()
            # Clean up trailing punctuation artifacts
            reason = reason.rstrip(".,;")
            return reason
    return ""


def _extract_duration(text: str) -> str:
    for pattern in _DURATION_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1) if m.lastindex else m.group(0)
    return ""


def _extract_employee_name(text: str) -> str:
    for pattern in _NAME_PATTERNS:
        m = re.search(pattern, text, re.MULTILINE)
        if m:
            return m.group(1).strip()
    return ""


def parse_attendance_exception(text: str) -> AttendanceException:
    """Parse an attendance exception email and extract structured fields."""
    return AttendanceException(
        employee_name=_extract_employee_name(text),
        employee_id=_extract_employee_id(text),
        exception_type=_extract_exception_type(text),
        date=_extract_date(text),
        reason=_extract_reason(text),
        duration=_extract_duration(text),
        raw_text=text,
    )
