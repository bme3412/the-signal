"""Host reputation scoring for Discover + curated episode links."""

from __future__ import annotations

from urllib.parse import urlparse

# Major wires, papers of record, top business/tech/science outlets.
_TIER1 = frozenset({
    "reuters.com",
    "apnews.com",
    "bloomberg.com",
    "ft.com",
    "wsj.com",
    "nytimes.com",
    "economist.com",
    "washingtonpost.com",
    "bbc.com",
    "bbc.co.uk",
    "theguardian.com",
    "nature.com",
    "science.org",
    "scientificamerican.com",
    "nih.gov",
    "who.int",
    "sec.gov",
    "federalreserve.gov",
})

# Strong specialty / trade press — still prefer over random web.
_TIER2 = frozenset({
    "axios.com",
    "cnbc.com",
    "forbes.com",
    "fortune.com",
    "businessinsider.com",
    "techcrunch.com",
    "theverge.com",
    "wired.com",
    "arstechnica.com",
    "mit.edu",
    "technologyreview.com",
    "spectrum.ieee.org",
    "ieee.org",
    "semafor.com",
    "politico.com",
    "theatlantic.com",
    "newyorker.com",
    "time.com",
    "npr.org",
    "pbs.org",
    "aljazeera.com",
    "scmp.com",
    "nikkei.com",
    "asia.nikkei.com",
    "restofworld.org",
    "protocol.com",
    "theinformation.com",
    "stratechery.com",
    "latent.space",
    "huggingface.co",
    "openai.com",
    "anthropic.com",
    "deepmind.google",
    "blog.google",
    "microsoft.com",
    "nvidia.com",
})

# Soft-prefer academic / government TLDs and known publisher patterns.
_TIER2_SUFFIXES = (
    ".edu",
    ".gov",
    ".ac.uk",
)

_SKIP_HOSTS = (
    "pinterest.",
    "facebook.com",
    "fb.com",
    "twitter.com",
    "x.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com",
    "youtu.be",
    "reddit.com",
    "quora.com",
    "medium.com",
    "substack.com",  # mixed; prefer named outlets above
    "blogspot.",
    "wordpress.com",
    "tumblr.com",
    "msn.com",
    "yahoo.com",
    "news.yahoo.com",
    "flipboard.com",
    "pocket.com",
    "apple.news",
    "google.com",
    "news.google.com",
    "bing.com",
    "duckduckgo.com",
    "wikipedia.org",
    "wiki/",
    "britannica.com",
    "fandom.com",
    "linkedin.com",
    "scribd.com",
    "slideshare.net",
    "prnewswire.com",
    "businesswire.com",
    "globenewswire.com",
    "einpresswire.com",
)

# Used when a first pass finds nothing reputable — bias the query.
PREFERRED_SITE_QUERY = (
    "site:reuters.com OR site:apnews.com OR site:bloomberg.com OR "
    "site:ft.com OR site:wsj.com OR site:nytimes.com OR site:economist.com OR "
    "site:bbc.com OR site:theguardian.com OR site:axios.com OR site:cnbc.com OR "
    "site:techcrunch.com OR site:theverge.com OR site:wired.com OR "
    "site:arstechnica.com OR site:nature.com OR site:semafor.com"
)


def host_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "").lower()
    except Exception:
        return ""


def _matches_host(host: str, candidates: frozenset[str]) -> bool:
    if host in candidates:
        return True
    return any(host.endswith("." + c) for c in candidates)


def reputation_score(url: str) -> int:
    """Higher = more trustworthy outlet. Negative = skip."""
    host = host_from_url(url)
    url_l = (url or "").lower()
    if not host:
        return -3
    if any(skip in host or skip in url_l for skip in _SKIP_HOSTS):
        return -8
    if _matches_host(host, _TIER1):
        return 12
    if _matches_host(host, _TIER2):
        return 8
    if host.endswith(_TIER2_SUFFIXES):
        return 7
    # Unknown but looks like a real publisher path (not a bare homepage dump).
    path = urlparse(url).path or ""
    if path.count("/") >= 2 and len(path) > 12:
        return 1
    return 0


def is_reputable(url: str, *, min_score: int = 7) -> bool:
    return reputation_score(url) >= min_score


def rank_results(results: list[dict], label: str = "") -> list[dict]:
    """Sort search hits: reputation first, then label relevance."""
    lab = label.lower().strip()

    def key(item: dict) -> tuple:
        url = item.get("url") or ""
        title = (item.get("title") or "").lower()
        desc = (item.get("description") or "").lower()
        rep = reputation_score(url)
        relevance = 0
        if lab:
            if lab in title:
                relevance += 4
            if lab in desc:
                relevance += 2
            if lab.replace(" ", "") in url.lower().replace("-", "").replace("_", ""):
                relevance += 1
        return (rep, relevance)

    return sorted(results, key=key, reverse=True)
