"""
FULL TERMINAL TEST — Prints every generated question with LLM details.
Run: python tests/test_print_questions.py

This script:
  1. Parses a sample resume
  2. Generates interview questions
  3. Prints EVERY question in full on terminal
  4. Shows which LLM provider was used
  5. Shows raw LLM response
"""

import os
import sys
import json
import asyncio
import time

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ==================== COLORS FOR TERMINAL ====================

class C:
    """ANSI colors for pretty terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    MAGENTA = '\033[35m'

def print_header(text, char="="):
    width = 80
    print(f"\n{C.BOLD}{C.CYAN}{char * width}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{text.center(width)}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{char * width}{C.END}")

def print_section(text):
    print(f"\n{C.BOLD}{C.YELLOW}{'─' * 60}{C.END}")
    print(f"{C.BOLD}{C.YELLOW}  {text}{C.END}")
    print(f"{C.BOLD}{C.YELLOW}{'─' * 60}{C.END}")

def print_ok(text):
    print(f"  {C.GREEN}✓{C.END} {text}")

def print_warn(text):
    print(f"  {C.YELLOW}⚠{C.END} {text}")

def print_err(text):
    print(f"  {C.RED}✗{C.END} {text}")

def print_info(label, value):
    print(f"  {C.GRAY}{label}:{C.END} {C.WHITE}{value}{C.END}")

# ==================== SAMPLE RESUME ====================

SAMPLE_RESUME = """
Bhautik Vekariya
bhautikvekariya1123@gmail.com
+91-9876543210
Ahmedabad, India
linkedin.com/in/bhautik-vekariya
github.com/bhautikv

PROFESSIONAL SUMMARY
Passionate data science enthusiast with hands-on experience in
machine learning, deep learning, and natural language processing.
Built multiple end-to-end ML pipelines and deployed models to production.

EDUCATION
Bachelor of Computer Applications (BCA)
Gujarat University
CGPA: 8.5/10.0
2020 - 2023

TECHNICAL SKILLS
Languages: Python, R, SQL, JavaScript
ML/AI: PyTorch, PyTorch Lightning, scikit-learn, Hugging Face, Pandas, NumPy, OpenCV
Tools: Docker, Git, Jupyter Notebook, VS Code, Postman
Databases: PostgreSQL, MongoDB, Redis
Cloud: AWS, Google Cloud
Frameworks: Flask, FastAPI, Django

WORK EXPERIENCE

Data Science Intern at TechCorp Solutions
Ahmedabad, India | June 2022 - December 2022
• Built customer churn prediction model with 94% accuracy using XGBoost
• Developed automated data pipeline processing 500K+ records daily
• Created interactive dashboards using Plotly and Streamlit
• Collaborated with cross-functional team of 8 engineers

PROJECTS

Sentiment Analysis Dashboard
Built a real-time sentiment analysis tool using BERT and Flask.
Analyzed 100K+ tweets with 92% accuracy. Deployed on AWS EC2.
Technologies: Python, PyTorch, Flask, Redis, Docker

Image Classification API
Created a REST API for image classification using ResNet50.
Handles 1000+ requests/minute with 95% accuracy.
Technologies: Python, PyTorch, FastAPI, Docker, AWS S3

Recommendation Engine
Built collaborative filtering recommendation system for e-commerce.
Increased user engagement by 35%.
Technologies: Python, scikit-learn, PostgreSQL, Redis

CERTIFICATIONS
AWS Certified Machine Learning - Specialty (2023)
AWS Cloud Practitioner (2022)
Deep Learning Specialization - Coursera (2022)

ACHIEVEMENTS
• Winner, Smart India Hackathon 2022
• Published paper on NLP techniques at ICML Workshop 2023
• Top 5% on Kaggle — Expert rank in NLP competitions
• Open source contributor — 200+ GitHub stars
"""


# ==================== TEST FUNCTIONS ====================


async def test_full_pipeline():
    """Full pipeline test with detailed terminal output."""

    print_header("AI INTERVIEW SYSTEM — FULL PIPELINE TEST")

    # ──────────────── STEP 1: LLM STATUS ────────────────
    print_section("STEP 1: LLM Provider Status")

    from app.services.llm_service import get_llm
    llm = get_llm()
    status = llm.get_status()

    print_info("Available", status["available"])
    print_info("Active Provider", status["active_provider"] or "NONE")
    print_info("Active Model", status["active_model"] or "NONE")
    print_info("Fallback Chain", " → ".join(status["fallback_order"]) or "none")

    for provider, info in status["providers"].items():
        marker = f"{C.GREEN}●{C.END}" if info["healthy"] else f"{C.RED}○{C.END}"
        print(f"    {marker} {provider}: failures={info['failures']}")

    # ──────────────── STEP 1b: RAW LLM TEST ────────────────
    print_section("STEP 1b: Raw LLM Test")

    if llm.is_available:
        print(f"  {C.GRAY}Sending test prompt to LLM...{C.END}")
        start = time.time()
        raw_response = llm.generate(
            "Respond with exactly: 'LLM is working correctly'",
            temperature=0.1,
            max_tokens=50,
        )
        elapsed = time.time() - start

        if raw_response:
            print_ok(f"LLM responded in {elapsed:.2f}s")
            print(f"  {C.CYAN}Response: \"{raw_response}\"{C.END}")
            print_info("Provider used", llm.active_provider)
        else:
            print_err("LLM returned None — all providers failed")
    else:
        print_warn("No LLM available — will use template-only mode")

    # ──────────────── STEP 2: PARSE RESUME ────────────────
    print_section("STEP 2: Resume Parsing")

    from app.services.resume_parser import ResumeParser
    parser = ResumeParser()

    start = time.time()
    parsed = await parser.parse(SAMPLE_RESUME.encode("utf-8"), "Bhautik_Vekariya.txt")
    parse_time = time.time() - start

    print_ok(f"Parsed in {parse_time:.2f}s")
    print_info("Name", parsed.personal_info.full_name or "NOT FOUND")
    print_info("Email", parsed.personal_info.email or "NOT FOUND")
    print_info("Phone", parsed.personal_info.phone or "NOT FOUND")
    print_info("Location", parsed.personal_info.location or "NOT FOUND")
    print_info("LinkedIn", parsed.personal_info.linkedin_url or "NOT FOUND")
    print_info("GitHub", parsed.personal_info.github_url or "NOT FOUND")

    print(f"\n  {C.BOLD}Education:{C.END}")
    for edu in parsed.education:
        print(f"    • {edu.degree or '?'} — {edu.institution}")
        if edu.gpa:
            print(f"      GPA: {edu.gpa}/{edu.gpa_scale}")

    print(f"\n  {C.BOLD}Experience:{C.END}")
    for exp in parsed.work_experience:
        print(f"    • {exp.role} at {exp.company}")
        if exp.responsibilities:
            for r in exp.responsibilities[:2]:
                print(f"      - {r[:80]}...")

    print(f"\n  {C.BOLD}Skills ({len(parsed.skills)}):{C.END}")
    by_cat = {}
    for s in parsed.skills:
        by_cat.setdefault(s.category, []).append(s.name)
    for cat, names in by_cat.items():
        print(f"    {C.CYAN}{cat}:{C.END} {', '.join(names)}")

    print(f"\n  {C.BOLD}Projects ({len(parsed.projects)}):{C.END}")
    for proj in parsed.projects:
        print(f"    • {proj.title}")
        if proj.description:
            print(f"      {proj.description[:80]}...")
        if proj.technologies:
            print(f"      Tech: {', '.join(proj.technologies)}")

    print(f"\n  {C.BOLD}Certifications ({len(parsed.certifications)}):{C.END}")
    for cert in parsed.certifications:
        print(f"    • {cert.name}")

    print(f"\n  {C.BOLD}Metadata:{C.END}")
    print_info("Experience Level", parsed.experience_level.value)
    print_info("Total Years", f"{parsed.total_experience_years:.1f}")
    print_info("Primary Domain", parsed.primary_domain or "unknown")
    print_info("Confidence", f"{parsed.overall_parse_confidence:.2f}")
    print_info("Top Skills", ", ".join(parsed.top_skills[:8]))

    # ──────────────── STEP 3: GENERATE QUESTIONS ────────────────
    print_section("STEP 3: Question Generation")

    from app.services.question_generator import QuestionGenerator
    qgen = QuestionGenerator()

    resume_dict = parsed.model_dump()

    print(f"  {C.GRAY}Generating 15 questions...{C.END}")
    start = time.time()
    question_set = qgen.generate(resume_dict, num_questions=15)
    gen_time = time.time() - start

    print_ok(f"Generated {question_set.total_questions} questions in {gen_time:.2f}s")
    print_info("Candidate Name", question_set.candidate_name)
    print_info("Experience Level", question_set.experience_level)
    print_info("Primary Domain", question_set.primary_domain)
    print_info("Base Difficulty", question_set.base_difficulty)
    print_info("Estimated Duration", f"{question_set.estimated_duration_minutes} minutes")
    print_info("LLM Provider Used", question_set.llm_provider or "templates-only")
    print_info("Generated At", question_set.generated_at)

    print(f"\n  {C.BOLD}Category Distribution:{C.END}")
    cat_names = {
        "T": "Technical", "P": "Project", "B": "Behavioral",
        "C": "Conceptual", "R": "Role-fit",
    }
    for cat_code, count in question_set.categories_distribution.items():
        name = cat_names.get(cat_code, cat_code)
        bar = "█" * count + "░" * (15 - count)
        print(f"    {name:15s} [{bar}] {count}")

    # ──────────────── STEP 4: PRINT ALL QUESTIONS ────────────────
    print_header("GENERATED INTERVIEW QUESTIONS", "─")

    for i, q in enumerate(question_set.questions):
        cat_name = cat_names.get(q.category.value, "Other")

        # Color by category
        cat_colors = {
            "T": C.BLUE, "P": C.GREEN, "B": C.YELLOW,
            "C": C.MAGENTA, "R": C.CYAN,
        }
        color = cat_colors.get(q.category.value, C.WHITE)

        # Difficulty badge
        diff_badges = {
            "easy": f"{C.GREEN}EASY{C.END}",
            "medium": f"{C.YELLOW}MEDIUM{C.END}",
            "hard": f"{C.RED}HARD{C.END}",
            "expert": f"{C.RED}{C.BOLD}EXPERT{C.END}",
        }
        diff_badge = diff_badges.get(q.difficulty.value, q.difficulty.value)

        print(f"\n{C.BOLD}{'─' * 80}{C.END}")
        print(
            f"  {C.BOLD}Q{q.id:02d}{C.END} "
            f"[{color}{cat_name}{C.END}] "
            f"[{diff_badge}] "
            f"{C.GRAY}({q.time_limit_seconds}s){C.END}"
        )
        print(f"{'─' * 80}")

        # Print the full question
        print(f"\n  {C.WHITE}{C.BOLD}{q.question}{C.END}")

        # Context
        if q.context:
            print(f"\n  {C.GRAY}Context: {q.context}{C.END}")

        # Resume reference
        if q.resume_reference:
            print(f"  {C.GRAY}Resume Ref: {q.resume_reference}{C.END}")

        # Expected topics
        if q.expected_topics:
            topics_str = ", ".join(q.expected_topics[:5])
            print(f"  {C.CYAN}Expected Topics: {topics_str}{C.END}")

        # Follow-up questions
        if q.follow_up_questions:
            print(f"  {C.YELLOW}Follow-ups:{C.END}")
            for fu in q.follow_up_questions[:3]:
                print(f"    → {fu}")

    # ──────────────── STEP 5: TEST LLM ENHANCEMENT ────────────────
    print_section("STEP 5: LLM Enhancement Details")

    if llm.is_available:
        print(f"  {C.GRAY}Testing direct LLM question enhancement...{C.END}")

        test_prompt = f"""You are an expert technical interviewer.
Candidate: {question_set.candidate_name}, {question_set.experience_level}-level {question_set.primary_domain} engineer
Skills: {', '.join(parsed.top_skills[:8])}

Generate 3 highly specific, personalized interview questions.
Return ONLY a JSON array of question strings.

Example format:
["Question 1 text here", "Question 2 text here", "Question 3 text here"]"""

        print(f"\n  {C.GRAY}Prompt sent to LLM:{C.END}")
        print(f"  {C.GRAY}{'─' * 60}{C.END}")
        for line in test_prompt.split('\n'):
            print(f"  {C.GRAY}  {line}{C.END}")
        print(f"  {C.GRAY}{'─' * 60}{C.END}")

        start = time.time()
        raw_result = llm.generate(test_prompt, temperature=0.7)
        elapsed = time.time() - start

        print(f"\n  {C.BOLD}Raw LLM Response ({elapsed:.2f}s):{C.END}")
        print(f"  {C.GRAY}Provider: {llm.active_provider}{C.END}")
        print(f"  {C.GRAY}{'─' * 60}{C.END}")

        if raw_result:
            print(f"  {C.GREEN}{raw_result}{C.END}")

            # Try to parse as JSON
            print(f"\n  {C.BOLD}Parsed JSON:{C.END}")
            parsed_json = llm.generate_json(test_prompt)
            if parsed_json:
                if isinstance(parsed_json, list):
                    for j, q_text in enumerate(parsed_json):
                        print(f"\n  {C.CYAN}LLM Q{j+1}:{C.END} {q_text}")
                else:
                    print(f"  {json.dumps(parsed_json, indent=2)}")
                print_ok("LLM JSON parsing successful")
            else:
                print_warn("JSON parsing failed — questions came from templates")
        else:
            print_err("LLM returned empty response")
            print_warn("All questions are template-based (still good!)")
    else:
        print_warn("No LLM available — all questions are template-based")
        print_info("Note", "Questions are still personalized using resume data")

    # ──────────────── STEP 6: TEST FOLLOW-UP ────────────────
    print_section("STEP 6: Follow-up Question Generation")

    if question_set.questions:
        original_q = question_set.questions[0].question
        fake_answer = (
            "I used Python's asyncio with aiohttp for concurrent API calls. "
            "The main challenge was handling rate limiting from external APIs. "
            "I implemented exponential backoff with jitter."
        )

        print(f"  {C.BOLD}Original Question:{C.END}")
        print(f"  {original_q[:100]}...")
        print(f"\n  {C.BOLD}Simulated Answer:{C.END}")
        print(f"  {fake_answer}")

        start = time.time()
        follow_up = qgen.generate_follow_up(
            original_question=original_q,
            candidate_answer=fake_answer,
            resume_data=resume_dict,
        )
        elapsed = time.time() - start

        print(f"\n  {C.BOLD}Follow-up Question ({elapsed:.2f}s):{C.END}")
        print(f"  {C.GREEN}{follow_up.question}{C.END}")
        print_info("Source", follow_up.context)

        if "LLM" in follow_up.context:
            print_ok("Follow-up generated by LLM ✓")
        else:
            print_warn("Follow-up from template (LLM unavailable)")

    # ──────────────── STEP 7: FULL JSON OUTPUT ────────────────
    print_section("STEP 7: Full JSON Output")

    full_output = {
        "candidate": {
            "name": question_set.candidate_name,
            "email": parsed.personal_info.email,
            "level": question_set.experience_level,
            "domain": question_set.primary_domain,
            "years": parsed.total_experience_years,
            "top_skills": parsed.top_skills[:8],
        },
        "config": {
            "total_questions": question_set.total_questions,
            "difficulty": question_set.base_difficulty,
            "duration_minutes": question_set.estimated_duration_minutes,
            "llm_provider": question_set.llm_provider,
            "categories": question_set.categories_distribution,
        },
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "category": cat_names.get(q.category.value, q.category.value),
                "difficulty": q.difficulty.value,
                "time_limit": q.time_limit_seconds,
                "expected_topics": q.expected_topics[:3],
                "follow_ups": q.follow_up_questions[:2],
                "context": q.context,
                "resume_ref": q.resume_reference,
            }
            for q in question_set.questions
        ],
    }

    # Save to file
    output_path = "tests/output_questions.json"
    os.makedirs("tests", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2, ensure_ascii=False)
    print_ok(f"Full output saved to: {output_path}")

    # Print condensed JSON
    print(f"\n  {C.GRAY}Condensed JSON (first 3 questions):{C.END}")
    condensed = {
        "candidate": full_output["candidate"]["name"],
        "llm": full_output["config"]["llm_provider"],
        "questions": [
            {"id": q["id"], "cat": q["category"], "q": q["question"][:80] + "..."}
            for q in full_output["questions"][:3]
        ],
    }
    print(json.dumps(condensed, indent=2))

    # ──────────────── SUMMARY ────────────────
    print_header("TEST SUMMARY")

    results = {
        "Resume Parsed": parsed.personal_info.full_name is not None,
        "Name Extracted": bool(question_set.candidate_name and question_set.candidate_name != "Candidate"),
        "Skills Found": len(parsed.skills) > 0,
        "Questions Generated": question_set.total_questions > 0,
        "LLM Available": llm.is_available,
        "LLM Enhanced": question_set.llm_provider is not None,
        "No Crash": True,
    }

    all_pass = True
    for test_name, passed in results.items():
        if passed:
            print_ok(f"{test_name}")
        else:
            print_err(f"{test_name}")
            if test_name not in ("LLM Available", "LLM Enhanced"):
                all_pass = False

    print(f"\n  {C.BOLD}Stats:{C.END}")
    print_info("Parse Time", f"{parse_time:.2f}s")
    print_info("Generation Time", f"{gen_time:.2f}s")
    print_info("Total Questions", question_set.total_questions)
    print_info("LLM Provider", question_set.llm_provider or "none (template-only)")
    print_info("Name", question_set.candidate_name)

    if all_pass:
        print(f"\n  {C.GREEN}{C.BOLD}{'═' * 50}{C.END}")
        print(f"  {C.GREEN}{C.BOLD}  ALL TESTS PASSED ✓{C.END}")
        print(f"  {C.GREEN}{C.BOLD}{'═' * 50}{C.END}")
    else:
        print(f"\n  {C.RED}{C.BOLD}  SOME TESTS FAILED ✗{C.END}")

    return all_pass


# ==================== TEST WITH REAL PDF ====================

async def test_with_pdf(pdf_path: str):
    """Test with an actual PDF file."""

    print_header(f"TESTING WITH PDF: {pdf_path}")

    if not os.path.exists(pdf_path):
        print_err(f"File not found: {pdf_path}")
        return

    with open(pdf_path, "rb") as f:
        content = f.read()

    filename = os.path.basename(pdf_path)
    print_info("File", filename)
    print_info("Size", f"{len(content) / 1024:.1f} KB")

    from app.services.resume_parser import ResumeParser
    from app.services.question_generator import QuestionGenerator

    parser = ResumeParser()
    parsed = await parser.parse(content, filename)

    print_ok(f"Name: {parsed.personal_info.full_name}")
    print_ok(f"Email: {parsed.personal_info.email}")
    print_ok(f"Skills: {len(parsed.skills)}")
    print_ok(f"Level: {parsed.experience_level.value}")

    qgen = QuestionGenerator()
    questions = qgen.generate(parsed.model_dump(), num_questions=10)

    print_ok(f"Generated {questions.total_questions} questions")
    print_ok(f"LLM: {questions.llm_provider or 'templates'}")

    cat_names = {"T": "Technical", "P": "Project", "B": "Behavioral", "C": "Conceptual", "R": "Role-fit"}

    for q in questions.questions:
        cat = cat_names.get(q.category.value, "?")
        print(f"\n  [{cat}] [{q.difficulty.value}] Q{q.id}:")
        print(f"  {C.WHITE}{q.question}{C.END}")
        if q.expected_topics:
            print(f"  {C.GRAY}Topics: {', '.join(q.expected_topics[:3])}{C.END}")


# ==================== MAIN ====================

if __name__ == "__main__":
    print(f"{C.BOLD}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║      AI INTERVIEW SYSTEM — QUESTION GENERATOR TEST     ║")
    print("║                  Full Terminal Output                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{C.END}")

    # Run main test
    success = asyncio.run(test_full_pipeline())

    # If a PDF path is provided as argument, test with it too
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        asyncio.run(test_with_pdf(pdf_path))

    print(f"\n{C.GRAY}Usage:{C.END}")
    print(f"  python tests/test_print_questions.py")
    print(f"  python tests/test_print_questions.py path/to/resume.pdf")
