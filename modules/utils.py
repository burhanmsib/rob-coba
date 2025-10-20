from datetime import datetime, date
from decimal import Decimal

# ======================== KONVERSI NUMERIK ========================
def safe_float(value, default=0.0):
    """
    Konversi berbagai tipe (str, int, Decimal) menjadi float aman.
    Jika gagal -> return default (0.0).
    """
    if value is None or value == "":
        return default
    try:
        if isinstance(value, (float, int)):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        s = str(value).strip().replace(",", ".")
        return float(s)
    except Exception:
        return default


# ======================== PARSE & FORMAT TANGGAL ========================
def parse_date_safe(val):
    """
    Ubah berbagai format tanggal (string / date) menjadi objek date (Python).
    Digunakan agar st.date_input tidak error saat nilai tanggal tidak standar.
    """
    if isinstance(val, date):
        return val
    if val is None:
        return None

    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            continue
    return None  # biarkan user pilih manual kalau parsing gagal


def to_db_date_str(d):
    """
    Ubah objek date menjadi format string 'YYYY-MM-DD' untuk disimpan di database.
    """
    if isinstance(d, date):
        return d.strftime("%Y-%m-%d")

    parsed = parse_date_safe(d)
    return parsed.strftime("%Y-%m-%d") if parsed else None
