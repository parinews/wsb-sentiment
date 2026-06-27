"""Build data/tickers.csv from the official Nasdaq Trader symbol directory.

These are free, public, unauthenticated files (no API key, no rate limits worth
worrying about). Re-run this occasionally to pick up newly listed tickers:

    python data/refresh_tickers.py

Output: data/tickers.csv with `symbol,name` rows (header included).
"""

import csv
import io
import sys
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
OUT_FILE = DATA_DIR / "tickers.csv"

SOURCES = [
    # (url, symbol_field, name_field)
    ("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt", "Symbol", "Security Name"),
    ("https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt", "ACT Symbol", "Security Name"),
]


def _download(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def build() -> dict[str, str]:
    symbols: dict[str, str] = {}
    for url, sym_field, name_field in SOURCES:
        text = _download(url)
        reader = csv.DictReader(io.StringIO(text), delimiter="|")
        for row in reader:
            symbol = (row.get(sym_field) or "").strip().upper()
            name = (row.get(name_field) or "").strip()
            # Skip footer line ("File Creation Time...") and test issues.
            if not symbol or symbol.startswith("FILE CREATION"):
                continue
            if (row.get("Test Issue") or "").strip().upper() == "Y":
                continue
            # Drop symbols with non-alphabetic chars (warrants/units like ABC.W).
            if not symbol.isalpha():
                continue
            symbols.setdefault(symbol, name)
    return symbols


def main() -> int:
    symbols = build()
    if len(symbols) < 1000:
        print(f"Refusing to write: only got {len(symbols)} symbols (download issue?).")
        return 1
    with OUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["symbol", "name"])
        for symbol in sorted(symbols):
            writer.writerow([symbol, symbols[symbol]])
    print(f"Wrote {len(symbols)} tickers to {OUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
