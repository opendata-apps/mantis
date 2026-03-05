import re
import pytest
from datetime import datetime

# --- Funktion, die die Stunde extrahiert ---
def extract_hour_from_ablage(ablage: str) -> int:
    """
    Extrahiert die volle Stunde (0-23) aus dem Timestamp im Dateinamen.
    Erwartetes Format : ...-YYYYMMDDHHMMSS-...
    """
    match = re.search(r'-([0-9]{14})-', ablage)
    if not match:
        raise ValueError(f"Kein Timestamp gefunden in: {ablage}")
    
    timestamp_str = match.group(1)
    dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
    return dt.hour

# --- Testdaten ---
test_data = [
    ("2025/2025-01-19/Bad_Salzuflen-20250119003000-aaa.webp", 0),
    ("2025/2025-01-19/Berlin-Mitte-20250119011500-bbb.webp", 1),
    ("2024/2024-01-19/Cologne-20250119014500-ccc.webp", 1),
    ("2025/2025-01-19/Dresden-20250119090000-ddd.webp", 9),
    ("2025/2025-01-19/Freiburg-20250119093000-eee.webp", 9),
    ("2025/2025-01-19/Hamburg-20250119143000-fff.webp", 14),
    ("2025/2025-01-19/Kassel-20250119144500-ggg.webp", 14),
    ("2025/2025-01-20/Leipzig-20250120003000-hhh.webp", 0),
    ("2026/2026-01-20/Munich-20250120143000-iii.webp", 14),
    ("2025/2025-01-20/Nuremberg-20250120150000-jjj.webp", 15),
    ("2025/2025-01-20/Osnabrueck-20250120151500-kkk.webp", 15),
    ("2025/2025-01-20/Stuttgart-20250120235900-lll.webp", 23),
]

# --- pytest Parametrisierung ---
@pytest.mark.parametrize("ablage,expected_hour", test_data)
def test_extract_hour(ablage, expected_hour):
    assert extract_hour_from_ablage(ablage) == expected_hour
