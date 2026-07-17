"""ATS (Applicant Tracking System) scoring for parsed resumes.

Produces a 0-100 readiness score with sub-scores and actionable suggestions,
approximating how a keyword-driven ATS plus a human screener would rate a resume.
Works with or without a job description: JD input drives keyword matching, and
structure/quality/impact sub-scores are always computed from the parsed resume.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.schemas.schemas import ParsedResume


# Common ATS-unfriendly signals and generic filler to penalize lightly.
_STOPWORDS = {
    "the", "and", "for", "with", "you", "your", "our", "are", "will", "have",
    "this", "that", "from", "they", "their", "who", "what", "when", "which",
    "a", "an", "to", "of", "in", "on", "at", "as", "is", "be", "or", "we",
    "role", "team", "work", "years", "experience", "ability", "strong", "good",
    "plus", "etc", "job", "candidate", "responsibilities", "requirements",
    "looking", "seeking", "engineer", "developer", "including", "using",
    "knowledge", "understanding", "excellent", "proficient", "familiar",
    "must", "should", "preferred", "required", "help", "build", "join",
}

_ACTION_VERBS = {
    "built", "designed", "led", "shipped", "launched", "improved", "reduced",
    "increased", "optimized", "migrated", "automated", "architected", "scaled",
    "developed", "implemented", "delivered", "created", "drove", "owned",
}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _label(score: float) -> str:
    if score >= 80:
        return "excellent"
    if score >= 65:
        return "good"
    if score >= 45:
        return "fair"
    return "needs_work"


def _keywords(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}", (text or "").lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


def _resume_terms(resume: ParsedResume, raw_text: str) -> set[str]:
    terms: set[str] = set(_keywords(raw_text))
    for skill in resume.skills:
        terms.update(_keywords(skill.name))
    for skill in resume.top_skills:
        terms.update(_keywords(skill))
    return terms


def _keyword_match(resume: ParsedResume, raw_text: str, job_description: str) -> Dict[str, Any]:
    """Match JD keywords against the resume. Returns sub-score 0-100 + gaps."""
    jd_terms = [t for t in dict.fromkeys(_keywords(job_description))]  # dedupe, keep order
    if not jd_terms:
        return {"score": None, "matched": [], "missing": [], "coverage": None}

    resume_terms = _resume_terms(resume, raw_text)
    matched = [t for t in jd_terms if t in resume_terms]
    missing = [t for t in jd_terms if t not in resume_terms]
    coverage = len(matched) / max(len(jd_terms), 1)
    # Reward coverage but don't require 100% — 70% overlap is already strong.
    score = _clamp((coverage / 0.7) * 100)
    return {
        "score": round(score, 1),
        "matched": matched[:25],
        "missing": missing[:15],
        "coverage": round(coverage, 3),
    }


def _structure_score(resume: ParsedResume) -> Dict[str, Any]:
    """Reward the presence of ATS-expected sections and contact channels."""
    checks: List[tuple[str, bool]] = [
        ("contact email", bool(resume.personal_info.email)),
        ("phone number", bool(resume.personal_info.phone)),
        ("professional links", bool(
            resume.personal_info.linkedin_url
            or resume.personal_info.github_url
            or resume.personal_info.portfolio_url
        )),
        ("work experience", len(resume.work_experience) > 0),
        ("skills section", len(resume.skills) >= 3),
        ("education", len(resume.education) > 0),
        ("projects or achievements", bool(resume.projects or resume.achievements)),
    ]
    passed = sum(1 for _, ok in checks if ok)
    score = _clamp(passed / len(checks) * 100)
    missing = [name for name, ok in checks if not ok]
    return {"score": round(score, 1), "missing_sections": missing}


def _impact_score(resume: ParsedResume, raw_text: str) -> Dict[str, Any]:
    """Reward quantified achievements and strong action verbs."""
    bullets: List[str] = []
    for exp in resume.work_experience:
        bullets.extend(exp.responsibilities)
        bullets.extend(exp.achievements)
    for proj in resume.projects:
        bullets.extend(proj.highlights)
    if not bullets:
        bullets = [ln.strip("-* ").strip() for ln in raw_text.splitlines() if ln.strip().startswith(("-", "*"))]

    total = max(len(bullets), 1)
    quantified = sum(1 for b in bullets if re.search(r"\d", b))
    action_led = sum(1 for b in bullets if _keywords(b) and _keywords(b)[0] in _ACTION_VERBS)

    quantified_ratio = quantified / total
    action_ratio = action_led / total
    # Metrics matter most; strong verbs are a secondary signal.
    score = _clamp(quantified_ratio * 65 + action_ratio * 35)
    return {
        "score": round(score, 1),
        "bullet_count": len(bullets),
        "quantified_bullets": quantified,
        "quantified_ratio": round(quantified_ratio, 3),
        "action_verb_ratio": round(action_ratio, 3),
    }


def _parse_quality_score(resume: ParsedResume) -> Dict[str, Any]:
    """How cleanly the resume parsed — a proxy for ATS machine-readability."""
    score = _clamp(float(resume.overall_parse_confidence) * 100)
    return {"score": round(score, 1), "warnings": list(resume.warnings)[:5]}


def _build_suggestions(
    keyword: Dict[str, Any],
    structure: Dict[str, Any],
    impact: Dict[str, Any],
    parse_quality: Dict[str, Any],
) -> List[str]:
    tips: List[str] = []
    if keyword.get("missing"):
        top_missing = ", ".join(keyword["missing"][:6])
        tips.append(f"Add job-relevant keywords the resume is missing: {top_missing}.")
    if structure.get("missing_sections"):
        tips.append(
            "Add missing sections for ATS parsing: " + ", ".join(structure["missing_sections"]) + "."
        )
    if impact.get("quantified_ratio", 0) < 0.4:
        tips.append("Quantify more bullet points with numbers (%, scale, latency, revenue, users).")
    if impact.get("action_verb_ratio", 0) < 0.4:
        tips.append("Start bullets with strong action verbs (built, led, reduced, shipped).")
    if parse_quality.get("score", 100) < 70:
        tips.append("Use a simpler single-column layout with standard headings so ATS software parses it cleanly.")
    if not tips:
        tips.append("Strong resume — keep tailoring keywords to each specific job description.")
    return tips[:6]


def compute_ats_score(
    resume: ParsedResume,
    raw_text: str = "",
    job_description: Optional[str] = None,
) -> Dict[str, Any]:
    """Return an ATS readiness report with an overall 0-100 score."""
    keyword = _keyword_match(resume, raw_text, job_description or "")
    structure = _structure_score(resume)
    impact = _impact_score(resume, raw_text)
    parse_quality = _parse_quality_score(resume)

    has_jd = keyword["score"] is not None
    if has_jd:
        # With a JD, keyword match is the dominant ATS signal.
        weights = {"keyword": 0.40, "structure": 0.20, "impact": 0.25, "parse": 0.15}
        overall = (
            keyword["score"] * weights["keyword"]
            + structure["score"] * weights["structure"]
            + impact["score"] * weights["impact"]
            + parse_quality["score"] * weights["parse"]
        )
    else:
        # Without a JD, score structure/impact/parse quality only.
        weights = {"structure": 0.35, "impact": 0.40, "parse": 0.25}
        overall = (
            structure["score"] * weights["structure"]
            + impact["score"] * weights["impact"]
            + parse_quality["score"] * weights["parse"]
        )

    overall = round(_clamp(overall), 1)

    return {
        "report_type": "ats_score",
        "score": overall,
        "label": _label(overall),
        "has_job_description": has_jd,
        "sub_scores": {
            "keyword_match": keyword["score"],
            "structure": structure["score"],
            "impact": impact["score"],
            "parse_quality": parse_quality["score"],
        },
        "keyword_match": keyword,
        "structure": structure,
        "impact": impact,
        "parse_quality": parse_quality,
        "suggestions": _build_suggestions(keyword, structure, impact, parse_quality),
        "summary": (
            f"ATS readiness {overall}/100 ({_label(overall).replace('_', ' ')})."
            + ("" if has_jd else " Add a job description to score keyword match.")
        ),
    }
