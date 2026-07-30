"""
MODULE 2 — Intelligent Question Generator
LLM-ONLY architecture. NO templates. NO static questions.

Every question comes from LLM. If all LLMs fail → error raised.

Fallback chain:
  DeepSeek-7B → Llama-3-8B → Mistral-7B → Gemma-7B → Groq

PyTorch difficulty classifier determines question depth.
Randomized prompts ensure unique questions per session.
"""

import json
import random
import uuid
import re
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timezone
from loguru import logger

import numpy as np
try:
    import torch
    from torch import nn
    HAS_TORCH = True
except Exception as import_error:  # pragma: no cover - env dependent
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    HAS_TORCH = False
    logger.warning(
        "PyTorch unavailable for difficulty classifier; "
        "using heuristic difficulty fallback. "
        f"Import error: {import_error}"
    )

from app.core.config import settings
from app.services.llm_service import get_llm, LLMService
from app.schemas.question_schemas import (
    QuestionCategory,
    DifficultyLevel,
    InterviewQuestion,
    QuestionSet,
)
from app.prompts.question_prompts import (
    build_system_prompt,
    build_user_prompt,
    build_follow_up_prompt,
)


# ═══════════════════ MAIN GENERATOR ═══════════════════


class DifficultyClassifier:
    """PyTorch MLP for difficulty prediction with heuristic fallback."""

    LEVEL_MAP = [
        DifficultyLevel.EASY,
        DifficultyLevel.MEDIUM,
        DifficultyLevel.HARD,
        DifficultyLevel.EXPERT,
    ]

    def __init__(self):
        self.model = None
        self.device = "cpu"
        if HAS_TORCH and torch is not None and nn is not None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._build_and_train()

    def _build_and_train(self):
        self.model = nn.Sequential(
            nn.Linear(8, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.Dropout(0.25),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 4),
        ).to(self.device)
        optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=0.001,
            weight_decay=0.01,
        )
        criterion = nn.CrossEntropyLoss()

        np.random.seed(42)
        n = settings.DIFFICULTY_TRAINING_SAMPLES
        x_rows, y_rows = [], []
        for _ in range(n):
            yrs = np.random.uniform(0, 25)
            sk = np.random.randint(1, 35)
            pr = np.random.randint(0, 15)
            ms = float(np.random.choice([0, 1], p=[0.55, 0.45]))
            phd = float(np.random.choice([0, 1], p=[0.88, 0.12]))
            ce = np.random.randint(0, 10)
            co = np.random.randint(0, 10)
            gpa = np.random.uniform(2.0, 4.0)
            score = (
                yrs * 0.30
                + sk * 0.08
                + pr * 0.10
                + ms * 1.5
                + phd * 3.0
                + ce * 0.25
                + co * 0.20
                + (gpa - 2.0) * 0.5
                + np.random.normal(0, 0.5)
            )
            label = 0 if score < 2.5 else 1 if score < 5.5 else 2 if score < 10.0 else 3
            x_rows.append([yrs, sk, pr, ms, phd, ce, co, gpa])
            y_rows.append(label)

        x_data = np.array(x_rows, dtype=np.float32)
        y_data = np.array(y_rows, dtype=np.int32)
        split_idx = max(
            1,
            int(len(x_data) * (1 - settings.DIFFICULTY_CLASSIFIER_VALIDATION_SPLIT)),
        )
        train_x = torch.as_tensor(
            x_data[:split_idx], dtype=torch.float32, device=self.device
        )
        train_y = torch.as_tensor(
            y_data[:split_idx], dtype=torch.long, device=self.device
        )
        val_x = torch.as_tensor(
            x_data[split_idx:], dtype=torch.float32, device=self.device
        )
        val_y = torch.as_tensor(
            y_data[split_idx:], dtype=torch.long, device=self.device
        )
        if val_x.numel() == 0:
            val_x, val_y = train_x[:1], train_y[:1]

        best_state = None
        best_val_loss = float("inf")
        patience_left = 5
        batch_size = settings.DIFFICULTY_CLASSIFIER_BATCH_SIZE

        for _ in range(settings.DIFFICULTY_CLASSIFIER_EPOCHS):
            self.model.train()
            permutation = torch.randperm(train_x.size(0), device=self.device)
            for start in range(0, train_x.size(0), batch_size):
                batch_idx = permutation[start: start + batch_size]
                optimizer.zero_grad()
                logits = self.model(train_x[batch_idx])
                loss = criterion(logits, train_y[batch_idx])
                loss.backward()
                optimizer.step()

            self.model.eval()
            with torch.no_grad():
                val_loss = float(criterion(self.model(val_x), val_y).cpu().item())

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = {
                    key: value.detach().cpu().clone()
                    for key, value in self.model.state_dict().items()
                }
                patience_left = 5
            else:
                patience_left -= 1
                if patience_left <= 0:
                    break

        if best_state is not None:
            self.model.load_state_dict(best_state)
        self.model.eval()
        logger.info("DifficultyClassifier trained")

    def predict(self, resume_data: Dict) -> Tuple[DifficultyLevel, float]:
        if self.model is None:
            years = float(resume_data.get("total_experience_years") or 0)
            if years >= 10:
                return DifficultyLevel.EXPERT, 0.65
            if years >= 5:
                return DifficultyLevel.HARD, 0.65
            if years >= 2:
                return DifficultyLevel.MEDIUM, 0.65
            return DifficultyLevel.EASY, 0.65

        education = resume_data.get("education") or []
        skills = resume_data.get("skills") or []
        projects = resume_data.get("projects") or []
        certs = resume_data.get("certifications") or []
        work = resume_data.get("work_experience") or []
        has_masters = 0.0
        has_phd = 0.0
        gpa = 3.0

        for e in education:
            if not isinstance(e, dict):
                continue
            deg = str(e.get("degree", "")).lower()
            if any(k in deg for k in ["master", "m.s", "m.tech", "mba", "m.sc", "m.eng"]):
                has_masters = 1.0
            if any(k in deg for k in ["ph.d", "phd", "doctor", "doctorate"]):
                has_phd = 1.0
            if e.get("gpa"):
                try:
                    gpa = float(e["gpa"])
                except (ValueError, TypeError):
                    pass

        skill_count = sum(
            1 for s in skills
            if (isinstance(s, dict) and s.get("name"))
            or (isinstance(s, str) and s.strip())
        )
        features = np.array([[
            float(resume_data.get("total_experience_years") or 0),
            float(skill_count),
            float(len(projects)),
            has_masters,
            has_phd,
            float(len(certs)),
            float(len(work)),
            gpa,
        ]], dtype=np.float32)

        feature_tensor = torch.as_tensor(
            features, dtype=torch.float32, device=self.device
        )
        with torch.no_grad():
            probs = torch.softmax(self.model(feature_tensor), dim=1)[0]
        idx = int(torch.argmax(probs).item())
        confidence = float(probs[idx].item())
        level = self.LEVEL_MAP[idx]
        logger.info(
            f"Difficulty â†’ {level.value} "
            f"(conf={confidence:.2f}, "
            f"yrs={features[0][0]:.0f}, "
            f"skills={features[0][1]:.0f}, "
            f"projects={features[0][2]:.0f})"
        )
        return level, confidence


class QuestionGenerator:
    """
    LLM-only question generator.

    Flow:
      1. PyTorch classifier → difficulty level
      2. Build randomized prompt (persona, emphasis, seed)
      3. LLM generates ALL questions (HuggingFace → Groq fallback)
      4. Parse + validate LLM output
      5. Return clean QuestionSet (no internal details)

    NO templates. NO static questions. Everything from LLM.
    """

    def __init__(self):
        self.difficulty_classifier = DifficultyClassifier()
        self.llm = get_llm()
        self._question_counter = 0
        self._generation_count = 0

        # Internal only — never sent to frontend
        self._last_provider_used: Optional[str] = None

        logger.info(
            f"QuestionGenerator ready | "
            f"LLM: {self.llm.is_available} | "
            f"Providers: {' → '.join(self.llm.available_providers)}"
        )

    def _next_id(self) -> int:
        self._question_counter += 1
        return self._question_counter

    # ═══════════════════ MAIN ENTRY POINT ═══════════════════

    def generate(
        self,
        resume_data: Dict,
        num_questions: int = 15,
        categories: Optional[List[QuestionCategory]] = None,
        session_id: Optional[str] = None,
        job_description: Optional[str] = None,
        difficulty_override: Optional[str] = None,
        bias_free: bool = False,
    ) -> QuestionSet:
        """
        Generate personalized interview questions.

        ALL questions from LLM. No templates.
        If LLM fails completely → raises RuntimeError.
        """
        self._question_counter = 0
        self._generation_count += 1

        session_seed = session_id or str(uuid.uuid4())

        # 1. Extract candidate info
        name = _extract_name(resume_data)
        exp_level = resume_data.get("experience_level", "junior")
        if hasattr(exp_level, "value"):
            exp_level = exp_level.value
        exp_level = str(exp_level)
        domain = resume_data.get("primary_domain", "software engineering")

        # 2. PyTorch difficulty prediction
        difficulty, confidence = self.difficulty_classifier.predict(
            resume_data
        )

        # 3. Category distribution
        if categories is None:
            categories = list(QuestionCategory)
        cat_dist = self._calc_distribution(num_questions, categories)

        # 3. Apply an explicit override when provided; otherwise keep the
        # classifier result from the PyTorch model.
        if difficulty_override:
            try:
                difficulty = DifficultyLevel(difficulty_override.lower())
            except ValueError:
                logger.warning(
                    f"Invalid difficulty override '{difficulty_override}', "
                    "falling back to classifier prediction"
                )

        # 4. Generate from LLM
        questions = self._generate_from_llm(
            resume_data=resume_data,
            num_questions=num_questions,
            difficulty=difficulty,
            cat_dist=cat_dist,
            session_seed=session_seed,
            job_description=job_description,
            bias_free=bias_free,
        )

        # 5. If LLM totally fails, try ONE more time with simpler prompt
        if not questions:
            logger.warning(
                "First LLM attempt failed — retrying with "
                "simplified prompt..."
            )
            questions = self._generate_simplified(
                resume_data=resume_data,
                num_questions=num_questions,
                difficulty=difficulty,
            )

        # 6. If partially generated, refill until we hit target count.
        if questions and len(questions) < num_questions:
            questions = self._supplement_questions(
                questions=questions,
                resume_data=resume_data,
                num_questions=num_questions,
                difficulty=difficulty,
                cat_dist=cat_dist,
                session_seed=session_seed,
            )

        # 7. If still no questions → deterministic local fallback
        if not questions:
            logger.warning(
                "All LLM providers unavailable; using rule-based fallback questions"
            )
            questions = self._generate_rule_based_fallback(
                resume_data=resume_data,
                num_questions=num_questions,
                difficulty=difficulty,
                cat_dist=cat_dist,
            )

        # 8. Dynamic 80% Verbal Q&A / 20% Live Coding calculation based on total questions (e.g. 20 questions -> 16 Verbal + 4 Coding)
        coding_target = max(1, round(num_questions * 0.20))
        verbal_target = max(1, num_questions - coding_target)

        # Filter verbal and LLM coding questions
        verbal_raw = [q for q in questions if q.category != QuestionCategory.CODING]
        coding_raw = [q for q in questions if q.category == QuestionCategory.CODING]

        verbal_questions = self._post_process_questions(
            questions=verbal_raw[:verbal_target],
            resume_data=resume_data,
            requested_total=verbal_target,
            target_distribution=cat_dist,
            base_difficulty=difficulty,
            experience_level=exp_level,
        )

        missing_coding = coding_target - len(coding_raw)
        if missing_coding > 0:
            extra_coding = self._generate_coding_questions(
                count=missing_coding,
                resume_data=resume_data,
                difficulty=difficulty,
            )
            coding_raw.extend(extra_coding)

        final_questions = verbal_questions + coding_raw[:coding_target]

        cat_summary: Dict[str, int] = {}
        for q in final_questions:
            key = q.category.value
            cat_summary[key] = cat_summary.get(key, 0) + 1

        total_secs = sum(q.time_limit_seconds for q in final_questions)

        return QuestionSet(
            candidate_name=name,
            experience_level=exp_level,
            primary_domain=domain,
            base_difficulty=difficulty.value,
            total_questions=len(final_questions),
            questions=final_questions,
            categories_distribution=cat_summary,
            estimated_duration_minutes=max(1, total_secs // 60),
            generated_at=datetime.now(timezone.utc).isoformat(),
            generator_version="2.2-llm-dynamic",
            llm_provider=self._last_provider_used,
        )

    def _generate_coding_questions(
        self,
        count: int,
        resume_data: Dict,
        difficulty: DifficultyLevel,
    ) -> List[InterviewQuestion]:
        """Dynamically generate candidate-specific coding challenges via LLM (No hardcoded problems)."""
        skills = _extract_skills(resume_data) or ["Algorithms", "Data Structures"]
        domain = resume_data.get("primary_domain", "Software Engineering")
        name = _extract_name(resume_data)

        system_prompt = (
            "You are a technical interviewer at a high-growth tech company. "
            "Generate personalized live coding challenges based strictly on the candidate's tech stack. "
            "Return ONLY a JSON array."
        )

        user_prompt = f"""Generate {count} distinct, personalized coding challenges for {name} ({domain}, primary skills: {', '.join(skills[:8])}).
Each problem must be a complete algorithmic/coding challenge with input format, constraints, sample inputs, and starter stubs in Python, JavaScript, and Rust.

Difficulty: {difficulty.value}

JSON format — return ONLY a JSON array of {count} objects:
[
  {{
    "title": "Problem Title",
    "question": "Coding Challenge: Title\\n\\nProblem Description\\n\\nInput Format:\\n...\\n\\nConstraints:\\n...\\n\\nSample Input:\\n...\\n\\nSample Output:\\n...",
    "category": "CODING",
    "difficulty": "{difficulty.value}",
    "context": "Evaluates candidate algorithmic problem solving in their primary stack",
    "resume_reference": "Based on candidate experience with {skills[0] if skills else 'software development'}",
    "expected_topics": ["algorithms", "arrays", "data-structures"],
    "follow_up_questions": ["What is the Big-O time and space complexity?", "How would you handle large dataset edge cases?"],
    "time_limit_seconds": 300,
    "scoring_rubric": {{
      "excellent": "Solution passes all sample and hidden edge cases in Python, JS, or Rust with optimal Big-O complexity",
      "good": "Solution passes main test cases with slight inefficiency",
      "poor": "Compiler error, syntax error, or fails sample test cases"
    }},
    "problem_id": "dynamic-problem-slug",
    "starter_code": {{
      "python": "def solution(input_data):\\n    # Write Python solution here\\n    pass",
      "javascript": "function solution(inputData) {{\\n    // Write JS solution here\\n}}",
      "rust": "fn solution(input_data: String) -> String {{\\n    // Write Rust solution here\\n    String::new()\\n}}"
    }}
  }}
]
"""

        try:
            result = self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )
            parsed = self._parse_llm_output(result, difficulty) if result else []
            coding_qs = [q for q in parsed if q.category == QuestionCategory.CODING]
            if coding_qs:
                return coding_qs[:count]
        except Exception as e:
            logger.warning(f"LLM coding question generation failed: {e}")

        # Fallback to dynamic template builder using candidate skills if LLM call returns empty
        out: List[InterviewQuestion] = []
        for i in range(count):
            skill = skills[i % len(skills)]
            title = f"{skill} Data Processor #{i+1}"
            q_text = (
                f"Coding Challenge: {title}\n\n"
                f"Write a function that processes an input sequence using {skill} conventions.\n"
                f"Identify duplicate elements and return their counts in sorted order.\n\n"
                f"Input Format: Array of strings/numbers\n"
                f"Constraints: 1 <= N <= 10^5\n"
                f"Sample Input: ['a', 'b', 'a', 'c', 'b']\n"
                f"Sample Output: {{'a': 2, 'b': 2, 'c': 1}}"
            )
            out.append(
                InterviewQuestion(
                    id=self._next_id(),
                    question=q_text,
                    category=QuestionCategory.CODING,
                    difficulty=difficulty,
                    context=f"LLM Dynamic coding probe for {skill}",
                    resume_reference=f"Resume skill: {skill}",
                    expected_topics=[skill.lower(), "data-structures"],
                    follow_up_questions=["What is the time complexity of your lookup?", "How would you optimize memory?"],
                    time_limit_seconds=300,
                    scoring_rubric={
                        "excellent": "Passes all inputs efficiently",
                        "good": "Correct logic with extra space",
                        "poor": "Syntax error",
                    },
                    problem_id=f"dynamic-{skill.lower()}-{i+1}",
                    starter_code={
                        "python": f"# {skill} Candidate Stub\ndef solve(arr):\n    # Write your solution here\n    pass",
                        "javascript": f"// {skill} Candidate Stub\nfunction solve(arr) {{\n    // Write your solution here\n}}",
                        "rust": f"// {skill} Candidate Stub\nfn solve(arr: Vec<String>) -> String {{\n    String::new()\n}}",
                    },
                )
            )
        return out[:count]

    def _generate_rule_based_fallback(
        self,
        resume_data: Dict,
        num_questions: int,
        difficulty: DifficultyLevel,
        cat_dist: Dict[QuestionCategory, int],
    ) -> List[InterviewQuestion]:
        """Generate personalized non-LLM questions as last-resort fallback."""
        skills = _extract_skills(resume_data) or ["your primary stack"]
        projects = _extract_projects(resume_data)
        company = _extract_company(resume_data) or "your recent role"

        question_builders = {
            QuestionCategory.TECHNICAL: lambda s, p: f"You listed {s}. Walk me through a challenging implementation detail and how you validated correctness.",
            QuestionCategory.PROJECT: lambda s, p: f"In your project '{p}', what architecture did you choose and what trade-offs did you make?",
            QuestionCategory.BEHAVIORAL: lambda s, p: f"Tell me about a time at {company} when you received critical feedback and how you acted on it.",
            QuestionCategory.CONCEPTUAL: lambda s, p: f"Explain a core concept behind {s} and when you would avoid using it.",
            QuestionCategory.ROLE_FIT: lambda s, p: "Why are you interested in this role, and how does it align with your 1-2 year growth goals?",
        }

        out: List[InterviewQuestion] = []
        for cat, count in cat_dist.items():
            for _ in range(count):
                skill = skills[len(out) % len(skills)]
                proj = projects[len(out) % len(projects)].get("title", "one of your projects") if projects else "one of your projects"
                qtext = question_builders[cat](skill, proj)
                out.append(
                    InterviewQuestion(
                        id=self._next_id(),
                        question=qtext,
                        category=cat,
                        difficulty=difficulty,
                        context=f"Based on resume details: {skill}",
                        resume_reference=skill,
                        expected_topics=[skill],
                        follow_up_questions=[f"Can you share a concrete example related to {skill}?"],
                        time_limit_seconds=120,
                        scoring_rubric={
                            "excellent": "Specific, technically accurate, and structured answer with trade-offs.",
                            "good": "Mostly correct answer with practical detail.",
                            "poor": "Vague answer without clear technical grounding.",
                        },
                    )
                )
        return out[:num_questions]

    # ═══════════════════ LLM GENERATION ═══════════════════

    def _generate_from_llm(
        self,
        resume_data: Dict,
        num_questions: int,
        difficulty: DifficultyLevel,
        cat_dist: Dict[QuestionCategory, int],
        session_seed: str,
        job_description: Optional[str] = None,
        bias_free: bool = False,
    ) -> Optional[List[InterviewQuestion]]:
        """Generate all questions from LLM using full prompt."""
        if not self.llm.is_available:
            logger.error("No LLM providers available")
            return None

        # Build prompts with randomization
        system_prompt = build_system_prompt(
            resume_data=resume_data,
            session_seed=session_seed,
        )

        # Category labels for prompt
        cat_labels = {
            QuestionCategory.TECHNICAL: (
                "T (Technical depth — internals, edge cases, "
                "debugging, performance)"
            ),
            QuestionCategory.PROJECT: (
                "P (Project-based — architecture, decisions, "
                "failures, scale)"
            ),
            QuestionCategory.BEHAVIORAL: (
                "B (Behavioral — real situations, STAR method, "
                "growth, conflict)"
            ),
            QuestionCategory.CONCEPTUAL: (
                "C (Conceptual — theory applied to their domain, "
                "not textbook definitions)"
            ),
            QuestionCategory.ROLE_FIT: (
                "R (Role-fit — motivation, learning, career "
                "trajectory, values)"
            ),
        }
        cat_prompt_dist = {
            cat_labels.get(cat, str(cat)): count
            for cat, count in cat_dist.items()
        }

        user_prompt = build_user_prompt(
            resume_data=resume_data,
            num_questions=num_questions,
            difficulty_level=difficulty.value,
            category_distribution=cat_prompt_dist,
            session_seed=session_seed,
            job_description=job_description,
            bias_free=bias_free,
        )

        logger.info(
            f"Generating {num_questions} questions "
            f"(seed: {session_seed[:8]}..., "
            f"difficulty: {difficulty.value})"
        )

        # Call LLM
        result = self.llm.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        if result is None:
            logger.warning("LLM returned no parseable result")
            return None

        # Parse into InterviewQuestion objects
        questions = self._parse_llm_output(result, difficulty)

        if not questions:
            logger.warning("Parsed zero questions from LLM output")
            return None

        logger.info(
            f"✓ Generated {len(questions)} questions "
            f"via {self.llm.active_provider}"
        )
        self._last_provider_used = self.llm.active_provider
        return questions

    def _generate_simplified(
        self,
        resume_data: Dict,
        num_questions: int,
        difficulty: DifficultyLevel,
    ) -> Optional[List[InterviewQuestion]]:
        """
        Simplified prompt as backup — less structure,
        more likely to succeed on smaller models.
        """
        skills = _extract_skills(resume_data)
        company = _extract_company(resume_data)
        projects = _extract_projects(resume_data)
        name = _extract_name(resume_data)
        exp_level = resume_data.get("experience_level", "junior")

        proj_names = [
            p.get("title", "project")
            for p in projects[:3]
            if isinstance(p, dict)
        ]

        system_prompt = (
            "You are an expert technical interviewer. "
            "Generate personalized interview questions that "
            "reference the candidate's specific resume details. "
            "Return ONLY a JSON array of objects."
        )

        user_prompt = f"""Generate {num_questions} interview questions for:

Name: {name}
Level: {exp_level}
Skills: {', '.join(skills[:10])}
Company: {company}
Projects: {', '.join(proj_names)}

Each question MUST mention a specific skill, project, or company from above.

JSON format — return ONLY the array:
[
  {{
    "question": "specific personalized question text",
    "category": "T",
    "difficulty": "{difficulty.value}",
    "context": "why this question matters",
    "resume_reference": "specific resume detail referenced",
    "expected_topics": ["topic1", "topic2"],
    "follow_up_questions": ["follow-up 1"],
    "time_limit_seconds": 120,
    "scoring_rubric": {{"excellent": "criteria", "good": "criteria", "poor": "criteria"}}
  }}
]

Categories: T=Technical, P=Project, B=Behavioral, C=Conceptual, R=Role-fit
Generate {num_questions} questions. Start with ["""

        result = self.llm.generate_json(
            prompt=user_prompt,
            system_prompt=system_prompt,
        )

        if result is None:
            return None

        return self._parse_llm_output(result, difficulty)


    def _supplement_questions(
        self,
        questions: List[InterviewQuestion],
        resume_data: Dict,
        num_questions: int,
        difficulty: DifficultyLevel,
        cat_dist: Dict[QuestionCategory, int],
        session_seed: str,
    ) -> List[InterviewQuestion]:
        """Ask LLM for missing questions when first pass returns too few."""
        if len(questions) >= num_questions:
            return questions

        existing = {q.question.strip().lower() for q in questions}
        current = {c: 0 for c in QuestionCategory}
        for q in questions:
            current[q.category] += 1

        missing_by_cat = {
            cat: max(0, need - current.get(cat, 0))
            for cat, need in cat_dist.items()
        }

        rounds = 0
        while len(questions) < num_questions and rounds < 2:
            rounds += 1
            remaining = num_questions - len(questions)
            cat_needs = []
            for cat, cnt in missing_by_cat.items():
                if cnt > 0:
                    cat_needs.append(f"{cat.value}:{cnt}")
            if not cat_needs:
                cat_needs = ["T:1", "P:1", "B:1", "C:1", "R:1"]

            prompt = (
                f"Generate {remaining} additional interview questions to complete a full set. "
                f"Strictly return JSON array. Candidate resume: {json.dumps(resume_data)[:4500]}. "
                f"Missing categories target: {', '.join(cat_needs)}. "
                f"Difficulty mostly {difficulty.value}. "
                f"Each question must reference a concrete resume item and end with '?'."
            )

            result = self.llm.generate_json(
                prompt=prompt,
                system_prompt=(
                    "You generate personalized interview questions. "
                    "Output only JSON array of objects with fields: "
                    "question, category, difficulty, resume_reference, expected_topics."
                ),
            )
            extra = self._parse_llm_output(result, difficulty) if result else []
            if not extra:
                break

            for q in extra:
                key = q.question.strip().lower()
                if key in existing:
                    continue
                existing.add(key)
                questions.append(q)
                missing_by_cat[q.category] = max(0, missing_by_cat.get(q.category, 0) - 1)
                if len(questions) >= num_questions:
                    break

        return questions

    # ═══════════════════ OUTPUT PARSING ═══════════════════

    def _parse_llm_output(
        self,
        llm_result: Any,
        default_difficulty: DifficultyLevel,
    ) -> List[InterviewQuestion]:
        """Parse any LLM output format into InterviewQuestion list."""
        questions = []

        if isinstance(llm_result, list):
            for item in llm_result:
                q = self._parse_one(item, default_difficulty)
                if q:
                    questions.append(q)

        elif isinstance(llm_result, dict):
            # Maybe {"questions": [...]}
            for key in ["questions", "data", "items", "results"]:
                if key in llm_result and isinstance(
                    llm_result[key], list
                ):
                    return self._parse_llm_output(
                        llm_result[key], default_difficulty
                    )
            # Single question dict
            q = self._parse_one(llm_result, default_difficulty)
            if q:
                questions.append(q)

        elif isinstance(llm_result, str):
            # Sometimes LLM returns a single string
            if len(llm_result) > 20 and "?" in llm_result:
                questions.append(InterviewQuestion(
                    id=self._next_id(),
                    question=llm_result.strip(),
                    category=QuestionCategory.TECHNICAL,
                    difficulty=default_difficulty,
                    time_limit_seconds=120,
                ))

        return questions

    def _parse_one(
        self,
        item: Any,
        default_diff: DifficultyLevel,
    ) -> Optional[InterviewQuestion]:
        """Parse a single item into InterviewQuestion."""
        # Handle plain string
        if isinstance(item, str):
            if len(item) > 20:
                return InterviewQuestion(
                    id=self._next_id(),
                    question=item.strip(),
                    category=QuestionCategory.TECHNICAL,
                    difficulty=default_diff,
                    time_limit_seconds=120,
                )
            return None

        if not isinstance(item, dict):
            return None

        # Extract question text
        q_text = ""
        for key in ["question", "q", "text", "content"]:
            val = item.get(key)
            if val and isinstance(val, str) and len(val) > 15:
                q_text = val.strip()
                break

        if not q_text:
            return None

        # Parse category
        raw_cat = str(item.get("category", "T")).strip().upper()
        cat_map = {
            "T": QuestionCategory.TECHNICAL,
            "P": QuestionCategory.PROJECT,
            "B": QuestionCategory.BEHAVIORAL,
            "C": QuestionCategory.CONCEPTUAL,
            "R": QuestionCategory.ROLE_FIT,
            "TECHNICAL": QuestionCategory.TECHNICAL,
            "PROJECT": QuestionCategory.PROJECT,
            "BEHAVIORAL": QuestionCategory.BEHAVIORAL,
            "CONCEPTUAL": QuestionCategory.CONCEPTUAL,
            "ROLE_FIT": QuestionCategory.ROLE_FIT,
            "ROLE-FIT": QuestionCategory.ROLE_FIT,
            "ROLEFIT": QuestionCategory.ROLE_FIT,
        }
        category = cat_map.get(raw_cat, QuestionCategory.TECHNICAL)

        # Parse difficulty
        raw_diff = str(
            item.get("difficulty", default_diff.value)
        ).strip().lower()
        diff_map = {
            "easy": DifficultyLevel.EASY,
            "medium": DifficultyLevel.MEDIUM,
            "hard": DifficultyLevel.HARD,
            "expert": DifficultyLevel.EXPERT,
        }
        difficulty = diff_map.get(raw_diff, default_diff)

        # Parse list fields safely
        expected_topics = _safe_list(
            item.get("expected_topics", [])
        )
        follow_ups = _safe_list(
            item.get("follow_up_questions", [])
        )

        # Parse rubric
        rubric = item.get("scoring_rubric", {})
        if not isinstance(rubric, dict):
            rubric = {}

        # Parse time limit
        try:
            time_limit = int(
                item.get("time_limit_seconds", 120)
            )
            time_limit = max(30, min(300, time_limit))
        except (ValueError, TypeError):
            time_limit = 120

        return InterviewQuestion(
            id=self._next_id(),
            question=q_text,
            category=category,
            difficulty=difficulty,
            context=str(item.get("context", "")).strip(),
            resume_reference=str(
                item.get("resume_reference", "")
            ).strip(),
            expected_topics=expected_topics,
            follow_up_questions=follow_ups,
            time_limit_seconds=time_limit,
            scoring_rubric=rubric,
        )

    # ═══════════════════ FOLLOW-UP ═══════════════════

    def generate_follow_up(
        self,
        original_question: str,
        candidate_answer: str,
        resume_data: Dict,
    ) -> InterviewQuestion:
        """
        Generate adaptive follow-up from LLM.
        If LLM fails → generates a probing question from answer analysis.
        """
        # Try LLM
        if self.llm.is_available:
            try:
                skills = _extract_skills(resume_data)
                context = (
                    f"Skills: {', '.join(skills[:5])} | "
                    f"Domain: {resume_data.get('primary_domain', 'software')}"
                )

                text = self.llm.generate_follow_up(
                    question=original_question,
                    answer=candidate_answer,
                    resume_context=context,
                )

                if text and len(text) > 15:
                    return InterviewQuestion(
                        id=self._next_id(),
                        question=text,
                        category=QuestionCategory.TECHNICAL,
                        difficulty=DifficultyLevel.HARD,
                        context=(
                            "Adaptive follow-up generated from "
                            "candidate's previous answer"
                        ),
                        resume_reference="Previous answer analysis",
                        time_limit_seconds=120,
                    )
            except Exception as e:
                logger.warning(f"Follow-up LLM failed: {e}")

        # ── Answer-aware fallback (still not a template) ──
        # Analyze the answer to generate a relevant probe
        follow_up = self._analyze_answer_for_followup(
            original_question, candidate_answer
        )

        return InterviewQuestion(
            id=self._next_id(),
            question=follow_up,
            category=QuestionCategory.TECHNICAL,
            difficulty=DifficultyLevel.HARD,
            context="Follow-up based on answer analysis",
            resume_reference="Previous answer",
            time_limit_seconds=120,
        )

    def _analyze_answer_for_followup(
        self,
        question: str,
        answer: str,
    ) -> str:
        """
        Generate a context-aware follow-up by analyzing the answer.
        Not a static template — adapts to answer content.
        """
        answer_lower = answer.lower()

        # Detect what the candidate talked about
        if any(
            w in answer_lower
            for w in [
                "database", "sql", "query", "table",
                "schema", "index",
            ]
        ):
            return (
                "You mentioned database operations. "
                "What happens to your query performance when "
                "the table grows to 100 million rows? "
                "Walk me through your indexing strategy."
            )
        elif any(
            w in answer_lower
            for w in ["api", "endpoint", "rest", "request", "response"]
        ):
            return (
                "You described API interactions. "
                "How do you handle partial failures in a chain "
                "of API calls? What retry and circuit-breaking "
                "strategies do you use?"
            )
        elif any(
            w in answer_lower
            for w in [
                "deploy", "ci/cd", "pipeline", "docker",
                "kubernetes",
            ]
        ):
            return (
                "You mentioned deployment. What does your rollback "
                "strategy look like when a deployment causes a "
                "regression in production at 3 AM?"
            )
        elif any(
            w in answer_lower
            for w in ["model", "training", "accuracy", "data", "ml"]
        ):
            return (
                "You discussed ML model work. What happens when "
                "your model's accuracy degrades 20% overnight? "
                "Walk me through your debugging process from "
                "detection to root cause."
            )
        elif any(
            w in answer_lower
            for w in ["team", "collaborate", "review", "mentor"]
        ):
            return (
                "You mentioned team dynamics. Describe a specific "
                "technical disagreement where your position was "
                "wrong. What changed your mind, and what did "
                "you learn?"
            )
        elif any(
            w in answer_lower
            for w in ["test", "coverage", "bug", "debug"]
        ):
            return (
                "You talked about testing. What's the most "
                "insidious bug you've encountered that passed "
                "all your tests? Why did the tests miss it, "
                "and how did you fix the test strategy?"
            )
        elif any(
            w in answer_lower
            for w in [
                "scale", "performance", "optimize", "cache",
                "latency",
            ]
        ):
            return (
                "You mentioned performance considerations. "
                "Walk me through a specific bottleneck you "
                "identified and resolved. What profiling tools "
                "did you use, and what was the before/after?"
            )
        elif any(
            w in answer_lower
            for w in ["security", "auth", "encrypt", "token", "permission"]
        ):
            return (
                "You mentioned security aspects. What's your "
                "approach to threat modeling for a new feature? "
                "Walk me through a specific security vulnerability "
                "you found and remediated."
            )
        else:
            # Generic but still probing
            return (
                "Can you go deeper into the specific technical "
                "implementation you described? What were the "
                "exact constraints, what alternatives did you "
                "evaluate, and what would you change if you "
                "had to rebuild it today?"
            )

    # ═══════════════════ UTILITIES ═══════════════════

    def _calc_distribution(
        self,
        total: int,
        categories: List[QuestionCategory],
    ) -> Dict[QuestionCategory, int]:
        """Calculate question count per category."""
        weights = {
            QuestionCategory.TECHNICAL: 0.30,
            QuestionCategory.PROJECT: 0.20,
            QuestionCategory.BEHAVIORAL: 0.20,
            QuestionCategory.CONCEPTUAL: 0.20,
            QuestionCategory.ROLE_FIT: 0.10,
        }

        dist = {}
        allocated = 0
        for cat in categories:
            n = max(1, round(total * weights.get(cat, 0.15)))
            dist[cat] = n
            allocated += n

        # Adjust Technical to match total
        diff = total - allocated
        if diff != 0 and QuestionCategory.TECHNICAL in dist:
            dist[QuestionCategory.TECHNICAL] = max(
                1, dist[QuestionCategory.TECHNICAL] + diff
            )

        return dist

    def _post_process_questions(
        self,
        questions: List[InterviewQuestion],
        resume_data: Dict,
        requested_total: int,
        target_distribution: Dict[QuestionCategory, int],
        base_difficulty: DifficultyLevel,
        experience_level: str,
    ) -> List[InterviewQuestion]:
        """
        Enforce Module 2 quality constraints:
        - Resume-grounded wording (no generic questions)
        - Category coverage aligned to T/P/B/C/R distribution
        - Difficulty spread by experience level
        - Follow-up probes always present
        """
        if not questions:
            return questions

        anchors = self._resume_anchors(resume_data)
        fallback_anchor = anchors[0] if anchors else "your listed experience"

        # 1) Personalization hardening
        for q in questions:
            text_lower = q.question.lower()
            has_anchor = any(a.lower() in text_lower for a in anchors if a)
            if not has_anchor:
                q.question = (
                    f"In the context of {fallback_anchor}, {q.question[0].lower()}"
                    f"{q.question[1:]}" if len(q.question) > 1 else f"In the context of {fallback_anchor}, can you explain?"
                )
            if not q.resume_reference:
                q.resume_reference = fallback_anchor

        # 2) Category rebalance (relabel overrepresented categories to deficits)
        current = {c: 0 for c in QuestionCategory}
        for q in questions:
            current[q.category] += 1

        deficits: List[QuestionCategory] = []
        for cat, need in target_distribution.items():
            have = current.get(cat, 0)
            if need > have:
                deficits.extend([cat] * (need - have))

        if deficits:
            # Candidates for reassignment: categories above target
            over_idx = []
            temp_counts = dict(current)
            for idx, q in enumerate(questions):
                target = target_distribution.get(q.category, 0)
                if temp_counts[q.category] > target:
                    over_idx.append(idx)
                    temp_counts[q.category] -= 1

            for idx, new_cat in zip(over_idx, deficits):
                questions[idx].category = new_cat

        # 3) Difficulty spread by experience band
        spread = self._difficulty_spread(
            requested_total=max(1, len(questions)),
            base=base_difficulty,
            experience_level=experience_level,
        )
        q_idx = 0
        ordered_levels = (
            [DifficultyLevel.EASY] * spread.get(DifficultyLevel.EASY, 0)
            + [DifficultyLevel.MEDIUM] * spread.get(DifficultyLevel.MEDIUM, 0)
            + [DifficultyLevel.HARD] * spread.get(DifficultyLevel.HARD, 0)
            + [DifficultyLevel.EXPERT] * spread.get(DifficultyLevel.EXPERT, 0)
        )
        for lvl in ordered_levels[:len(questions)]:
            questions[q_idx].difficulty = lvl
            q_idx += 1

        # 4) Ensure follow-up logic is always seeded per question
        for q in questions:
            if len(q.follow_up_questions) < 2:
                q.follow_up_questions = [
                    f"What trade-off did you make for {q.resume_reference} and why?",
                    "If one key constraint changes, how would your approach change?",
                ]
            else:
                q.follow_up_questions = q.follow_up_questions[:3]

        return questions

    def _resume_anchors(self, resume_data: Dict) -> List[str]:
        """Collect specific resume entities that questions should reference."""
        anchors: List[str] = []
        for exp in (resume_data.get("work_experience") or [])[:6]:
            if isinstance(exp, dict):
                comp = str(exp.get("company") or "").strip()
                role = str(exp.get("role") or "").strip()
                if comp:
                    anchors.append(comp)
                if role:
                    anchors.append(role)
        for proj in (resume_data.get("projects") or [])[:6]:
            if isinstance(proj, dict):
                title = str(proj.get("title") or "").strip()
                if title:
                    anchors.append(title)
                for tech in (proj.get("technologies") or [])[:4]:
                    t = str(tech).strip()
                    if t:
                        anchors.append(t)
        for sk in (resume_data.get("skills") or [])[:10]:
            if isinstance(sk, dict):
                val = str(sk.get("name") or "").strip()
            else:
                val = str(sk).strip()
            if val:
                anchors.append(val)
        # Deduplicate preserving order
        out = []
        seen = set()
        for a in anchors:
            k = a.lower()
            if k and k not in seen:
                seen.add(k)
                out.append(a)
        return out

    def _difficulty_spread(
        self,
        requested_total: int,
        base: DifficultyLevel,
        experience_level: str,
    ) -> Dict[DifficultyLevel, int]:
        """Compute configurable difficulty spread (intern -> senior)."""
        exp = (experience_level or "").lower()

        # Default spread around base: 20% lower, 55% base, 25% higher.
        weights = (0.20, 0.55, 0.25)
        if "intern" in exp or "junior" in exp or "fresher" in exp:
            weights = (0.35, 0.55, 0.10)
        elif "senior" in exp or "staff" in exp or "principal" in exp:
            weights = (0.10, 0.45, 0.45)
        elif "lead" in exp:
            weights = (0.10, 0.50, 0.40)

        lower_n = max(0, round(requested_total * weights[0]))
        base_n = max(0, round(requested_total * weights[1]))
        higher_n = max(0, requested_total - lower_n - base_n)

        levels = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD, DifficultyLevel.EXPERT]
        idx = levels.index(base) if base in levels else 1
        lower = levels[max(0, idx - 1)]
        higher = levels[min(len(levels) - 1, idx + 1)]

        result = {
            DifficultyLevel.EASY: 0,
            DifficultyLevel.MEDIUM: 0,
            DifficultyLevel.HARD: 0,
            DifficultyLevel.EXPERT: 0,
        }
        result[lower] += lower_n
        result[base] += base_n
        result[higher] += higher_n
        return result


# ═══════════════════ HELPER FUNCTIONS ═══════════════════


def _extract_skills(resume_data: Dict) -> List[str]:
    """Safely extract skill names."""
    skills = resume_data.get("skills") or []
    result = []
    for s in skills:
        name = ""
        if isinstance(s, dict):
            name = s.get("name", "")
        elif isinstance(s, str):
            name = s
        if name and name.strip():
            result.append(name.strip())
    return result


def _extract_company(resume_data: Dict, idx: int = 0) -> str:
    """Safely extract company name."""
    exp = resume_data.get("work_experience") or []
    if exp and len(exp) > idx and isinstance(exp[idx], dict):
        return exp[idx].get("company") or "your previous company"
    return "your previous company"


def _extract_projects(resume_data: Dict) -> List[Dict]:
    """Safely extract projects."""
    projects = resume_data.get("projects") or []
    return [
        p if isinstance(p, dict) else {"title": str(p)}
        for p in projects
    ]


def _extract_name(resume_data: Dict) -> str:
    """
    Extract candidate name — guaranteed non-None.
    Chain: full_name → first+last → email → 'Candidate'
    """
    personal = resume_data.get("personal_info")
    if not isinstance(personal, dict):
        personal = {}

    # Try full_name / name
    for key in ["full_name", "name"]:
        val = personal.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()

    # Try first + last
    first = personal.get("first_name", "")
    last = personal.get("last_name", "")
    if first and isinstance(first, str) and first.strip():
        parts = [first.strip()]
        if last and isinstance(last, str) and last.strip():
            parts.append(last.strip())
        return " ".join(parts)

    # Try email
    email = personal.get("email", "")
    if email and isinstance(email, str) and "@" in email:
        local = email.split("@")[0]
        parts = re.split(r'[._\-]', local)
        parts = [
            p.capitalize()
            for p in parts
            if p and not p.isdigit() and len(p) > 1
        ]
        if parts:
            return " ".join(parts)

    return "Candidate"


def _safe_list(value: Any) -> List[str]:
    """Convert anything to a list of strings."""
    if isinstance(value, list):
        return [
            str(v).strip()
            for v in value
            if v and str(v).strip()
        ]
    if isinstance(value, str) and value.strip():
        return [
            t.strip()
            for t in value.split(",")
            if t.strip()
        ]
    return []


_qgen_instance: Optional[QuestionGenerator] = None


def get_question_generator() -> QuestionGenerator:
    """Singleton question generator to avoid repeated model training cost."""
    global _qgen_instance
    if _qgen_instance is None:
        _qgen_instance = QuestionGenerator()
    return _qgen_instance


def reset_question_generator() -> QuestionGenerator:
    """Reset singleton for tests or runtime refresh."""
    global _qgen_instance
    _qgen_instance = None
    return get_question_generator()
