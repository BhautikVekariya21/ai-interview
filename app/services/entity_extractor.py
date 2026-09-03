"""
Entity extraction: NER + regex + heuristics.
FIX: Label mismatch (NER PERSON → NAME), robust name fallback.
"""
import re
from typing import List, Dict, Optional
from loguru import logger

from app.services.ner_engine import NEREngine
from app.services.skill_normalizer import SkillNormalizer


class EntityExtractor:
    """Hybrid entity extraction: NER + regex + heuristics."""

    # ===== FIX: Map ALL possible NER labels to internal labels =====
    LABEL_MAP = {
        # Name variants
        "PERSON": "NAME",
        "NAME": "NAME",
        "PER": "NAME",
        # Organization variants
        "ORG": "ORG",
        "ORGANIZATION": "ORG",
        "INSTITUTION": "ORG",
        "COMPANY": "ORG",
        # Job title variants
        "JOBTITLE": "ROLE",
        "JOB_TITLE": "ROLE",
        "ROLE": "ROLE",
        "TITLE": "ROLE",
        # Skill variants
        "SKILL": "SKILL",
        "TECH": "SKILL",
        "TECHNOLOGY": "SKILL",
        # Contact variants
        "EMAIL": "EMAIL",
        "PHONE": "PHONE",
        # Location variants
        "LOCATION": "LOCATION",
        "LOC": "LOCATION",
        "GPE": "LOCATION",
        "GEO": "LOCATION",
        # Date variants
        "DATE": "DATE",
        "DURATION": "DATE",
        "TIME": "DATE",
        # Education variants
        "DEGREE": "DEGREE",
        "FIELD": "FIELD",
        "GPA": "GPA",
        # Other
        "PROJECT": "PROJECT",
        "CERT": "CERT",
        "CERTIFICATION": "CERT",
        "ACHIEVEMENT": "ACHIEVEMENT",
        "AWARD": "ACHIEVEMENT",
    }

    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    )
    PHONE_PATTERNS = [
        re.compile(r'\+?\d{1,3}[\s\-.]?\(?\d{2,4}\)?[\s\-.]?\d{3,4}[\s\-.]?\d{3,4}'),
        re.compile(r'\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}'),
        re.compile(r'\+\d{1,3}\s?\d{10}'),
    ]
    URL_PATTERNS = {
        "linkedin": re.compile(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+/?', re.I),
        "github": re.compile(r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?', re.I),
        "portfolio": re.compile(
            r'(?:https?://)?(?:www\.)?[\w\-]+\.(?:com|io|dev|me|net|org)/?\S*', re.I
        ),
    }
    DATE_PATTERNS = [
        re.compile(
            r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
            r'Dec(?:ember)?)\s*\.?\s*\d{4}\b', re.I
        ),
        re.compile(
            r'\b(?:'
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}'
            r'|\d{1,2}/\d{4}'
            r'|\d{4}'
            r')\s*(?:-|–|—|to)\s*(?:'
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}'
            r'|\d{1,2}/\d{4}'
            r'|\d{4}|Present|Current|Now'
            r')\b', re.I
        ),
        re.compile(r'\b\d{1,2}/\d{4}\b'),
        re.compile(r'\b(20\d{2}|19\d{2})\b'),
    ]
    GPA_PATTERN = re.compile(
        r'(?:GPA|CGPA|Grade|Score)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:/\s*(\d+\.?\d*))?', re.I
    )
    DEGREE_PATTERNS = re.compile(
        r'\b(?:B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|Ph\.?D\.?|'
        r'B\.?Tech\.?|M\.?Tech\.?|B\.?E\.?|M\.?E\.?|MBA|BCA|MCA|'
        r'Bachelor(?:\'?s)?|Master(?:\'?s)?|Doctorate|'
        r'Associate(?:\'?s)?|Diploma)\b'
        r'(?:\s+(?:of|in)\s+[\w\s]+)?', re.I
    )
    INSTITUTION_HINTS = re.compile(
        r'\b(university|college|institute|school|academy|polytechnic)\b',
        re.I,
    )
    EXPERIENCE_HEADER_PATTERNS = [
        re.compile(
            r'^(?P<role>[^|,@]{2,80})\s+(?:at|@)\s+(?P<company>[^|,]{2,80})\s*(?:[|,-]\s*(?P<date>.+))?$',
            re.I,
        ),
        re.compile(
            r'^(?P<role>[^|,]{2,80})\s*[|,-]\s*(?P<company>[^|,]{2,80})\s*[|,-]\s*(?P<date>.+)$',
            re.I,
        ),
    ]

    def __init__(self, ner_engine: NEREngine, skill_normalizer: SkillNormalizer):
        self.ner_engine = ner_engine
        self.skill_normalizer = skill_normalizer
        logger.info("EntityExtractor initialized")

    def _normalize_label(self, label: str) -> str:
        """Map any NER label to our internal label."""
        return self.LABEL_MAP.get(label, label)

    def extract_all(
        self, cleaned_text: str, lines: List[str],
        tokens: List[List[str]], sections: List[Dict],
    ) -> Dict:
        logger.info("Starting full entity extraction...")

        # NER predictions
        ner_entities = self.ner_engine.predict(lines, tokens)
        # Normalize ALL labels immediately
        for ent in ner_entities:
            ent["label"] = self._normalize_label(ent["label"])
        logger.info(f"NER found {len(ner_entities)} entities")

        # Regex extraction
        regex_results = self._extract_regex_entities(cleaned_text)
        regex_count = sum(
            len(v) if isinstance(v, list) else (1 if v else 0)
            for v in regex_results.values()
        )
        logger.info(f"Regex found: {regex_count} entities")

        # Section-aware extraction
        section_results = self._extract_from_sections(sections)

        # Merge all sources
        merged = self._merge_extractions(
            ner_entities, regex_results, section_results, cleaned_text
        )
        return merged

    def _extract_regex_entities(self, text: str) -> Dict:
        results = {"emails": [], "phones": [], "urls": {}, "dates": [], "gpas": [], "degrees": []}
        for m in self.EMAIL_PATTERN.finditer(text):
            results["emails"].append({"value": m.group(), "confidence": 0.95})
        for pat in self.PHONE_PATTERNS:
            for m in pat.finditer(text):
                phone = m.group().strip()
                digits = re.sub(r'\D', '', phone)
                if 7 <= len(digits) <= 15:
                    results["phones"].append({"value": phone, "confidence": 0.9})
        for url_type, pat in self.URL_PATTERNS.items():
            m = pat.search(text)
            if m:
                results["urls"][url_type] = {"value": m.group(), "confidence": 0.95}
        for pat in self.DATE_PATTERNS:
            for m in pat.finditer(text):
                results["dates"].append({"value": m.group(), "confidence": 0.85})
        for m in self.GPA_PATTERN.finditer(text):
            val = float(m.group(1))
            scale = float(m.group(2)) if m.group(2) else (4.0 if val <= 4.0 else 10.0)
            results["gpas"].append({"value": val, "scale": scale})
        for m in self.DEGREE_PATTERNS.finditer(text):
            results["degrees"].append({"value": m.group().strip()})
        return results

    def _extract_from_sections(self, sections: List[Dict]) -> Dict:
        results = {
            "personal_info": {}, "education": [], "experience": [],
            "skills": [], "projects": [], "certifications": [],
            "publications": [], "achievements": [],
        }
        for section in sections:
            sec_type = section["type"]
            content = section["content_lines"]
            if sec_type in ("personal", "summary"):
                results["personal_info"]["summary"] = " ".join(content[:5])
            elif sec_type == "education":
                results["education"].extend(self._parse_education_section(content))
            elif sec_type == "experience":
                results["experience"].extend(self._parse_experience_section(content))
            elif sec_type == "skills":
                results["skills"].extend(self._parse_skills_section(content))
            elif sec_type == "projects":
                results["projects"].extend(self._parse_projects_section(content))
            elif sec_type == "certifications":
                results["certifications"].extend(self._parse_certifications_section(content))
            elif sec_type == "achievements":
                results["achievements"].extend(self._parse_achievements_section(content))
        return results

    # ===== Name extraction heuristic =====
    def _extract_name_heuristic(self, text: str) -> Optional[str]:
        """
        Fallback name extraction when NER fails.
        Checks first 8 lines for a 2-4 word capitalized name.
        """
        from app.core.config import settings

        lines = text.strip().split('\n')
        for line in lines[:8]:
            line = line.strip()
            if not line or len(line) < 3 or len(line) > 60:
                continue
            # Skip emails, phones, urls
            if '@' in line:
                continue
            if re.search(r'\d{3}[\s\-.]?\d{3}', line):
                continue
            if re.search(r'https?://', line, re.I):
                continue
            if re.search(r'linkedin|github', line, re.I):
                continue
            # Skip section headers
            line_lower = line.lower().strip().rstrip(':')
            is_header = False
            for kws in settings.SECTION_KEYWORDS.values():
                if line_lower in kws:
                    is_header = True
                    break
            if is_header:
                continue
            # Name: 2-4 words, each starts with capital
            words = line.split()
            if 2 <= len(words) <= 4:
                alpha_words = [w for w in words if re.match(r'^[A-Z][a-zA-Z.\-\']+$', w)]
                if len(alpha_words) >= 2:
                    return line
            # ALL CAPS name
            if 2 <= len(words) <= 4 and line == line.upper():
                if all(re.match(r'^[A-Z.\-\']+$', w) for w in words):
                    return line.title()
        return None

    def _merge_extractions(
        self, ner_entities, regex_results, section_results, cleaned_text
    ) -> Dict:
        merged = {
            "personal_info": {}, "education": [], "experience": [],
            "skills": [], "projects": [], "certifications": [],
            "publications": [], "achievements": [],
        }

        # === Personal Info ===
        if regex_results["emails"]:
            merged["personal_info"]["email"] = regex_results["emails"][0]["value"]
        if regex_results["phones"]:
            merged["personal_info"]["phone"] = regex_results["phones"][0]["value"]
        for url_type, url_data in regex_results.get("urls", {}).items():
            merged["personal_info"][f"{url_type}_url"] = url_data["value"]

        # NER entities (labels already normalized)
        for entity in ner_entities:
            label = entity["label"]
            text_val = entity["text"]
            if label == "NAME":
                if not merged["personal_info"].get("full_name"):
                    merged["personal_info"]["full_name"] = text_val
            elif label == "LOCATION":
                if not merged["personal_info"].get("location"):
                    merged["personal_info"]["location"] = text_val
            elif label == "EMAIL" and not merged["personal_info"].get("email"):
                merged["personal_info"]["email"] = text_val
            elif label == "PHONE" and not merged["personal_info"].get("phone"):
                merged["personal_info"]["phone"] = text_val

        # ===== Name fallback chain =====
        if not merged["personal_info"].get("full_name"):
            heuristic_name = self._extract_name_heuristic(cleaned_text)
            if heuristic_name:
                merged["personal_info"]["full_name"] = heuristic_name
                logger.info(f"Name from heuristic: '{heuristic_name}'")

        if not merged["personal_info"].get("full_name"):
            email = merged["personal_info"].get("email", "")
            if email and "@" in email:
                local = email.split("@")[0]
                parts = re.split(r'[._\-]', local)
                parts = [p for p in parts if p and not p.isdigit() and len(p) > 1]
                if parts:
                    name = " ".join(p.capitalize() for p in parts)
                    merged["personal_info"]["full_name"] = name
                    logger.info(f"Name from email: '{name}'")

        # Summary
        if section_results.get("personal_info", {}).get("summary"):
            merged["personal_info"]["summary"] = section_results["personal_info"]["summary"]

        # === Education ===
        merged["education"] = section_results.get("education", [])
        for ent in ner_entities:
            if ent["label"] == "ORG":
                for edu in merged["education"]:
                    if "institution" not in edu:
                        edu["institution"] = ent["text"]
                        break

        # === Experience ===
        merged["experience"] = section_results.get("experience", [])
        for ent in ner_entities:
            if ent["label"] == "ORG":
                for exp in merged["experience"]:
                    if "company" not in exp:
                        exp["company"] = ent["text"]
                        break
            elif ent["label"] == "ROLE":
                for exp in merged["experience"]:
                    if "role" not in exp:
                        exp["role"] = ent["text"]
                        break

        # === Skills ===
        raw_skills = set()
        for ent in ner_entities:
            if ent["label"] == "SKILL":
                raw_skills.add(ent["text"])
        for skill in section_results.get("skills", []):
            raw_skills.add(skill)
        merged["skills"] = self.skill_normalizer.normalize(list(raw_skills))

        # === Projects ===
        merged["projects"] = section_results.get("projects", [])
        for ent in ner_entities:
            if ent["label"] == "PROJECT":
                if not any(ent["text"].lower() in p.get("title", "").lower() for p in merged["projects"]):
                    merged["projects"].append({"title": ent["text"]})

        # === Certifications ===
        merged["certifications"] = section_results.get("certifications", [])
        for ent in ner_entities:
            if ent["label"] == "CERT":
                merged["certifications"].append({"name": ent["text"]})

        # === Achievements ===
        merged["achievements"] = section_results.get("achievements", [])
        for ent in ner_entities:
            if ent["label"] == "ACHIEVEMENT":
                merged["achievements"].append({"title": ent["text"]})

        return merged

    # ===== Section parsers =====
    def _parse_education_section(self, lines: List[str]) -> List[Dict]:
        entries, current = [], {}
        for line in lines:
            line = line.strip()
            if not line:
                if current:
                    entries.append(current)
                    current = {}
                continue
            dm = self.DEGREE_PATTERNS.search(line)
            if dm:
                if current and "degree" in current:
                    entries.append(current)
                    current = {}
                current["degree"] = dm.group().strip()
            gm = self.GPA_PATTERN.search(line)
            if gm:
                current["gpa"] = float(gm.group(1))
                if gm.group(2):
                    current["gpa_scale"] = float(gm.group(2))
            dr = self._extract_date_range(line)
            if dr:
                current["date_range"] = dr
            else:
                for dp in self.DATE_PATTERNS:
                    d = dp.search(line)
                    if d:
                        if "start_date" not in current:
                            current["start_date"] = d.group()
                        elif "end_date" not in current:
                            current["end_date"] = d.group()
            if (
                not dm and not gm and len(line) > 3
                and "institution" not in current
                and (self.INSTITUTION_HINTS.search(line) or len(line.split()) >= 2)
            ):
                current["institution"] = line
        if current:
            entries.append(current)
        return self._dedupe_dict_entries(
            entries, key_order=["institution", "degree", "date_range"]
        )

    def _parse_experience_section(self, lines: List[str]) -> List[Dict]:
        entries, current, resps = [], {}, []
        for line in lines:
            line = line.strip()
            if not line:
                if current:
                    current["responsibilities"] = resps
                    entries.append(current)
                    current, resps = {}, []
                continue
            has_date = any(p.search(line) for p in self.DATE_PATTERNS)
            matched_header = self._parse_experience_header_line(line)
            if matched_header:
                if current:
                    current["responsibilities"] = resps
                    entries.append(current)
                    resps = []
                current = {"raw_header": line, **matched_header}
            elif has_date and len(line.split()) <= 16:
                if current:
                    current["responsibilities"] = resps
                    entries.append(current)
                    resps = []
                current = {"raw_header": line}
                current["date_range"] = self._extract_date_range(line) or line
                cleaned = self._strip_dates(line).strip(" |-–,")
                if " at " in cleaned.lower():
                    role, company = re.split(r'\s+at\s+', cleaned, maxsplit=1, flags=re.I)
                    current["role"] = role.strip()
                    current["company"] = company.strip()
                else:
                    current["role"] = cleaned
            elif line.startswith(('•', '-')):
                resp = line.lstrip('•- ').strip()
                if resp:
                    resps.append(resp)
            elif current:
                resps.append(line)
        if current:
            current["responsibilities"] = resps
            entries.append(current)
        cleaned_entries = []
        for e in entries:
            e["responsibilities"] = [r for r in e.get("responsibilities", []) if r]
            cleaned_entries.append(e)
        return self._dedupe_dict_entries(cleaned_entries, key_order=["company", "role", "date_range", "raw_header"])

    def _parse_skills_section(self, lines: List[str]) -> List[str]:
        skills = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Drop a leading category label like "Languages:" or "Tools -"
            line = re.sub(r'^[\w\s/&]+[:\-–]\s+', '', line, count=1)
            parts = re.split(r'[,;|•●○▪·/\t\n]+', line)
            for part in parts:
                skill = part.strip().strip('-–—● ').strip()
                if not skill or len(skill) < 2:
                    continue
                # Strip trailing proficiency annotations: "(Advanced)", "- Expert",
                # ": Intermediate", star ratings, or year counts.
                skill = re.sub(
                    r'\s*[\(\[]?\s*(?:beginner|basic|intermediate|advanced|'
                    r'proficient|expert|familiar|fluent|native|working knowledge|'
                    r'\d+\+?\s*(?:years?|yrs?)|[★☆]+)\s*[\)\]]?\s*$',
                    '', skill, flags=re.I,
                ).strip(' -–—:()[]')
                if skill and len(skill) >= 2 and len(skill) <= 50:
                    skills.append(skill)
        return skills

    def _parse_projects_section(self, lines: List[str]) -> List[Dict]:
        entries, current, desc = [], {}, []
        for line in lines:
            line = line.strip()
            if not line:
                if current:
                    current["description"] = " ".join(desc)
                    entries.append(current)
                    current, desc = {}, []
                continue
            if not current or (len(line.split()) <= 8 and not line.startswith(('•', '-'))):
                if current:
                    current["description"] = " ".join(desc)
                    entries.append(current)
                    desc = []
                current = {"title": line}
            else:
                desc.append(line.lstrip('•- ').strip())
        if current:
            current["description"] = " ".join(desc)
            entries.append(current)
        return entries

    def _parse_certifications_section(self, lines: List[str]) -> List[Dict]:
        entries = []
        for line in lines:
            line = line.strip().lstrip('•- ')
            if line and len(line) > 3:
                entry = {"name": line}
                for dp in self.DATE_PATTERNS:
                    d = dp.search(line)
                    if d:
                        entry["date"] = d.group()
                        entry["name"] = dp.sub('', line).strip(' |-–,')
                        break
                entries.append(entry)
        return entries

    def _extract_date_range(self, text: str) -> Optional[str]:
        for p in self.DATE_PATTERNS:
            m = p.search(text)
            if m:
                return m.group().strip()
        return None

    def _strip_dates(self, text: str) -> str:
        cleaned = text
        for p in self.DATE_PATTERNS:
            cleaned = p.sub("", cleaned)
        return re.sub(r'\s{2,}', ' ', cleaned).strip()

    def _parse_experience_header_line(self, line: str) -> Optional[Dict]:
        date_range = self._extract_date_range(line)

        # Common format: "Role - Company - 2019 - 2021"
        hyphen_parts = [p.strip() for p in re.split(r'\s+-\s+', line) if p.strip()]
        if len(hyphen_parts) >= 3:
            maybe_role = hyphen_parts[0]
            maybe_company = hyphen_parts[1]
            maybe_tail = " - ".join(hyphen_parts[2:])
            if self._extract_date_range(maybe_tail) or re.search(r'\b(?:19|20)\d{2}\b', maybe_tail):
                result = {"role": maybe_role, "company": maybe_company}
                if date_range:
                    result["date_range"] = date_range
                else:
                    result["date_range"] = maybe_tail
                return result

        for pat in self.EXPERIENCE_HEADER_PATTERNS:
            m = pat.match(line)
            if not m:
                continue
            role = (m.groupdict().get("role") or "").strip(" |-–—,")
            company = (m.groupdict().get("company") or "").strip(" |-–—,")
            date = (m.groupdict().get("date") or "").strip(" |-–—,")
            result = {}
            if role:
                result["role"] = role
            if company:
                result["company"] = company
            if date:
                result["date_range"] = date
            elif date_range:
                result["date_range"] = date_range
            if result:
                return result
        return None

    def _dedupe_dict_entries(self, entries: List[Dict], key_order: List[str]) -> List[Dict]:
        seen = set()
        out = []
        for e in entries:
            parts = [str(e.get(k, "")).strip().lower() for k in key_order]
            key = "|".join(parts)
            if key and key not in seen:
                seen.add(key)
                out.append(e)
        return out
    def _parse_achievements_section(self, lines: List[str]) -> List[Dict]:
        return [
            {"title": line.strip().lstrip('•- '), "confidence": 0.7}
            for line in lines
            if line.strip().lstrip('•- ') and len(line.strip()) > 3
        ]
