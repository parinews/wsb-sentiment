# WSB Daily Sentiment Email

A daily email of the stocks most discussed on r/wallstreetbets, each with a
bullish / neutral / bearish sentiment indicator. Runs free on GitHub Actions.

## How it works

1. **Fetch** the top 100 hot posts from r/wallstreetbets (last 24h) and up to 500
   comments per post, via Reddit's official API (read-only).
2. **Detect tickers** in every comment/post, matching against the full Nasdaq/NYSE
   symbol list and rejecting common-word/slang false positives (YOLO, DD, CEO…).
3. **Rank** the top 10 tickers by mention count.
4. **Score sentiment** with VADER plus a custom WSB slang lexicon; average each
   ticker's comment scores into 🟢 Bullish / ⚪ Neutral / 🔴 Bearish.
5. **Email** an HTML table to you at 8:30 AM ET daily.

## One-time setup

### 1. Reddit API credentials (free)
1. Create a throwaway Reddit account (no personal info needed).
2. Go to <https://www.reddit.com/prefs/apps> → **create another app…**
3. Choose type **script**, set redirect URI to `http://localhost:8080`, save.
4. Copy the **client ID** (under the app name) and **client secret**.

### 2. Gmail App Password (free)
1. Enable 2-Step Verification on the Gmail account.
2. Go to <https://myaccount.google.com/apppasswords> and create an app password.
3. Use that 16-character value (not your normal password).

### 3. Build the ticker list
```bash
cd "WSB Sentiment"
pip install -r requirements.txt
python data/refresh_tickers.py      # writes data/tickers.csv (commit this file)
```

### 4. GitHub repository secrets
Add these under **Settings → Secrets and variables → Actions**:

| Secret | Value |
| --- | --- |
| `REDDIT_CLIENT_ID` | from step 1 |
| `REDDIT_CLIENT_SECRET` | from step 1 |
| `REDDIT_USER_AGENT` | any string, e.g. `wsb-sentiment-email by u/yourname` |
| `GMAIL_USER` | your-gmail@gmail.com |
| `GMAIL_APP_PASSWORD` | from step 2 |
| `EMAIL_TO` | where to send (defaults to `GMAIL_USER`) |

## Local testing

```bash
cd "WSB Sentiment"
cp .env.example .env      # fill in your values
python main.py --dry-run  # fetch + build, print HTML, do NOT send
python main.py            # actually send the email
```

## Scheduling

`.github/workflows/wsb_email.yml` (at the repository root's `.github/workflows/`)
runs on cron at the two UTC times that map to 8:30 AM ET, and a gate step lets
exactly one through per day based on the current Eastern offset — so it stays at
8:30 ET across daylight-saving changes. Use **Actions → WSB Daily Sentiment Email
→ Run workflow** to trigger a manual end-to-end test (the manual run bypasses the
time gate).

## Tuning

- Scan breadth/depth, ranking size, sentiment thresholds: `config.py`
- WSB slang sentiment weights: `data/wsb_lexicon.py`
- Ticker false-positive blacklist: `tickers.py` (`BLACKLIST`)
