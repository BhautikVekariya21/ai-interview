"""
Prompt engineering for interview question generation.

Anti-repetition strategies:
  1. Random interviewer persona per session
  2. UUID + timestamp seed in every prompt
  3. Randomly shuffled resume emphasis
  4. Variable question opening patterns
  5. Explicit anti-pattern blacklist
  6. Randomized difficulty spread instructions
"""

import random
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


# ═══════════════════ INTERVIEWER PERSONAS ═══════════════════

PERSONAS = [
    {
        "role": "Distinguished Engineer at a FAANG company",
        "style": (
            "You obsess over system design trade-offs, failure modes, "
            "and production-readiness. You ask 'What breaks when...' "
            "and 'Why not alternative X?' questions. You want candidates "
            "to defend architectural decisions with hard evidence."
        ),
    },
    {
        "role": "VP of Engineering at a Series-C startup",
        "style": (
            "You evaluate holistically — technical depth, communication, "
            "ownership mentality, and ability to ship under constraints. "
            "You ask scenario questions: 'Given ambiguous requirements "
            "and 2 weeks, how would you...' You hate vague answers."
        ),
    },
    {
        "role": "Principal ML Architect at a research lab",
        "style": (
            "You probe mathematical foundations behind ML tools. "
            "You ask 'Derive the loss function for...', "
            "'What happens to gradients when...', "
            "'Compare convergence of X vs Y.' "
            "You want proof the candidate understands algorithms, "
            "not just API calls."
        ),
    },
    {
        "role": "Staff SRE/Platform Engineer",
        "style": (
            "Every question has a reliability and observability angle. "
            "You ask about SLOs, incident postmortems, cascading failures, "
            "capacity planning. 'Your service hits 10K RPS and latency "
            "spikes to 5s — walk me through your debugging process.'"
        ),
    },
    {
        "role": "Security-focused Engineering Director",
        "style": (
            "You weave security into every technical question. "
            "'How do you prevent SSRF in this microservice?' "
            "'What is the threat model for this data pipeline?' "
            "You want candidates who think about attack surfaces "
            "automatically, not as an afterthought."
        ),
    },
    {
        "role": "Startup CTO who codes daily",
        "style": (
            "You value pragmatism, speed, and end-to-end ownership. "
            "You ask: 'Ship this feature in 3 days — what corners do "
            "you cut and what is non-negotiable?' You test whether "
            "candidates can make real engineering trade-offs."
        ),
    },
    {
        "role": "Tech Lead at a distributed-systems company",
        "style": (
            "You probe deeply into concurrency, consistency, "
            "distributed consensus, and network partitions. "
            "'What happens to your system during a network split?' "
            "'Explain exactly how your database handles concurrent writes.' "
            "You want candidates who understand CAP theorem viscerally."
        ),
    },
    {
        "role": "Senior Engineering Manager with 20 years experience",
        "style": (
            "You blend behavioral and technical seamlessly. "
            "'Tell me about a time your architecture decision was wrong. "
            "What was the technical signal you missed, and how did you "
            "course-correct?' You evaluate growth mindset and honesty."
        ),
    },
]

# ═══════════════════ QUESTION STARTERS ═══════════════════
# These are REGULAR strings (not f-strings).
# {company}, {tech} etc. are literal text — examples for the LLM.

QUESTION_STARTERS = [
    "In your role at {company}, you used {tech}. Walk me through...",
    "Your project '{project}' leverages {tech}. Explain the design decision behind...",
    "At {company}, you were responsible for {responsibility}. What would happen if...",
    "Given your {years} years with {tech}, describe a scenario where...",
    "You mention {tech} in your resume. Under what conditions would it fail, and...",
    "If I asked you to redesign '{project}' from scratch today...",
    "At {company}, imagine your {tech} service receives 100x traffic overnight...",
    "Your resume shows you used {tech} at {company}. What is the hardest bug...",
    "Suppose a junior developer asks you why {tech} over alternatives at {company}...",
    "In '{project}', what was the riskiest technical decision and...",
    "You have worked with {tech} extensively. Explain its internal mechanism for...",
    "At {company}, how did you ensure {tech} did not become a single point of failure...",
    "Walk me through the exact data flow in '{project}' from request to response...",
    "What would break in '{project}' if {tech} was removed? How would you migrate...",
    "Describe the worst production incident involving {tech} you have encountered...",
]

# ═══════════════════ ORDERING STRATEGIES ═══════════════════

ORDERING_STRATEGIES = [
    "Start with a project deep-dive to build rapport, escalate to hard technical internals, end with a thought-provoking architectural challenge.",
    "Open with an approachable technical question to establish baseline ability. Alternate technical/behavioral. End with a creative scenario question.",
    "Group by theme: all questions about one technology together, then the next. Increase difficulty within each group.",
    "Alternate: technical then behavioral then project then conceptual then role-fit. Spiral upward in difficulty.",
    "Start behavioral to relax the candidate, then hit with rapid-fire technical depth, end with project architecture.",
    "Lead with a 'what would you do if...' scenario, follow with deep technical probing, close with career vision.",
]

# ═══════════════════ EMPHASIS STRATEGIES ═══════════════════
# Regular strings — {old_tech} etc. are literal text for the LLM.

EMPHASIS_STRATEGIES = [
    "Focus 60 percent on their MOST RECENT role. Probe deeply: architecture, scale, team dynamics, failures.",
    "Focus on SKILL GAPS — if they list many backend skills but no frontend, ask frontend fundamentals. If no testing mentioned, probe testing philosophy.",
    "Focus on their STRONGEST skill. Go impossibly deep: internals, memory model, garbage collection, edge cases, performance characteristics.",
    "Focus on TRANSITIONS — why they switched technologies or roles, what they miss about previous stack, what surprised them about the new one.",
    "Focus on PROJECTS — every question MUST reference a specific project by name. Probe design, testing, deployment, monitoring.",
    "Focus on FAILURE MODES — for every technology they list, ask what breaks, what they would monitor, how they would debug at 3 AM.",
]

# ═══════════════════ BLACKLISTED QUESTIONS ═══════════════════
# Regular string — no f-string issues

BLACKLISTED_PATTERNS = """
NEVER generate these generic questions (or anything similar):
- "Tell me about yourself"
- "What is OOP / polymorphism / inheritance?"
- "What is REST API?"
- "What is a database?"
- "Explain MVC pattern"
- "What is version control?"
- "What are your strengths and weaknesses?"
- "Why do you want this job?"
- "What is Docker/Kubernetes?" (ask about THEIR specific usage instead)
- "Explain React/Angular/Vue" (ask about THEIR specific component decisions)
- "What is machine learning?" (ask about THEIR specific model choices)
- Any question answerable by a 5-minute Google search
- Any question that does not reference specific resume content
"""


# ═══════════════════ BUILD SYSTEM PROMPT ═══════════════════

def build_system_prompt(
    resume_data: Dict,
    session_seed: Optional[str] = None,
) -> str:
    """
    Build system prompt with randomized persona.

    IMPORTANT: This returns an f-string. Any literal curly braces
    that should appear in the output text MUST be double-escaped:
      {company}   → Python tries to evaluate variable 'company' → ERROR
      {{company}} → outputs literal {company} in the string → CORRECT
    """
    seed = session_seed or str(uuid.uuid4())
    rng = random.Random(hash(seed) % (2**32))

    persona = rng.choice(PERSONAS)
    ordering = rng.choice(ORDERING_STRATEGIES)
    emphasis = rng.choice(EMPHASIS_STRATEGIES)

    # Pick random question starters for variety instruction
    # IMPORTANT: These contain {company}, {tech}, etc. as literal text
    # We must NOT put them inside the f-string with .format() — just
    # include them as pre-formatted text.
    starters = rng.sample(
        QUESTION_STARTERS,
        min(6, len(QUESTION_STARTERS)),
    )
    starters_text = "\n".join(f"  - {s}" for s in starters)

    # ══════════════════════════════════════════════════════════
    # CRITICAL FIX: The starters_text contains {company}, {tech},
    # {project} etc. which are literal examples for the LLM.
    # If we put them inside an f-string, Python will try to
    # evaluate them as variables → NameError.
    #
    # SOLUTION: Build the prompt via string concatenation, NOT f-string,
    # for sections that contain literal braces. Or use .format() only
    # for the parts we control.
    # ══════════════════════════════════════════════════════════

    # Build each section separately to avoid f-string brace conflicts
    prompt_parts = []

    prompt_parts.append(
        f"You are conducting a REAL technical interview. "
        f"This is NOT a quiz. This is a conversation between "
        f"a senior engineer and a candidate."
    )
    prompt_parts.append("")
    prompt_parts.append(f"YOUR ROLE: {persona['role']}")
    prompt_parts.append(f"YOUR STYLE: {persona['style']}")
    prompt_parts.append("")
    prompt_parts.append(f"SESSION: {seed}")
    prompt_parts.append(f"TIME: {datetime.now(timezone.utc).isoformat()}")
    prompt_parts.append("")
    prompt_parts.append("ABSOLUTE RULES:")
    prompt_parts.append("")
    prompt_parts.append(
        "1. EVERY question MUST reference SPECIFIC details from "
        "the candidate resume:\n"
        "   - Exact project names (for example \"In your project 'TaskFlow'...\")\n"
        "   - Exact company names (for example \"At Google, you...\")\n"
        "   - Exact technologies with versions if available\n"
        "   - Specific responsibilities or achievements mentioned"
    )
    prompt_parts.append("")
    prompt_parts.append(
        "2. ZERO generic questions. If a question could apply to "
        "ANY candidate, REWRITE it to be specific to THIS candidate."
    )
    prompt_parts.append("")
    prompt_parts.append(
        "3. Questions must test UNDERSTANDING, not memorization:\n"
        "   - \"What breaks when...\" instead of \"What is...\"\n"
        "   - \"Why did you choose X over Y for project Z?\" instead of \"Explain X\"\n"
        "   - \"Walk me through debugging...\" instead of \"What is debugging?\""
    )
    prompt_parts.append("")
    prompt_parts.append(
        "4. Difficulty must match experience:\n"
        "   - Intern/Junior: Focus on fundamentals applied to THEIR projects\n"
        "   - Mid-level: Architecture decisions, trade-offs, debugging\n"
        "   - Senior: System design, failure modes, team impact, mentoring\n"
        "   - Expert: Novel problems, research-level depth, organizational impact"
    )
    prompt_parts.append("")
    prompt_parts.append(
        "5. Each question MUST start with a DIFFERENT opening pattern. "
        "Vary between:"
    )
    # starters_text contains {company}, {tech} etc. as literal text
    # Safe here because we're using append (no f-string interpretation)
    prompt_parts.append(starters_text)
    prompt_parts.append("")
    prompt_parts.append(
        "6. Include SCENARIO questions that force real-time thinking:\n"
        "   - \"Your database at [company name] is at 95 percent capacity "
        "on a Friday at 5 PM...\"\n"
        "   - \"A new regulation requires all PII encrypted at rest in 2 weeks...\"\n"
        "   - \"Your ML model accuracy drops 15 percent overnight...\""
    )
    prompt_parts.append("")
    prompt_parts.append(
        "7. At least a THIRD of questions must be un-Googleable probes that only "
        "someone who truly did the work could answer — forcing specific decisions, "
        "trade-offs, failures, and numbers from THEIR experience:\n"
        "   - \"What was the hardest bug in [project] and how did you isolate it?\"\n"
        "   - \"What did you measure before and after [specific change]?\"\n"
        "   - \"What would you do differently if you rebuilt [project] today?\"\n"
        "   These resist rehearsed or AI-fed answers and reveal genuine ownership."
    )
    prompt_parts.append("")
    prompt_parts.append(BLACKLISTED_PATTERNS)
    prompt_parts.append("")
    prompt_parts.append(f"QUESTION ORDERING: {ordering}")
    prompt_parts.append(f"EMPHASIS: {emphasis}")
    prompt_parts.append("")
    prompt_parts.append("OUTPUT FORMAT:")
    prompt_parts.append("")
    prompt_parts.append(
        "Return ONLY a valid JSON array. No markdown. No explanation. "
        "No preamble.\nStart your response with [ and end with ]"
    )
    prompt_parts.append("")
    prompt_parts.append(
        'Each element must be a JSON object with these exact keys:\n'
        '{\n'
        '    "question": "The full, specific, personalized question text.",\n'
        '    "category": "T|P|B|C|R",\n'
        '    "difficulty": "easy|medium|hard|expert",\n'
        '    "context": "Why this question matters for this specific candidate",\n'
        '    "resume_reference": "Exact resume detail this question references",\n'
        '    "expected_topics": ["topic1", "topic2", "topic3", "topic4"],\n'
        '    "follow_up_questions": ["deeper follow-up 1", "deeper follow-up 2"],\n'
        '    "time_limit_seconds": 120,\n'
        '    "scoring_rubric": {\n'
        '        "excellent": "What makes a 90+ answer with specific criteria",\n'
        '        "good": "What makes a 60-89 answer",\n'
        '        "poor": "Red flags that indicate below 40"\n'
        '    }\n'
        '}'
    )
    prompt_parts.append("")
    prompt_parts.append(
        "Categories: T=Technical depth, P=Project-based, "
        "B=Behavioral, C=Conceptual/theory, R=Role-fit"
    )
    prompt_parts.append("")
    prompt_parts.append(
        "Do NOT write live-coding problems. These are spoken-answer questions "
        "only. The coding round is drawn separately from a vetted problem bank "
        "so that submissions can be executed and graded against real test cases."
    )

    return "\n".join(prompt_parts)


# ═══════════════════ BUILD USER PROMPT ═══════════════════

def build_user_prompt(
    resume_data: Dict,
    num_questions: int = 15,
    difficulty_level: str = "medium",
    category_distribution: Optional[Dict[str, int]] = None,
    session_seed: Optional[str] = None,
    job_description: Optional[str] = None,
    bias_free: bool = False,
) -> str:
    """
    Build user prompt with full resume context, randomly emphasized.

    Same f-string escaping rules apply here.
    """
    seed = session_seed or str(uuid.uuid4())
    rng = random.Random(hash(seed + "user") % (2**32))

    # ── Extract everything ──
    # ── Extract context pieces safely ──
    name = str(resume_data.get("name", "Candidate")).strip()
    if not name or name.lower() == "unknown":
        # Fallback to personal_info block if present
        pi = resume_data.get("personal_info", {})
        if isinstance(pi, dict):
            name = str(pi.get("full_name", "Candidate")).strip()

    if bias_free:
        name = "Candidate"
    
    exp_level = str(resume_data.get("experience_level", "Mid")).strip()
    domain = str(resume_data.get("inferred_domain", "Software Engineering")).strip()
    total_years = resume_data.get("total_years_experience", 0)

    education = resume_data.get("education") or []
    experience = resume_data.get("work_experience") or []
    skills = resume_data.get("skills") or []
    projects = resume_data.get("projects") or []
    certs = resume_data.get("certifications") or []
    achievements = resume_data.get("achievements") or []

    # ── Normalize skills ──
    skill_names = []
    for s in skills:
        if isinstance(s, dict):
            skill_names.append(s.get("name", str(s)))
        else:
            skill_names.append(str(s))

    # ── Shuffle for variety ──
    shuffled_skills = list(skill_names)
    rng.shuffle(shuffled_skills)
    shuffled_projects = list(projects)
    rng.shuffle(shuffled_projects)
    shuffled_exp = list(experience)
    rng.shuffle(shuffled_exp)

    # ── Format sections ──
    edu_text = _fmt_education(education)
    exp_text = _fmt_experience(shuffled_exp)
    proj_text = _fmt_projects(shuffled_projects)
    cert_text = _fmt_list(certs, "certifications")
    achv_text = _fmt_list(achievements, "achievements")

    # ── Category distribution ──
    # Verbal questions only. Live-coding problems are selected from the vetted
    # problem bank (see app.services.coding_problem_selector) because a problem
    # invented here would carry no test cases and could not be graded.
    if not category_distribution:
        category_distribution = {
            "T (Technical depth — internals, edge cases, debugging, performance)": max(
                1, round(num_questions * 0.35)
            ),
            "P (Project-based — architecture, decisions, failures, scale)": max(
                1, round(num_questions * 0.25)
            ),
            "B (Behavioral — real situations, STAR method, growth, conflict)": max(
                1, round(num_questions * 0.20)
            ),
            "C (Conceptual — theory applied to their domain, not textbook definitions)": max(
                1, round(num_questions * 0.12)
            ),
            "R (Role-fit — motivation, learning, career trajectory, values)": max(
                1, round(num_questions * 0.08)
            ),
        }

    cat_text = "\n".join(
        f"    {k}: {v} questions" for k, v in category_distribution.items()
    )

    # ── Random emphasis picks ──
    highlighted_skills = rng.sample(
        shuffled_skills, min(4, len(shuffled_skills))
    ) if shuffled_skills else ["general software engineering"]

    emphasis_note = (
        f"THIS SESSION: Pay special attention to "
        f"{', '.join(highlighted_skills)}. "
        f"Ask about internal mechanisms, failure modes, "
        f"performance characteristics, and real-world gotchas."
    )

    # ── Project highlight ──
    proj_highlight = ""
    if shuffled_projects:
        focus_proj = shuffled_projects[0]
        if isinstance(focus_proj, dict):
            proj_name = focus_proj.get("title", "their project")
            proj_techs = focus_proj.get("technologies", [])
            proj_tech_str = (
                ", ".join(proj_techs[:5]) if proj_techs else "not specified"
            )
            proj_highlight = (
                f"DEEP DIVE PROJECT: '{proj_name}' "
                f"(technologies: {proj_tech_str}). "
                f"Ask at least 2 questions specifically about this project "
                f"architecture, testing, deployment, and failure handling."
            )

    # ── Build the prompt ──
    # All variables here are Python variables defined above.
    # No literal curly braces needed in the body text.

    jd_text = f"\nTARGET JOB DESCRIPTION:\n{job_description}\n\nALIGNMENT REQUIREMENT:\nEnsure the questions map the candidate's existing experience strictly against the requirements of this Job Description.\n" if job_description and job_description.strip() else ""

    return f"""CANDIDATE RESUME

CANDIDATE: {name}
EXPERIENCE LEVEL: {exp_level} ({total_years} years total)
PRIMARY DOMAIN: {domain}

EDUCATION:
{edu_text or '  Not provided'}

WORK EXPERIENCE:
{exp_text or '  Not provided'}

TECHNICAL SKILLS:
  {', '.join(shuffled_skills) if shuffled_skills else 'Not provided'}

PROJECTS:
{proj_text or '  Not provided'}

CERTIFICATIONS:
{cert_text or '  Not provided'}

ACHIEVEMENTS:
{achv_text or '  Not provided'}
{jd_text}
GENERATION INSTRUCTIONS:

{emphasis_note}

{proj_highlight}

Generate exactly {num_questions} interview questions.

DIFFICULTY CALIBRATION — read this before writing anything.

A question's difficulty is set by WHAT THE ANSWER REQUIRES, never by how the
question is worded. Adding "in depth" or "at scale" to an easy question does not
make it hard; it makes it a padded easy question. Use these definitions:

  easy — Recall and description. Answerable by anyone who has genuinely used the
    technology, from memory, in about a minute. One concept, no trade-offs.
    Verifiable as easy: the answer is a fact or a definition applied to their work.
    Example shape: "What does <tool they used> do for you in <their project>?"

  medium — Application and comparison. Requires choosing between two viable
    options and justifying the choice, or explaining a mechanism one level below
    the API they used. Two or three interacting concepts. The candidate must have
    actually built something to answer well; reading documentation is not enough.
    Example shape: "Why <approach A> rather than <approach B> in <their project>,
    and what did that cost you?"

  hard — Diagnosis and design under constraint. Requires reasoning about failure
    modes, concurrency, consistency, or performance limits that only appear in
    production. There is no single correct answer; a strong answer names the
    trade-off explicitly and defends it. Three or more concepts interacting.
    Example shape: "<Their system> is losing writes under <specific condition>.
    Walk me through how you would find the cause and what you would change."

  expert — Novel design or deep internals. Requires knowledge of how the tool is
    implemented, or designing a system with conflicting requirements where every
    option is wrong in some way. Answerable only by someone who has operated this
    at scale and has been burned by it.

SELF-CHECK before you emit each question — apply honestly:
  1. Could a candidate who only read the docs answer this? If yes, it is easy.
     Do not label it medium.
  2. Does answering require naming a trade-off or a failure mode? If not, it is
     not hard, regardless of how complex the wording is.
  3. Does the difficulty field match what the answer actually demands? If they
     disagree, change the field, not the question.

Base difficulty: {difficulty_level}
Difficulty spread across the {num_questions} questions:
  - 15 percent one level BELOW base (warm-up, asked first)
  - 55 percent AT base level
  - 30 percent one level ABOVE base (challenge, asked last)
Order the questions so difficulty ramps up. Never open with the hardest question.

Category distribution:
{cat_text}

UNIQUENESS ENFORCEMENT:
  Session seed: {seed}
  This seed MUST produce questions that are completely different
  from any other seed. Vary: question angle, opening words,
  specific resume detail referenced, scenario framing.

  Every question must be answerable ONLY by THIS candidate
  who has THIS specific resume. If you remove the candidate
  name and resume, the questions should make no sense.

Return ONLY a valid JSON array of {num_questions} question objects.
No markdown fences. No explanation. Start with [ and end with ]
["""


# ═══════════════════ FOLLOW-UP PROMPT ═══════════════════

def build_follow_up_prompt(
    original_question: str,
    candidate_answer: str,
    resume_context: str = "",
) -> str:
    """
    Build prompt for adaptive follow-up generation.
    This is a regular string concatenation — no f-string escaping issues.
    """
    parts = [
        "You are a senior interviewer mid-conversation with a candidate.",
        "",
        f"PREVIOUS QUESTION: {original_question}",
        "",
        f"CANDIDATE ANSWER: {candidate_answer}",
    ]

    if resume_context:
        parts.append("")
        parts.append(f"RESUME CONTEXT: {resume_context}")

    parts.extend([
        "",
        "Based on their answer, generate ONE follow-up question that does ONE of these:",
        "1. CHALLENGES a specific claim: 'You said X. But what about edge case Y?'",
        "2. PROBES DEEPER: 'You mentioned Z. Walk me through the exact implementation.'",
        "3. TESTS UNDERSTANDING: 'If we changed constraint A, how would your approach change?'",
        "4. EXPOSES GAPS: 'You did not mention testing/monitoring/security. How did you handle that?'",
        "5. CONNECTS TO RESUME: 'Given your experience with that technology, how does it relate to what you just described?'",
        "",
        "The follow-up must be IMPOSSIBLE to answer with a generic response.",
        "It must force the candidate to demonstrate real understanding.",
        "",
        "Return ONLY the question text. No explanation. No numbering. Just the question.",
    ])

    return "\n".join(parts)


# ═══════════════════ HELPER FORMATTERS ═══════════════════

def _safe_name(personal: Dict) -> str:
    """Extract name with guaranteed non-None return."""
    # Try full_name or name
    for key in ["full_name", "name"]:
        val = personal.get(key)
        if val and isinstance(val, str) and val.strip():
            return val.strip()

    # Try first_name + last_name
    first = personal.get("first_name", "")
    last = personal.get("last_name", "")
    if first and isinstance(first, str) and first.strip():
        parts = [first.strip()]
        if last and isinstance(last, str) and last.strip():
            parts.append(last.strip())
        return " ".join(parts)

    # Try deriving from email
    email = personal.get("email", "")
    if email and "@" in str(email):
        import re
        local = str(email).split("@")[0]
        parts = re.split(r'[._\-]', local)
        parts = [
            p.capitalize()
            for p in parts
            if p and not p.isdigit() and len(p) > 1
        ]
        if parts:
            return " ".join(parts)

    return "Candidate"


def _fmt_education(education: List) -> str:
    """Format education entries for the prompt."""
    if not education:
        return ""
    lines = []
    for e in education:
        if isinstance(e, dict):
            parts = []
            if e.get("degree"):
                parts.append(str(e["degree"]))
            if e.get("field") or e.get("major"):
                parts.append(
                    f"in {e.get('field') or e.get('major')}"
                )
            if e.get("institution"):
                parts.append(f"from {e['institution']}")
            if e.get("gpa"):
                parts.append(f"(GPA: {e['gpa']})")
            if e.get("graduation_year"):
                parts.append(f"[{e['graduation_year']}]")
            lines.append(f"  - {' '.join(parts)}")
        else:
            lines.append(f"  - {e}")
    return "\n".join(lines)


def _fmt_experience(experience: List) -> str:
    """Format work experience entries for the prompt."""
    if not experience:
        return ""
    lines = []
    for exp in experience:
        if isinstance(exp, dict):
            role = exp.get("role") or exp.get("title", "Role")
            company = exp.get("company", "Company")
            duration = exp.get("duration", "")
            header = f"  * {role} at {company}"
            if duration:
                header += f" ({duration})"
            lines.append(header)

            # Responsibilities
            for field in [
                "responsibilities", "description", "duties"
            ]:
                items = exp.get(field, [])
                if isinstance(items, list):
                    for r in items[:4]:
                        lines.append(f"      - {r}")
                elif isinstance(items, str) and items:
                    lines.append(f"      - {items}")

            # Technologies used in this role
            techs = exp.get("technologies", [])
            if techs:
                lines.append(
                    f"      Tech: {', '.join(techs[:8])}"
                )
        else:
            lines.append(f"  * {exp}")
    return "\n".join(lines)


def _fmt_projects(projects: List) -> str:
    """Format project entries for the prompt."""
    if not projects:
        return ""
    lines = []
    for p in projects:
        if isinstance(p, dict):
            title = p.get("title", "Project")
            techs = p.get("technologies", [])
            desc = p.get("description", "")
            header = f"  > {title}"
            if techs:
                header += f" [{', '.join(techs[:6])}]"
            lines.append(header)
            if desc:
                # Truncate long descriptions
                desc_str = str(desc)[:250]
                lines.append(f"      {desc_str}")
        else:
            lines.append(f"  > {p}")
    return "\n".join(lines)


def _fmt_list(items: List, label: str) -> str:
    """Format a generic list (certs, achievements, etc.)."""
    if not items:
        return ""
    lines = []
    for item in items:
        if isinstance(item, dict):
            name = item.get("name", str(item))
            lines.append(f"  - {name}")
        else:
            lines.append(f"  - {item}")
    return "\n".join(lines)
