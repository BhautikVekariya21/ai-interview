"""Technology news aggregation from public RSS feeds."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin
from xml.etree.ElementTree import Element

import requests
# Untrusted remote RSS/Atom feeds are parsed here — use defusedxml instead of
# the stdlib xml.etree.ElementTree.fromstring to guard against XXE and
# billion-laughs style XML entity-expansion attacks (CWE-611 / CWE-776).
from defusedxml.ElementTree import fromstring as _safe_xml_fromstring


DEFAULT_LIMIT = 30

FEEDS = [
    {"name": "Bloomberg Technology", "url": "https://feeds.bloomberg.com/technology/news.rss"},
    {"name": "Forbes Innovation", "url": "https://www.forbes.com/innovation/feed2/"},
    {"name": "CNN Technology", "url": "http://rss.cnn.com/rss/edition_technology.rss"},
    {"name": "BBC Technology", "url": "http://feeds.bbci.co.uk/news/technology/rss.xml"},
    {"name": "The Guardian Technology", "url": "https://www.theguardian.com/technology/rss"},
    {"name": "NYT Technology", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "CNBC Technology", "url": "https://www.cnbc.com/id/19854910/device/rss/rss.html"},
    {"name": "Wall Street Journal Tech", "url": "https://feeds.a.dj.com/rss/RSSWSJD.xml"},
    {"name": "Financial Times Technology", "url": "https://www.ft.com/technology?format=rss"},
    {"name": "France 24", "url": "https://www.france24.com/en/rss"},
    {"name": "Moneycontrol Business", "url": "https://www.moneycontrol.com/rss/business.xml"},
    # AI labs & major tech companies (official blogs + focused coverage).
    # Anthropic, xAI, Meta AI, Apple and Moonshot/Kimi don't expose a usable
    # public RSS feed, so their news is covered via the AI-focused feeds below.
    {"name": "OpenAI", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/"},
    {"name": "Google DeepMind", "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "Android", "url": "https://blog.google/products/android/rss/"},
    {"name": "NVIDIA", "url": "https://blogs.nvidia.com/feed/"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "Ars Technica AI", "url": "https://arstechnica.com/ai/feed/"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/"},
    {"name": "9to5Google", "url": "https://9to5google.com/feed/"},
]

CATEGORY_RULES = {
    "hiring": ["hiring", "recruiting", "jobs", "talent", "engineer hiring"],
    "layoffs": ["layoff", "layoffs", "job cuts", "workforce", "fired", "redundancies"],
    "innovation": ["innovation", "launch", "product", "breakthrough", "startup", "technology", "chip", "robot"],
    "ai": ["ai", "artificial intelligence", "openai", "anthropic", "llm", "gpt", "model", "agentic"],
    "elon": ["elon musk", "x.ai", "tesla", "spacex", "x ", "twitter"],
}

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80",  # circuit board
    "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1200&q=80",  # cybersecurity
    "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80",  # matrix code
    "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1200&q=80",  # robot
    "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=1200&q=80",  # laptop dark
    "https://images.unsplash.com/photo-1517430816045-df4b7de11d1d?auto=format&fit=crop&w=1200&q=80",  # workstation
    "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80",  # office code
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",  # earth network
    "https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=1200&q=80",  # team laptops
    "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1200&q=80",  # server racks
]
FALLBACK_IMAGE = FALLBACK_IMAGES[0]


def _fallback_image_for(item: Dict[str, Any], index: int) -> str:
    """Deterministically vary the fallback so adjacent cards don't repeat one image."""
    seed = f"{item.get('link') or item.get('title') or ''}{index}"
    return FALLBACK_IMAGES[sum(ord(ch) for ch in seed) % len(FALLBACK_IMAGES)]


def _strip_html(value: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", value or "", flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def _first_image_from_html(value: str) -> Optional[str]:
    if not value:
        return None
    meta_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', value, flags=re.IGNORECASE)
    if meta_match:
        return meta_match.group(1)
    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)', value, flags=re.IGNORECASE)
    if img_match:
        return img_match.group(1)
    return None


def _node_text(node: Optional[Element]) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


def _parse_published(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        dt = parsedate_to_datetime(value)
        return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)


def _classify_news(text: str) -> str:
    lower = text.lower()
    best_category = "innovation"
    best_score = 0
    for category, keywords in CATEGORY_RULES.items():
        score = sum(1 for keyword in keywords if keyword in lower)
        if score > best_score:
            best_score = score
            best_category = category
    return best_category


def _extract_image(item: Element, channel_link: str = "") -> Optional[str]:
    namespaces = {
        "media": "http://search.yahoo.com/mrss/",
        "content": "http://purl.org/rss/1.0/modules/content/",
    }
    media_content = item.find("media:content", namespaces)
    if media_content is not None and media_content.attrib.get("url"):
        return media_content.attrib["url"]

    media_thumbnail = item.find("media:thumbnail", namespaces)
    if media_thumbnail is not None and media_thumbnail.attrib.get("url"):
        return media_thumbnail.attrib["url"]

    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.attrib.get("url"):
        return enclosure.attrib["url"]

    encoded = item.find("content:encoded", namespaces)
    encoded_image = _first_image_from_html(_node_text(encoded))
    if encoded_image:
        return encoded_image

    description_image = _first_image_from_html(_node_text(item.find("description")))
    if description_image:
        return description_image

    return None


def _fetch_feed(feed: Dict[str, str]) -> List[Dict[str, Any]]:
    response = requests.get(feed["url"], timeout=8, headers={"User-Agent": "ai-interview-news/1.0"})
    response.raise_for_status()

    root = _safe_xml_fromstring(response.content)
    channel_link = _node_text(root.find("./channel/link"))
    items = root.findall(".//item")
    parsed: List[Dict[str, Any]] = []

    for item in items[:12]:
        title = _strip_html(_node_text(item.find("title")))
        link = _node_text(item.find("link"))
        if not title or not link:
            continue
        summary_html = _node_text(item.find("description"))
        summary = _strip_html(summary_html)
        published = _parse_published(_node_text(item.find("pubDate")) or _node_text(item.find("published")))
        category = _classify_news(f"{title} {summary}")
        parsed.append(
            {
                "id": re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80],
                "title": title,
                "summary": summary[:260] + ("..." if len(summary) > 260 else ""),
                "link": urljoin(channel_link, link),
                "image_url": _extract_image(item, channel_link),
                "source": feed["name"],
                "courtesy": f"Courtesy: Original reporting by {feed['name']}",
                "published_at": published.isoformat(),
                "published_label": published.strftime("%b %d, %Y"),
                "category": category,
            }
        )
    return parsed


def _enrich_images(items: List[Dict[str, Any]], limit: int = 20) -> None:
    """Fetch og:image for stories whose feed had no image, in parallel.

    Fetches are capped at `limit` and share a short timeout so a slow origin
    can't stall the whole news response.
    """
    pending = [item for item in items if not item.get("image_url")][:limit]
    if not pending:
        return

    def fetch_one(item: Dict[str, Any]) -> None:
        try:
            response = requests.get(item["link"], timeout=4, headers={"User-Agent": "ai-interview-news/1.0"})
            response.raise_for_status()
            image_url = _first_image_from_html(response.text)
            if image_url:
                item["image_url"] = image_url
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=8) as pool:
        pool.map(fetch_one, pending)


def _interleave_by_source(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Round-robin across sources so high-volume wires don't crowd out AI-lab
    and single-company blogs, which post less often. Each source's stories stay
    in newest-first order; we take one per source per pass until we hit `limit`.
    """
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:  # items arrive newest-first, preserving per-source order
        buckets.setdefault(item["source"], []).append(item)

    result: List[Dict[str, Any]] = []
    while len(result) < limit and any(buckets.values()):
        for source in list(buckets.keys()):
            queue = buckets[source]
            if queue:
                result.append(queue.pop(0))
                if len(result) >= limit:
                    break
    return result


def fetch_technology_news(category: Optional[str] = None, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for feed in FEEDS:
        try:
            items.extend(_fetch_feed(feed))
        except Exception:
            continue

    seen: set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for item in sorted(items, key=lambda news: news["published_at"], reverse=True):
        key = item["link"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    if category and category in CATEGORY_RULES:
        filtered = [item for item in deduped if item["category"] == category]
    else:
        filtered = deduped

    if not filtered:
        filtered = deduped

    filtered = _interleave_by_source(filtered, limit)
    _enrich_images(filtered)

    for index, item in enumerate(filtered):
        if not item.get("image_url"):
            item["image_url"] = _fallback_image_for(item, index)

    return {
        "success": True,
        "category": category or "all",
        "categories": ["all", "hiring", "layoffs", "innovation", "ai", "elon"],
        "items": filtered,
        "sources": [feed["name"] for feed in FEEDS],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
