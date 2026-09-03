"""Technology FAQ service backed by the public Stack Exchange API."""

from __future__ import annotations

import html
import re
from collections import defaultdict
from typing import Any

import requests

STACK_EXCHANGE_API = "https://api.stackexchange.com/2.3"
STACK_EXCHANGE_SITE = "stackoverflow"
FAQ_PAGE_SIZE = 8

SUPPORTED_TECHNOLOGIES = [
    {"id": "python", "label": "Python", "tag": "python", "description": "Popular Python questions and practical answers."},
    {"id": "javascript", "label": "JavaScript", "tag": "javascript", "description": "Core JS FAQs from modern frontend and backend work."},
    {"id": "typescript", "label": "TypeScript", "tag": "typescript", "description": "Typing, tooling, and TS ergonomics answers."},
    {"id": "react", "label": "React", "tag": "reactjs", "description": "React patterns, hooks, and component architecture FAQs."},
    {"id": "nodejs", "label": "Node.js", "tag": "node.js", "description": "Server-side JavaScript FAQs and runtime guidance."},
    {"id": "java", "label": "Java", "tag": "java", "description": "Java language and ecosystem FAQs."},
    {"id": "csharp", "label": "C#", "tag": "c#", "description": "C# answers covering .NET and language usage."},
    {"id": "cpp", "label": "C++", "tag": "c++", "description": "C++ language and memory/model FAQs."},
    {"id": "go", "label": "Go", "tag": "go", "description": "Go concurrency, standard library, and backend FAQs."},
    {"id": "rust", "label": "Rust", "tag": "rust", "description": "Ownership, borrowing, and idiomatic Rust FAQs."},
    {"id": "php", "label": "PHP", "tag": "php", "description": "PHP runtime and web application FAQs."},
    {"id": "swift", "label": "Swift", "tag": "swift", "description": "Swift language and iOS/macOS development FAQs."},
    {"id": "kotlin", "label": "Kotlin", "tag": "kotlin", "description": "Kotlin language and Android/server FAQs."},
    {"id": "docker", "label": "Docker", "tag": "docker", "description": "Container build and runtime FAQs."},
    {"id": "kubernetes", "label": "Kubernetes", "tag": "kubernetes", "description": "Cluster, pod, and deployment troubleshooting FAQs."},
    {"id": "fastapi", "label": "FastAPI", "tag": "fastapi", "description": "FastAPI routing, validation, and async FAQs."},
    {"id": "django", "label": "Django", "tag": "django", "description": "Django models, views, and app architecture FAQs."},
    {"id": "aws", "label": "AWS", "tag": "amazon-web-services", "description": "Cloud infrastructure and AWS service FAQs."},
]

_TECH_BY_ID = {item["id"]: item for item in SUPPORTED_TECHNOLOGIES}


def list_supported_technologies() -> list[dict[str, str]]:
    return SUPPORTED_TECHNOLOGIES


def _strip_html(value: str) -> str:
    if not value:
        return ""
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", value, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|li|pre|h[1-6])>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li>", "• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _preview(text: str, max_chars: int = 240) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "…"


def _fetch_json(path: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(f"{STACK_EXCHANGE_API}{path}", params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if "items" not in payload:
        raise RuntimeError("Unexpected FAQ API response format")
    return payload


def fetch_faq_for_technology(technology_id: str) -> dict[str, Any]:
    tech = _TECH_BY_ID.get(technology_id)
    if not tech:
        raise ValueError(f"Unsupported technology '{technology_id}'")

    faq_payload = _fetch_json(
        f"/tags/{tech['tag']}/faq",
        {
            "site": STACK_EXCHANGE_SITE,
            "pagesize": FAQ_PAGE_SIZE,
        },
    )

    questions = faq_payload.get("items", [])
    question_ids = [str(item["question_id"]) for item in questions if item.get("question_id")]

    answers_by_question: dict[int, list[dict[str, Any]]] = defaultdict(list)
    if question_ids:
        answers_payload = _fetch_json(
            f"/questions/{';'.join(question_ids)}/answers",
            {
                "site": STACK_EXCHANGE_SITE,
                "pagesize": max(20, len(question_ids) * 3),
                "order": "desc",
                "sort": "votes",
                "filter": "withbody",
            },
        )
        for item in answers_payload.get("items", []):
            answers_by_question[item["question_id"]].append(item)

    faq_items: list[dict[str, Any]] = []
    for question in questions:
        qid = question["question_id"]
        accepted_answer_id = question.get("accepted_answer_id")
        candidates = answers_by_question.get(qid, [])
        selected_answer = None
        if accepted_answer_id:
            selected_answer = next((ans for ans in candidates if ans.get("answer_id") == accepted_answer_id), None)
        if selected_answer is None and candidates:
            selected_answer = candidates[0]

        answer_text = _strip_html(selected_answer.get("body", "")) if selected_answer else ""
        faq_items.append(
            {
                "question_id": qid,
                "question": html.unescape(question.get("title", "")),
                "link": question.get("link", ""),
                "score": question.get("score", 0),
                "answer_count": question.get("answer_count", 0),
                "tags": question.get("tags", []),
                "answer": {
                    "answer_id": selected_answer.get("answer_id") if selected_answer else None,
                    "score": selected_answer.get("score", 0) if selected_answer else 0,
                    "is_accepted": bool(selected_answer.get("is_accepted")) if selected_answer else False,
                    "body_text": answer_text,
                    "preview": _preview(answer_text) if answer_text else "No answer summary available yet.",
                },
            }
        )

    faq_items.sort(key=lambda item: item.get("score", 0), reverse=True)

    return {
        "technology": {
            "id": tech["id"],
            "label": tech["label"],
            "tag": tech["tag"],
            "description": tech["description"],
        },
        "source": {
            "name": "Stack Exchange API",
            "site": STACK_EXCHANGE_SITE,
            "docs": "https://api.stackexchange.com/docs",
        },
        "items": faq_items,
    }
