"""Ticker detection: find valid stock symbols in text while rejecting the
common-word / slang false positives that plague WSB scanning."""

import csv
import re
from functools import lru_cache

from config import TICKERS_FILE

# Tokens that ARE valid tickers but are overwhelmingly used as English words or
# WSB slang in comments. We ignore these unless they appear with a $ prefix
# (an explicit cashtag like "$BE" clearly means the ticker).
BLACKLIST = {
    # WSB / finance slang and acronyms
    "DD", "YOLO", "HODL", "FD", "FOMO", "ATH", "ATL", "EOD", "EOW", "AH", "PM",
    "ER", "EPS", "PE", "PT", "IV", "OTM", "ITM", "ATM", "TA", "FA", "IPO", "ETF",
    "CEO", "CFO", "COO", "CTO", "SEC", "FED", "IRS", "GDP", "USD", "EU", "UK",
    "US", "USA", "IMO", "IMHO", "TLDR", "RIP", "LOL", "LMAO", "LMFAO", "WTF",
    "OMG", "BTW", "FYI", "AKA", "ASAP", "NSFW", "TIL", "OP", "MOD", "PSA",
    "GUH", "HOLD", "MOON", "PUMP", "DUMP", "CALL", "PUT", "GAIN", "LOSS", "BAG",
    "WSB", "QQQ",  # QQQ is an ETF but rarely a "discussed stock" pick; keep noise down
    # Common English words that collide with tickers
    "A", "I", "AN", "AND", "ARE", "ALL", "ANY", "AM", "AT", "BE", "BIG", "BUY",
    "BY", "CAN", "DO", "EVER", "FOR", "GO", "GOOD", "GOT", "HAS", "HE", "IT",
    "ITS", "LOW", "MAN", "NEW", "NO", "NOW", "ON", "ONE", "OR", "OUT", "PLAY",
    "REAL", "RED", "RUN", "SEE", "SO", "TWO", "UP", "VS", "WELL", "YES", "OK",
    "NEXT", "OPEN", "TELL", "TURN", "FUN", "LOVE", "CASH", "HUGE", "EOY", "FF",
    "WSJ", "CNBC", "AI", "EV", "YOY", "QOQ", "MOM", "DCA", "ROI", "AGM",
}

# $TICKER  or  bare 1-5 letter all-caps token.
CASHTAG_RE = re.compile(r"\$([A-Za-z]{1,5})\b")
BARE_RE = re.compile(r"\b([A-Z]{1,5})\b")


@lru_cache(maxsize=1)
def load_tickers() -> dict[str, str]:
    """Return {symbol: company_name}. Built by data/refresh_tickers.py."""
    if not TICKERS_FILE.exists():
        raise RuntimeError(
            f"{TICKERS_FILE} not found. Run `python data/refresh_tickers.py` first."
        )
    out: dict[str, str] = {}
    with TICKERS_FILE.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = (row.get("symbol") or "").strip().upper()
            if sym:
                out[sym] = (row.get("name") or "").strip()
    return out


def company_name(symbol: str) -> str:
    return load_tickers().get(symbol.upper(), "")


def extract_tickers(text: str) -> set[str]:
    """Return the set of valid tickers mentioned in a single piece of text.

    A set (not a count) so that one comment repeating "$GME GME GME" counts as
    a single mention for that comment.
    """
    if not text:
        return set()
    valid = load_tickers()
    found: set[str] = set()

    # Cashtags bypass the blacklist (explicit intent).
    for m in CASHTAG_RE.finditer(text):
        sym = m.group(1).upper()
        if sym in valid:
            found.add(sym)

    # Bare uppercase tokens must be valid AND not blacklisted.
    for m in BARE_RE.finditer(text):
        sym = m.group(1)
        if sym in BLACKLIST:
            continue
        if sym in valid:
            found.add(sym)

    return found
