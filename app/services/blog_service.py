"""Engineering, coding and career blog aggregation from public RSS feeds.

Mirrors news_service.py, but pulls long-form developer/career articles and
classifies them into the same categories the Blog page filters on:
Interview Prep, Coding, AI & Technology, Career Tips.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from xml.etree.ElementTree import Element

import requests
# Untrusted remote RSS/Atom feeds are parsed here — use defusedxml instead of
# the stdlib xml.etree.ElementTree.fromstring to guard against XXE and
# billion-laughs style XML entity-expansion attacks (CWE-611 / CWE-776).
from defusedxml.ElementTree import fromstring as _safe_xml_fromstring


DEFAULT_LIMIT = 30

# Public developer / career / interview blogs with stable RSS feeds. The
# category hint biases classification when an article's text is ambiguous.
FEEDS = [
    {"name": "freeCodeCamp", "url": "https://www.freecodecamp.org/news/rss/", "hint": "Coding"},
    {"name": "dev.to", "url": "https://dev.to/feed", "hint": "Coding"},
    {"name": "The GitHub Blog", "url": "https://github.blog/feed/", "hint": "Coding"},
    {"name": "Stack Overflow Blog", "url": "https://stackoverflow.blog/feed/", "hint": "Coding"},
    {"name": "Martin Fowler", "url": "https://martinfowler.com/feed.atom", "hint": "Coding"},
    {"name": "Google Developers", "url": "https://developers.googleblog.com/feeds/posts/default", "hint": "Coding"},
    {"name": "Netflix Tech Blog", "url": "https://netflixtechblog.com/feed", "hint": "Coding"},
    {"name": "LeetCode Discuss", "url": "https://leetcode.com/discuss/rss", "hint": "Interview Prep"},
    {"name": "Interviewing.io Blog", "url": "https://interviewing.io/blog/rss.xml", "hint": "Interview Prep"},
    {"name": "Pragmatic Engineer", "url": "https://blog.pragmaticengineer.com/rss/", "hint": "Career Tips"},
    {"name": "High Growth Engineer", "url": "https://careercutler.substack.com/feed", "hint": "Career Tips"},
    {"name": "OpenAI", "url": "https://openai.com/blog/rss.xml", "hint": "AI & Technology"},
    {"name": "Google AI", "url": "https://blog.google/technology/ai/rss/", "hint": "AI & Technology"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "hint": "AI & Technology"},
    {"name": "Hugging Face", "url": "https://huggingface.co/blog/feed.xml", "hint": "AI & Technology"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "hint": "AI & Technology"},
]

# The Blog page's category pills. Classification maps every article to one of
# these; unmatched articles fall back to the feed's own hint.
CATEGORY_RULES = {
    "Interview Prep": [
        "interview", "hiring loop", "onsite", "phone screen", "whiteboard",
        "system design interview", "behavioral", "mock interview", "offer",
    ],
    "Coding": [
        "algorithm", "data structure", "leetcode", "coding", "javascript",
        "python", "typescript", "rust", "golang", "react", "refactor",
        "debugging", "clean code", "big-o", "complexity", "compiler", "api",
    ],
    "AI & Technology": [
        "ai", "artificial intelligence", "llm", "gpt", "machine learning",
        "model", "neural", "rag", "agent", "openai", "anthropic", "transformer",
    ],
    "Career Tips": [
        "career", "salary", "negotiation", "promotion", "senior engineer",
        "resume", "portfolio", "networking", "referral", "mentorship", "growth",
    ],
}

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1531403009284-440f080d1e12?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1586281380349-632531db7ed4?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=800&q=80",
]


def _fallback_image_for(item: Dict[str, Any], index: int) -> str:
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


def _classify(text: str, hint: str) -> str:
    lower = text.lower()
    best_category = ""
    best_score = 0
    for category, keywords in CATEGORY_RULES.items():
        score = sum(1 for keyword in keywords if keyword in lower)
        if score > best_score:
            best_score = score
            best_category = category
    return best_category or hint


def _estimate_read_time(text: str) -> str:
    words = len((text or "").split())
    mins = max(1, round(words / 200))
    return f"{mins} min read"


def _extract_image(item: Element) -> Optional[str]:
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


def _atom_link(item: Element) -> str:
    """Atom feeds put the URL in <link href="...">, RSS in <link>text</link>."""
    link_text = _node_text(item.find("link"))
    if link_text:
        return link_text
    for link in item.findall("{http://www.w3.org/2005/Atom}link"):
        rel = link.attrib.get("rel", "alternate")
        if rel == "alternate" and link.attrib.get("href"):
            return link.attrib["href"]
    first = item.find("{http://www.w3.org/2005/Atom}link")
    if first is not None and first.attrib.get("href"):
        return first.attrib["href"]
    return ""


def _fetch_feed(feed: Dict[str, str]) -> List[Dict[str, Any]]:
    response = requests.get(feed["url"], timeout=6, headers={"User-Agent": "ai-interview-blog/1.0"})
    response.raise_for_status()

    root = _safe_xml_fromstring(response.content)
    channel_link = _node_text(root.find("./channel/link"))
    # RSS uses <item>; Atom uses <entry>.
    items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
    parsed: List[Dict[str, Any]] = []

    for item in items[:20]:
        title = _strip_html(_node_text(item.find("title")) or _node_text(item.find("{http://www.w3.org/2005/Atom}title")))
        link = _atom_link(item)
        if not title or not link:
            continue
        summary_html = (
            _node_text(item.find("description"))
            or _node_text(item.find("{http://www.w3.org/2005/Atom}summary"))
            or _node_text(item.find("{http://www.w3.org/2005/Atom}content"))
        )
        summary = _strip_html(summary_html)
        published = _parse_published(
            _node_text(item.find("pubDate"))
            or _node_text(item.find("published"))
            or _node_text(item.find("{http://www.w3.org/2005/Atom}updated"))
        )
        category = _classify(f"{title} {summary}", feed.get("hint", "Coding"))
        parsed.append(
            {
                "id": re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:80],
                "title": title,
                "excerpt": summary[:220] + ("..." if len(summary) > 220 else ""),
                "link": urljoin(channel_link, link),
                "image_url": _extract_image(item),
                "source": feed["name"],
                "courtesy": f"Courtesy: {feed['name']}",
                "read_time": _estimate_read_time(summary),
                "published_at": published.isoformat(),
                "published_label": published.strftime("%b %d, %Y"),
                "category": category,
            }
        )
    return parsed


def _enrich_images(items: List[Dict[str, Any]], limit: int = 16) -> None:
    pending = [item for item in items if not item.get("image_url")][:limit]
    if not pending:
        return

    def fetch_one(item: Dict[str, Any]) -> None:
        try:
            response = requests.get(item["link"], timeout=4, headers={"User-Agent": "ai-interview-blog/1.0"})
            response.raise_for_status()
            image_url = _first_image_from_html(response.text)
            if image_url:
                item["image_url"] = image_url
        except Exception:
            pass

    with ThreadPoolExecutor(max_workers=8) as pool:
        pool.map(fetch_one, pending)


def _interleave_by_source(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
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


def fetch_blog_feed(category: Optional[str] = None, limit: int = DEFAULT_LIMIT) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []

    def fetch_safe(feed: Dict[str, str]) -> List[Dict[str, Any]]:
        try:
            return _fetch_feed(feed)
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=min(16, len(FEEDS))) as pool:
        for parsed in pool.map(fetch_safe, FEEDS):
            items.extend(parsed)

    seen: set[str] = set()
    deduped: List[Dict[str, Any]] = []
    for item in sorted(items, key=lambda post: post["published_at"], reverse=True):
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
        "categories": ["all", *CATEGORY_RULES.keys()],
        "items": filtered,
        "sources": [feed["name"] for feed in FEEDS],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
