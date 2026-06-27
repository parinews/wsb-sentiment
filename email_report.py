"""Build the HTML report and send it via Gmail SMTP."""

import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    EMAIL_TO,
    GMAIL_APP_PASSWORD,
    GMAIL_USER,
    SMTP_HOST,
    SMTP_PORT,
)
from sentiment import TickerSentiment
from tickers import company_name


def build_html(ranked: list[TickerSentiment], date_str: str) -> str:
    rows = []
    for rank, t in enumerate(ranked, start=1):
        name = company_name(t.symbol) or "—"
        rows.append(
            f"""
            <tr>
              <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;color:#888;">{rank}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:600;">{t.symbol}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #eee;color:#555;">{name}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:right;">{t.mentions}</td>
              <td style="padding:8px 12px;border-bottom:1px solid #eee;white-space:nowrap;">{t.emoji} {t.label} ({t.mean_score:+.2f})</td>
            </tr>"""
        )

    body = "".join(rows) or (
        '<tr><td colspan="5" style="padding:16px;text-align:center;color:#888;">'
        "No tickers detected in the last 24h.</td></tr>"
    )

    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:24px;background:#f6f7f9;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#222;">
  <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">
    <div style="padding:20px 24px;background:#111;color:#fff;">
      <h1 style="margin:0;font-size:18px;">🦍 WSB Daily — Most Discussed</h1>
      <div style="font-size:13px;color:#aaa;margin-top:4px;">{date_str}</div>
    </div>
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <thead>
        <tr style="text-align:left;background:#fafafa;color:#666;font-size:12px;text-transform:uppercase;letter-spacing:.04em;">
          <th style="padding:10px 12px;text-align:right;">#</th>
          <th style="padding:10px 12px;">Ticker</th>
          <th style="padding:10px 12px;">Company</th>
          <th style="padding:10px 12px;text-align:right;">Mentions</th>
          <th style="padding:10px 12px;">Sentiment</th>
        </tr>
      </thead>
      <tbody>{body}
      </tbody>
    </table>
    <div style="padding:14px 24px;font-size:11px;color:#999;border-top:1px solid #eee;">
      Ranked by comment mentions on r/wallstreetbets. Sentiment is an automated
      VADER + WSB-slang read (−1 to +1) and is directional, not advice.
    </div>
  </div>
</body>
</html>"""


def send_email(html: str, subject: str) -> None:
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "Missing GMAIL_USER / GMAIL_APP_PASSWORD. Set them in .env (local) "
            "or as GitHub Actions secrets."
        )
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText("Open in an HTML-capable client to view the report.", "plain"))
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, [EMAIL_TO], msg.as_string())


def subject_line(ranked: list[TickerSentiment], date_str: str) -> str:
    top = ", ".join(t.symbol for t in ranked[:3]) if ranked else "no tickers"
    return f"WSB Daily ({date_str}) — Top: {top}"
