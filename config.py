"""Central configuration: tunable constants and environment loading."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TICKERS_FILE = DATA_DIR / "tickers.csv"

# --- Scan breadth / depth ---------------------------------------------------
SUBREDDIT = "wallstreetbets"
POST_LIMIT = 100               # top N hot posts to consider
POST_MAX_AGE_HOURS = 24        # only posts created within this window
MAX_COMMENTS_PER_POST = 500    # cap comments scanned per post
# Each MoreComments expansion is an API call; this caps how many we make per
# post so a megathread can't blow the request budget.
COMMENT_EXPANSION_LIMIT = 32

# --- Ranking ----------------------------------------------------------------
TOP_N = 10                     # tickers shown in the email

# --- Sentiment thresholds (mean VADER compound, -1..+1) ---------------------
BULLISH_THRESHOLD = 0.15
BEARISH_THRESHOLD = -0.15

# --- Email ------------------------------------------------------------------
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465                # SSL


def _load_dotenv() -> None:
    """Minimal .env loader for local runs (no external dependency).

    Lines like KEY=VALUE are read into os.environ if not already set.
    Silently does nothing if .env is absent (e.g. in CI).
    """
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


def get_env(name: str, default: str | None = None, required: bool = False) -> str | None:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it in .env (local) or as a GitHub Actions secret."
        )
    return value


# Resolved once at import time.
REDDIT_CLIENT_ID = get_env("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = get_env("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = get_env("REDDIT_USER_AGENT", "wsb-sentiment-email/1.0")

GMAIL_USER = get_env("GMAIL_USER")
GMAIL_APP_PASSWORD = get_env("GMAIL_APP_PASSWORD")
EMAIL_TO = get_env("EMAIL_TO") or GMAIL_USER
