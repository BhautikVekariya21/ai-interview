"""Technology news aggregation from public RSS feeds."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import requests


DEFAULT_LIMIT = 30

FEEDS = [
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Wired", "url": "https://www.wired.com/feed/rss"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/ai/feed/"},
]

CATEGORY_RULES = {
    "hiring": ["hiring", "recruiting", "jobs", "talent", "engineer hiring"],
    "layoffs": ["layoff", "layoffs", "job cuts", "workforce", "fired", "redundancies"],
    "innovation": ["innovation", "launch", "product", "breakthrough", "startup", "technology", "chip", "robot"],
    "ai": ["ai", "artificial intelligence", "openai", "anthropic", "llm", "gpt", "model", "agentic"],
    "elon": ["elon musk", "x.ai", "tesla", "spacex", "x ", "twitter"],
}

FALLBACK_IMAGE = "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80"


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


def _node_text(node: Optional[ET.Element]) -> str:
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


def _extract_image(item: ET.Element, channel_link: str = "") -> Optional[str]:
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

    root = ET.fromstring(response.content)
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


def _enrich_images(items: List[Dict[str, Any]], limit: int = 4) -> None:
    remaining = limit
    for item in items:
        if item.get("image_url"):
            continue
        if remaining <= 0:
            break
        try:
            response = requests.get(item["link"], timeout=6, headers={"User-Agent": "ai-interview-news/1.0"})
            response.raise_for_status()
            image_url = _first_image_from_html(response.text)
            if image_url:
                item["image_url"] = image_url
                remaining -= 1
        except Exception:
            continue


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

    filtered = filtered[:limit]
    _enrich_images(filtered)

    for item in filtered:
        if not item.get("image_url"):
            item["image_url"] = FALLBACK_IMAGE

    return {
        "success": True,
        "category": category or "all",
        "categories": ["all", "hiring", "layoffs", "innovation", "ai", "elon"],
        "items": filtered,
        "sources": [feed["name"] for feed in FEEDS],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
