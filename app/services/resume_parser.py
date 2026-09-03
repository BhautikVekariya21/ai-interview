"""
Main orchestrator service for the resume parsing pipeline.
Coordinates all sub-services and produces the final ParsedResume JSON.
"""

import inspect
import re
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, List, Optional

from loguru import logger

from app.schemas.schemas import (
    Achievement,
    Certification,
    Education,
    ExperienceLevel,
    ParsedResume,
    PersonalInfo,
    Project,
    Publication,
    Skill,
    WorkExperience,
)
from app.services.entity_extractor import EntityExtractor
from app.services.file_extractor import FileExtractor
from app.services.ner_engine import NEREngine
from app.services.rust_accelerator import get_rust_accelerator
from app.services.section_detector import SectionDetector
from app.services.skill_normalizer import SkillNormalizer
from app.services.text_preprocessor import TextPreprocessor


class ResumeParser:
    """
    Master orchestrator for the resume parsing pipeline.
    """

    def __init__(self):
        logger.info("Initializing ResumeParser pipeline...")

        self._rust = get_rust_accelerator()
        self.file_extractor = FileExtractor()
        self.preprocessor = TextPreprocessor()
        self.ner_engine = NEREngine()
        self.section_detector = SectionDetector()
        self.skill_normalizer = SkillNormalizer()
        self.entity_extractor = EntityExtractor(self.ner_engine, self.skill_normalizer)

        try:
            self.ner_engine.load_model()
        except Exception as e:
            logger.warning(f"NER model not available: {e}. Using rule-based extraction only.")

        logger.info("ResumeParser pipeline initialized")

    @staticmethod
    async def _emit_progress(
        callback: Optional[Callable[[int, int, str], Awaitable[None]]],
        step: int,
        total_steps: int,
        message: str,
    ) -> None:
        """Emit progress events to a callback (sync or async)."""
        if callback is None:
            return
        result = callback(step, total_steps, message)
        if inspect.isawaitable(result):
            await result

    async def parse(
        self,
        file_content: bytes,
        filename: str,
        progress_callback: Optional[Callable[[int, int, str], Awaitable[None]]] = None,
    ) -> ParsedResume:
        """Parse a resume file into structured JSON."""
        start_time = time.time()
        warnings: List[str] = []
        total_steps = 7

        logger.info(f"{'=' * 60}")
        logger.info(f"PARSING RESUME: {filename}")
        logger.info(f"{'=' * 60}")
        print(f"[parser] start parse: {filename}", flush=True)

        # Step 1: Extract text
        logger.info("[1/7] Extracting text from file...")
        print("[parser] [1/7] extracting text", flush=True)
        await self._emit_progress(
            progress_callback, 1, total_steps, "Extracting text from document"
        )
        raw_text, file_type = await self.file_extractor.extract(file_content, filename)

        # Step 2: Preprocess
        logger.info("[2/7] Preprocessing text...")
        print("[parser] [2/7] preprocessing text", flush=True)
        await self._emit_progress(
            progress_callback, 2, total_steps, "Preprocessing and cleaning text"
        )
        preprocessed = self.preprocessor.preprocess(raw_text)
        cleaned_text = preprocessed["cleaned_text"]
        lines = preprocessed["lines"]
        tokens = preprocessed["tokens"]

        # Step 3: Detect sections
        logger.info("[3/7] Detecting sections...")
        print("[parser] [3/7] detecting sections", flush=True)
        await self._emit_progress(progress_callback, 3, total_steps, "Detecting resume sections")
        sections = self.section_detector.detect_sections(lines)

        # Step 4: Extract entities
        logger.info("[4/7] Extracting entities...")
        print("[parser] [4/7] extracting entities", flush=True)
        await self._emit_progress(
            progress_callback, 4, total_steps, "Running NER entity extraction"
        )
        extracted = self.entity_extractor.extract_all(cleaned_text, lines, tokens, sections)

        # Step 5: Build structured output
        logger.info("[5/7] Building structured output...")
        print("[parser] [5/7] building structured resume", flush=True)
        await self._emit_progress(progress_callback, 5, total_steps, "Building structured profile")
        parsed = self._build_parsed_resume(extracted, cleaned_text, filename, file_type)

        # Step 6: Infer experience level
        logger.info("[6/7] Inferring experience level...")
        print("[parser] [6/7] inferring experience level", flush=True)
        await self._emit_progress(
            progress_callback, 6, total_steps, "Inferring experience insights"
        )
        parsed.total_experience_years = self._calculate_total_experience(parsed.work_experience)
        parsed.experience_level = self._infer_experience_level(parsed.total_experience_years)

        # Step 7: Compute metadata
        logger.info("[7/7] Computing metadata...")
        print("[parser] [7/7] computing metadata", flush=True)
        await self._emit_progress(progress_callback, 7, total_steps, "Computing final metadata")
        parsed.primary_domain = self._infer_domain(parsed.skills)
        parsed.top_skills = [s.name for s in parsed.skills[:10]]
        parsed.skill_categories = self.skill_normalizer.categorize_skills(
            [{"name": s.name, "category": s.category} for s in parsed.skills]
        )
        parsed.parse_timestamp = datetime.now(timezone.utc).isoformat()
        parsed.raw_text_length = len(cleaned_text)
        parsed.overall_parse_confidence = self._compute_overall_confidence(parsed)
        parsed.warnings = warnings

        elapsed = time.time() - start_time
        logger.info(f"PARSING COMPLETE in {elapsed:.2f}s")
        print(f"[parser] done in {elapsed:.2f}s", flush=True)

        return parsed

    def _build_parsed_resume(
        self,
        extracted: Dict,
        cleaned_text: str,
        filename: str,
        file_type: str,
    ) -> ParsedResume:
        """Convert raw extractions to Pydantic schema."""

        pi_data = extracted.get("personal_info", {})
        personal_info = PersonalInfo(
            full_name=pi_data.get("full_name"),
            email=pi_data.get("email"),
            phone=pi_data.get("phone"),
            linkedin_url=pi_data.get("linkedin_url"),
            github_url=pi_data.get("github_url"),
            portfolio_url=pi_data.get("portfolio_url"),
            location=pi_data.get("location"),
            summary=pi_data.get("summary"),
        )

        if personal_info.full_name:
            name_parts = personal_info.full_name.split()
            if len(name_parts) >= 2:
                personal_info.first_name = name_parts[0]
                personal_info.last_name = name_parts[-1]
            elif len(name_parts) == 1:
                personal_info.first_name = name_parts[0]

        education: List[Education] = []
        for edu_data in extracted.get("education", []):
            try:
                edu = Education(
                    institution=edu_data.get("institution", "Unknown"),
                    degree=edu_data.get("degree"),
                    field_of_study=edu_data.get("field"),
                    gpa=edu_data.get("gpa"),
                    gpa_scale=edu_data.get("gpa_scale", 4.0),
                    start_date=edu_data.get("start_date"),
                    end_date=edu_data.get("end_date"),
                    confidence=0.7,
                )
                education.append(edu)
            except Exception as e:
                logger.warning(f"Failed to parse education entry: {e}")

        work_experience: List[WorkExperience] = []
        for exp_data in extracted.get("experience", []):
            try:
                exp = WorkExperience(
                    company=exp_data.get("company", "Unknown"),
                    role=exp_data.get("role", "Unknown"),
                    location=exp_data.get("location"),
                    start_date=exp_data.get("start_date"),
                    end_date=exp_data.get("end_date"),
                    is_current="present" in str(exp_data.get("end_date", "")).lower(),
                    responsibilities=exp_data.get("responsibilities", []),
                    confidence=0.7,
                )
                work_experience.append(exp)
            except Exception as e:
                logger.warning(f"Failed to parse experience entry: {e}")

        skills: List[Skill] = []
        for skill_data in extracted.get("skills", []):
            try:
                skill = Skill(
                    name=skill_data.get("name", ""),
                    category=skill_data.get("category", "other"),
                    confidence=skill_data.get("confidence", 0.5),
                )
                skills.append(skill)
            except Exception as e:
                logger.warning(f"Failed to parse skill: {e}")

        skills.sort(key=lambda s: s.confidence, reverse=True)

        # Augment with taxonomy skills mentioned anywhere in the resume
        # (e.g. inside experience/project bullets, not just a Skills section).
        existing_names = {s.name.lower() for s in skills}
        for match in self._scan_taxonomy_skills(cleaned_text):
            if match["name"].lower() not in existing_names:
                existing_names.add(match["name"].lower())
                skills.append(
                    Skill(
                        name=match["name"],
                        category=match["category"],
                        confidence=0.55,
                    )
                )

        projects: List[Project] = []
        for proj_data in extracted.get("projects", []):
            try:
                proj = Project(
                    title=proj_data.get("title", "Unknown"),
                    description=proj_data.get("description"),
                    technologies=proj_data.get("technologies", []),
                    url=proj_data.get("url"),
                    confidence=0.7,
                )
                projects.append(proj)
            except Exception as e:
                logger.warning(f"Failed to parse project: {e}")

        certifications: List[Certification] = []
        for cert_data in extracted.get("certifications", []):
            try:
                cert = Certification(
                    name=cert_data.get("name", "Unknown"),
                    issue_date=cert_data.get("date"),
                    confidence=0.7,
                )
                certifications.append(cert)
            except Exception as e:
                logger.warning(f"Failed to parse certification: {e}")

        achievements: List[Achievement] = []
        for ach_data in extracted.get("achievements", []):
            try:
                ach = Achievement(
                    title=ach_data.get("title", "Unknown"),
                    confidence=ach_data.get("confidence", 0.6),
                )
                achievements.append(ach)
            except Exception as e:
                logger.warning(f"Failed to parse achievement: {e}")

        # Robust fallback extraction for noisy resumes
        if not skills:
            fallback_skills = self._fallback_extract_skills(cleaned_text)
            for name in fallback_skills[:20]:
                skills.append(Skill(name=name, category="other", confidence=0.45))

        if not projects:
            fallback_projects = self._fallback_extract_projects(cleaned_text)
            for title in fallback_projects[:5]:
                projects.append(
                    Project(
                        title=title, description=None, technologies=[], url=None, confidence=0.45
                    )
                )

        if not certifications:
            for name, date in self._fallback_extract_certifications(cleaned_text)[:15]:
                certifications.append(
                    Certification(name=name, issue_date=date, confidence=0.4)
                )

        if not achievements:
            for title in self._fallback_extract_achievements(cleaned_text)[:15]:
                achievements.append(Achievement(title=title, confidence=0.4))

        if not personal_info.email:
            m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", cleaned_text)
            if m:
                personal_info.email = m.group(0)

        return ParsedResume(
            personal_info=personal_info,
            education=education,
            work_experience=work_experience,
            skills=skills,
            projects=projects,
            certifications=certifications,
            publications=[],
            achievements=achievements,
            source_file_name=filename,
            source_file_type=file_type,
        )

    def _fallback_extract_skills(self, text: str) -> List[str]:
        return [m["name"] for m in self._scan_taxonomy_skills(text)]

    def _scan_taxonomy_skills(self, text: str) -> List[Dict]:
        """Scan the whole resume for any known skill alias from the taxonomy.

        Uses the SkillNormalizer's lookup table so it stays in sync with the
        canonical taxonomy instead of a tiny hard-coded list. Matches on word
        boundaries and returns canonical names with their categories.
        """
        txt = (text or "").lower()
        if not txt:
            return []

        results: List[Dict] = []
        seen = set()
        lookup = getattr(self.skill_normalizer, "lookup_table", {})
        for alias, (canonical, category) in lookup.items():
            if len(alias) < 2:
                continue
            key = canonical.lower()
            if key in seen:
                continue
            # Escape alias; allow '.', '+', '#' which appear in tech names.
            pattern = r"(?<![\w.+#])" + re.escape(alias) + r"(?![\w.+#])"
            if re.search(pattern, txt):
                seen.add(key)
                results.append({"name": canonical, "category": category})
        return results

    def _fallback_extract_projects(self, text: str) -> List[str]:
        if self._rust and hasattr(self._rust, "fallback_project_lines"):
            return self._rust.fallback_project_lines(text or "", 80)

        lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
        out: List[str] = []
        for ln in lines:
            if any(w in ln.lower() for w in ["project", "built", "developed", "implemented"]):
                if 6 <= len(ln) <= 120:
                    out.append(ln[:80])
        dedup = []
        seen = set()
        for x in out:
            k = x.lower()
            if k not in seen:
                seen.add(k)
                dedup.append(x)
        return dedup

    # Signals that a line names a certification / course / license.
    _CERT_HINTS = re.compile(
        r"\b(certified|certificate|certification|certyfi|"
        r"credential|licen[sc]e|nanodegree|specialization|"
        r"microdegree|bootcamp|coursera|udemy|udacity|edx|"
        r"aws|azure|gcp|google cloud|oracle|cisco|comptia|pmp|"
        r"scrum|kubernetes|professional certificate)\b",
        re.I,
    )
    # Signals that a line describes an award / achievement / honor.
    _ACHIEVEMENT_HINTS = re.compile(
        r"\b(award|awarded|winner|won|first place|second place|third place|"
        r"rank(?:ed)?|runner[- ]?up|finalist|medal|gold|silver|bronze|"
        r"scholarship|honou?r|honou?rs|dean'?s list|recognition|recognized|"
        r"achievement|achieved|top \d+|percentile|selected|hackathon|"
        r"prize|trophy|distinction|merit)\b",
        re.I,
    )

    def _fallback_extract_certifications(self, text: str):
        """Find certification-like lines anywhere when no section was detected."""
        results = []
        seen = set()
        for raw in (text or "").splitlines():
            line = raw.strip().lstrip("•-*● ").strip()
            if not (5 <= len(line) <= 140):
                continue
            if not self._CERT_HINTS.search(line):
                continue
            date = None
            m = re.search(r"\b(20\d{2}|19\d{2})\b", line)
            if m:
                date = m.group()
            name = line
            key = name.lower()
            if key not in seen:
                seen.add(key)
                results.append((name, date))
        return results

    def _fallback_extract_achievements(self, text: str):
        """Find award/achievement-like lines anywhere when no section was detected."""
        results = []
        seen = set()
        for raw in (text or "").splitlines():
            line = raw.strip().lstrip("•-*● ").strip()
            if not (5 <= len(line) <= 160):
                continue
            if not self._ACHIEVEMENT_HINTS.search(line):
                continue
            key = line.lower()
            if key not in seen:
                seen.add(key)
                results.append(line)
        return results

    def _calculate_total_experience(self, experiences: List[WorkExperience]) -> float:
        """Calculate total years of experience."""
        total_months = 0

        for exp in experiences:
            if exp.duration_months:
                total_months += exp.duration_months
            elif exp.start_date and exp.end_date:
                try:
                    start_years = re.findall(r"\d{4}", str(exp.start_date))
                    end_years = re.findall(r"\d{4}", str(exp.end_date))

                    if start_years:
                        start_year = int(start_years[0])
                        if end_years:
                            end_year = int(end_years[0])
                        elif exp.is_current:
                            end_year = datetime.now().year
                        else:
                            continue

                        months = (end_year - start_year) * 12
                        if months > 0:
                            total_months += months
                except Exception:
                    pass
            elif exp.is_current:
                total_months += 12

        return total_months / 12.0

    def _infer_experience_level(self, years: float) -> ExperienceLevel:
        """Infer experience level from total years."""
        if years < 0.5:
            return ExperienceLevel.INTERN
        elif years < 2:
            return ExperienceLevel.JUNIOR
        elif years < 5:
            return ExperienceLevel.MID_LEVEL
        elif years < 10:
            return ExperienceLevel.SENIOR
        elif years < 15:
            return ExperienceLevel.LEAD
        else:
            return ExperienceLevel.EXECUTIVE

    def _infer_domain(self, skills: List[Skill]) -> Optional[str]:
        """Infer primary professional domain from skills."""
        domain_indicators = {
            "backend": [
                "Python",
                "Java",
                "Go",
                "Node.js",
                "Django",
                "Flask",
                "FastAPI",
                "Spring Boot",
                "PostgreSQL",
                "REST API",
            ],
            "frontend": [
                "React",
                "Angular",
                "Vue.js",
                "JavaScript",
                "TypeScript",
                "CSS",
                "HTML",
                "Tailwind CSS",
                "Next.js",
            ],
            "fullstack": [
                "React",
                "Node.js",
                "MongoDB",
                "Express.js",
            ],
            "ml_ai": [
                "PyTorch",
                "PyTorch Lightning",
                "Hugging Face",
                "scikit-learn",
                "NLP",
                "Computer Vision",
                "Deep Learning",
                "Machine Learning",
            ],
            "data_science": [
                "Pandas",
                "NumPy",
                "R",
                "Statistics",
                "Tableau",
                "Power BI",
                "SQL",
            ],
            "devops": [
                "Docker",
                "Kubernetes",
                "Terraform",
                "Jenkins",
                "CI/CD",
                "AWS",
                "Azure",
                "GCP",
            ],
            "mobile": [
                "Swift",
                "Kotlin",
                "React Native",
                "Flutter",
                "Dart",
                "iOS",
                "Android",
            ],
        }

        skill_names = {s.name.lower() for s in skills}
        domain_scores: Dict[str, int] = {}

        for domain, indicators in domain_indicators.items():
            score = sum(1 for ind in indicators if ind.lower() in skill_names)
            domain_scores[domain] = score

        if domain_scores:
            best_domain = max(domain_scores, key=lambda k: domain_scores[k])
            if domain_scores[best_domain] > 0:
                return best_domain

        return None

    def _compute_overall_confidence(self, parsed: ParsedResume) -> float:
        """Compute overall parsing confidence score."""
        scores: List[float] = []

        pi = parsed.personal_info
        pi_fields = [pi.full_name, pi.email, pi.phone]
        pi_score = sum(1 for f in pi_fields if f) / len(pi_fields)
        scores.append(pi_score)

        if parsed.education:
            edu_scores = [e.confidence for e in parsed.education]
            scores.append(sum(edu_scores) / len(edu_scores))
        else:
            scores.append(0.3)

        if parsed.work_experience:
            exp_scores = [e.confidence for e in parsed.work_experience]
            scores.append(sum(exp_scores) / len(exp_scores))
        else:
            scores.append(0.3)

        if parsed.skills:
            skill_scores = [s.confidence for s in parsed.skills]
            scores.append(sum(skill_scores) / len(skill_scores))
        else:
            scores.append(0.2)

        return sum(scores) / len(scores) if scores else 0.0
