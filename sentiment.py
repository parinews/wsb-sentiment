"""Sentiment scoring: VADER tuned with the WSB slang lexicon, plus aggregation
of per-comment scores into a per-ticker label."""

from dataclasses import dataclass
from functools import lru_cache

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config import BEARISH_THRESHOLD, BULLISH_THRESHOLD
from data.wsb_lexicon import WSB_LEXICON


@lru_cache(maxsize=1)
def get_analyzer() -> SentimentIntensityAnalyzer:
    analyzer = SentimentIntensityAnalyzer()
    analyzer.lexicon.update(WSB_LEXICON)
    return analyzer


def score(text: str) -> float:
    """Compound sentiment for one piece of text, in -1..+1."""
    return get_analyzer().polarity_scores(text)["compound"]


def label_for(mean_score: float) -> tuple[str, str]:
    """Map a mean compound score to (emoji, word)."""
    if mean_score >= BULLISH_THRESHOLD:
        return "🟢", "Bullish"
    if mean_score <= BEARISH_THRESHOLD:
        return "🔴", "Bearish"
    return "⚪", "Neutral"


@dataclass
class TickerSentiment:
    symbol: str
    mentions: int
    mean_score: float

    @property
    def emoji(self) -> str:
        return label_for(self.mean_score)[0]

    @property
    def label(self) -> str:
        return label_for(self.mean_score)[1]


def aggregate(records: list[tuple[set[str], float]]) -> dict[str, TickerSentiment]:
    """Aggregate per-comment results into per-ticker sentiment.

    records: list of (tickers_in_comment, comment_compound_score).
    Each comment contributes one mention and one score to each ticker it names.
    """
    totals: dict[str, list[float]] = {}
    for tickers, compound in records:
        for sym in tickers:
            totals.setdefault(sym, []).append(compound)

    result: dict[str, TickerSentiment] = {}
    for sym, scores in totals.items():
        mean = sum(scores) / len(scores)
        result[sym] = TickerSentiment(symbol=sym, mentions=len(scores), mean_score=mean)
    return result
