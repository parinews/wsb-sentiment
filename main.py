"""Orchestrator: fetch r/wallstreetbets discussion, rank tickers by mentions,
score sentiment, and email (or preview) the daily report.

Usage:
    python main.py             # fetch, build, and send the email
    python main.py --dry-run   # fetch and build, but print HTML instead of sending
"""

import argparse
import sys
from datetime import datetime

from config import TOP_N
from email_report import build_html, send_email, subject_line
from reddit_client import fetch_texts
from sentiment import aggregate, score
from tickers import extract_tickers


def analyze(texts: list[str]):
    """Turn raw text blobs into ranked per-ticker sentiment."""
    records: list[tuple[set[str], float]] = []
    for text in texts:
        tickers = extract_tickers(text)
        if not tickers:
            continue
        records.append((tickers, score(text)))

    by_ticker = aggregate(records)
    ranked = sorted(by_ticker.values(), key=lambda t: t.mentions, reverse=True)
    return ranked[:TOP_N]


def main() -> int:
    parser = argparse.ArgumentParser(description="WSB daily sentiment email")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the HTML report to stdout instead of sending an email.",
    )
    args = parser.parse_args()

    date_str = datetime.now().strftime("%a, %b %d %Y")

    print("Fetching r/wallstreetbets ...")
    texts = fetch_texts()

    print("Detecting tickers and scoring sentiment ...")
    ranked = analyze(texts)

    print(f"\nTop {len(ranked)} tickers:")
    for rank, t in enumerate(ranked, start=1):
        print(f"  {rank:>2}. {t.symbol:<6} {t.mentions:>4} mentions  "
              f"{t.emoji} {t.label} ({t.mean_score:+.2f})")

    html = build_html(ranked, date_str)
    subject = subject_line(ranked, date_str)

    if args.dry_run:
        print("\n--- DRY RUN: HTML report below, not sending ---\n")
        print(html)
        return 0

    print(f"\nSending email: {subject!r}")
    send_email(html, subject)
    print("Sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
