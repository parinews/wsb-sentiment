"""Read-only Reddit fetching via PRAW: pull recent hot posts and their comments."""

import time

import praw

from config import (
    COMMENT_EXPANSION_LIMIT,
    MAX_COMMENTS_PER_POST,
    POST_LIMIT,
    POST_MAX_AGE_HOURS,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    SUBREDDIT,
)


def _client() -> praw.Reddit:
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise RuntimeError(
            "Missing REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET. Set them in .env "
            "(local) or as GitHub Actions secrets."
        )
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
        check_for_async=False,
    )
    reddit.read_only = True
    return reddit


def fetch_texts(verbose: bool = True) -> list[str]:
    """Return a list of text blobs (post titles+bodies and comments) from the
    last POST_MAX_AGE_HOURS, drawn from the top POST_LIMIT hot posts.

    Comment scanning is the core signal; the post's own title+selftext is also
    included since tickers frequently appear there (e.g. "YOLO $TSLA calls").
    """
    reddit = _client()
    subreddit = reddit.subreddit(SUBREDDIT)
    cutoff = time.time() - POST_MAX_AGE_HOURS * 3600

    texts: list[str] = []
    posts_scanned = 0

    for post in subreddit.hot(limit=POST_LIMIT):
        if post.stickied or post.created_utc < cutoff:
            continue
        posts_scanned += 1

        header = post.title or ""
        if getattr(post, "selftext", ""):
            header += "\n" + post.selftext
        texts.append(header)

        # Expand comment tree up to a cap, then take at most N comments.
        post.comments.replace_more(limit=COMMENT_EXPANSION_LIMIT)
        count = 0
        for comment in post.comments.list():
            body = getattr(comment, "body", None)
            if not body or body in ("[deleted]", "[removed]"):
                continue
            texts.append(body)
            count += 1
            if count >= MAX_COMMENTS_PER_POST:
                break

        if verbose:
            print(f"  post {posts_scanned}: {count} comments  ({post.title[:60]!r})")

    if verbose:
        print(f"Scanned {posts_scanned} posts, {len(texts)} total text items.")
    return texts
