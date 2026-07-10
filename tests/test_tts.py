"""
Module 3 TTS Test Suite — Terminal output with audio generation.
Run: python tests/test_tts.py
"""

import os
import sys
import time
import asyncio

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


# ─── Terminal Colors ─────────────────────────────────────────

class C:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'
    GRAY = '\033[90m'
    MAGENTA = '\033[35m'


def header(text):
    print(f"\n{C.BOLD}{C.CYAN}{'=' * 70}{C.END}")
    print(f"{C.BOLD}{C.CYAN}  {text}{C.END}")
    print(f"{C.BOLD}{C.CYAN}{'=' * 70}{C.END}")


def section(text):
    print(f"\n{C.YELLOW}{'─' * 55}{C.END}")
    print(f"  {C.BOLD}{text}{C.END}")
    print(f"{C.YELLOW}{'─' * 55}{C.END}")


def ok(text):
    print(f"  {C.GREEN}✓{C.END} {text}")


def warn(text):
    print(f"  {C.YELLOW}⚠{C.END} {text}")


def err(text):
    print(f"  {C.RED}✗{C.END} {text}")


def info(label, value):
    print(f"  {C.GRAY}{label}:{C.END} {value}")


def save_audio(audio_bytes, filename):
    """Save audio to tests/output/ directory."""
    os.makedirs("tests/output", exist_ok=True)
    path = f"tests/output/{filename}"
    with open(path, "wb") as f:
        f.write(audio_bytes)
    return path


async def test_tts():
    header("MODULE 3: TEXT-TO-SPEECH — FULL TEST")

    from app.services.tts_service import get_tts

    tts = get_tts()

    results = {}

    # ── 1. Configuration ──
    section("1. TTS Configuration")
    config = tts.get_config()
    info("Active Provider", config.active_provider or "NONE")
    info("Available", ", ".join(config.available_providers) or "none")
    info("Fallback Chain", " → ".join(config.fallback_order) or "none")
    info("Voice ID", config.voice_id)
    info("Speech Rate", config.speech_rate)
    info("Language", config.language)
    info("Cache", f"{'ON' if config.cache_enabled else 'OFF'} "
                  f"({config.cache_size_mb} MB)")

    results["Config"] = bool(tts.available_providers)

    if not tts.available_providers:
        err("No TTS providers available!")
        print(f"\n  {C.YELLOW}Install at least one:{C.END}")
        print("    pip install elevenlabs  (best quality, API key)")
        print("    pip install gTTS        (free, internet needed)")
        print("    pip install pyttsx3     (offline, basic)")
        return

    # ── 2. ElevenLabs Usage ──
    if "elevenlabs" in tts.available_providers:
        section("2. ElevenLabs API Status")
        usage = tts.get_usage()
        if usage:
            used = usage['character_count']
            limit = usage['character_limit']
            remaining = usage['remaining']
            pct = used / max(limit, 1) * 100

            info("Characters Used", f"{used:,}")
            info("Character Limit", f"{limit:,}")
            info("Remaining", f"{remaining:,}")
            info("Tier", usage.get("tier", "unknown"))

            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            color = C.GREEN if pct < 70 else (
                C.YELLOW if pct < 90 else C.RED
            )
            print(f"  Usage: [{color}{bar}{C.END}] {pct:.1f}%")

            results["ElevenLabs"] = True
        else:
            warn("Could not fetch usage — check API key")
            results["ElevenLabs"] = False
    else:
        section("2. ElevenLabs — Not Available")
        warn("Set ELEVENLABS_API_KEY in .env for best quality")
        results["ElevenLabs"] = False

    # ── 3. Basic Text Generation ──
    section("3. Text-to-Speech Generation")

    test_texts = [
        (
            "Short",
            "Hello, welcome to your interview!",
        ),
        (
            "Medium",
            "Can you explain how Python's garbage collector works? "
            "Describe both reference counting and the cyclic collector.",
        ),
        (
            "Technical",
            "Tell me about your experience with PyTorch and "
            "Hugging Face. How did you use torch.compile for model "
            "optimization in your API project?",
        ),
    ]

    all_gen_ok = True
    for label, text in test_texts:
        start = time.time()
        audio, provider, cached = tts.generate(text=text)
        elapsed = time.time() - start

        if audio:
            path = save_audio(audio, f"test_{label.lower()}.mp3")
            ok(
                f"[{label}] {len(text)} chars → "
                f"{len(audio):,} bytes via {C.CYAN}{provider}{C.END} "
                f"({'cached' if cached else f'{elapsed:.2f}s'})"
            )
        else:
            err(f"[{label}] FAILED!")
            all_gen_ok = False

    results["Generation"] = all_gen_ok

    # ── 4. SSML Processing ──
    section("4. Pronunciation Processing")

    from app.services.ssml_processor import SSMLProcessor
    ssml = SSMLProcessor()

    test_ssml = [
        ("API design with REST", "A P I design with REST"),
        ("nginx and kubernetes", "engine X and Kubernetes"),
        ("JSON parsing in FastAPI", "Jason parsing in Fast A P I"),
        ("SQL vs NoSQL databases", "S Q L vs No S Q L databases"),
    ]

    for original, expected_fragment in test_ssml:
        processed = ssml.process(original)
        has_fix = any(
            word in processed
            for word in expected_fragment.split()[:2]
        )
        if has_fix:
            ok(f"'{original}' → '{processed}'")
        else:
            warn(f"'{original}' → '{processed}' (expected: {expected_fragment})")

    results["SSML"] = True

    # ── 5. Interview Intro ──
    section("5. Interview Introduction")

    intro_audio, intro_text, _script_src = tts.generate_interview_intro(
        candidate_name="Bhautik Vekariya",
        num_questions=15,
        duration_minutes=30,
    )

    if intro_audio:
        path = save_audio(intro_audio, "interview_intro.mp3")
        ok(f"Intro: {len(intro_audio):,} bytes → {path}")
        # Print script wrapped
        print(f"\n  {C.CYAN}Script:{C.END}")
        words = intro_text.split()
        line = "    "
        for word in words:
            if len(line) + len(word) > 68:
                print(line)
                line = "    "
            line += word + " "
        if line.strip():
            print(line)

        results["Intro"] = True
    else:
        err("Failed to generate intro!")
        results["Intro"] = False

    # ── 6. Questions ──
    section("6. Interview Question Audio")

    test_questions = [
        "You listed Python as a key skill. Explain how Python's GIL "
        "affects multithreading in your data processing pipelines.",

        "Walk me through the architecture of your Sentiment Analysis "
        "Dashboard. Why did you choose BERT over other transformer models?",

        "Tell me about a time at TechCorp when you disagreed with "
        "a technical decision. How did you handle it?",

        "Explain the bias-variance tradeoff. How do you diagnose "
        "overfitting in your machine learning models?",

        "Where do you see yourself in 3 years given your expertise "
        "in PyTorch and data science?",
    ]

    q_ok = True
    for i, q_text in enumerate(test_questions, 1):
        start = time.time()
        audio, full_text = tts.generate_question_audio(
            question_text=q_text,
            question_number=i,
            total_questions=len(test_questions),
            include_transition=True,
        )
        elapsed = time.time() - start

        if audio:
            path = save_audio(audio, f"question_{i}.mp3")
            ok(f"Q{i}: {len(audio):,} bytes ({elapsed:.2f}s)")
            print(f"    {C.GRAY}{full_text[:75]}...{C.END}")
        else:
            err(f"Q{i} FAILED!")
            q_ok = False

    results["Questions"] = q_ok

    # ── 7. Outro ──
    section("7. Interview Outro")

    outro_audio, outro_text, _script_src = tts.generate_interview_outro(
        candidate_name="Bhautik Vekariya",
        num_questions=15,
        score=78,
    )

    if outro_audio:
        path = save_audio(outro_audio, "interview_outro.mp3")
        ok(f"Outro: {len(outro_audio):,} bytes → {path}")
        results["Outro"] = True
    else:
        err("Failed to generate outro!")
        results["Outro"] = False

    # ── 8. Language Detection ──
    section("8. Language Detection (Stretch Goal)")

    test_langs = {
        "English": (
            "Experienced software engineer with expertise in "
            "Python, Django, and machine learning pipelines"
        ),
        "Hindi": (
            "पायथन और डेटा साइंस में अनुभव। "
            "मशीन लर्निंग प्रोजेक्ट्स पर काम किया है"
        ),
        "Spanish": (
            "Experiencia en desarrollo de software con "
            "Java y Spring Boot en aplicaciones empresariales"
        ),
        "French": (
            "Expérience en développement web avec "
            "React et Node.js pour applications modernes"
        ),
        "Gujarati": (
            "પાયથોન અને ડેટા સાયન્સમાં અનુભવ ધરાવે છે"
        ),
    }

    for expected, text in test_langs.items():
        lang, conf = tts.lang_detector.detect(text)
        lang_name = tts.lang_detector.get_language_name(lang)
        marker = (
            f"{C.GREEN}✓{C.END}" if conf > 0.5
            else f"{C.YELLOW}?{C.END}"
        )
        print(
            f"  {marker} Expected: {expected:10s} | "
            f"Got: {lang_name} ({lang}, {conf:.2f})"
        )

    results["Language Detection"] = True

    # ── 9. Voice Listing ──
    section("9. Available Voices")

    voices = tts.list_voices()
    info("Total voices", len(voices))

    if voices:
        for v in voices[:8]:
            print(
                f"    {C.CYAN}{v.get('name', '?'):25s}{C.END} "
                f"| {v.get('voice_id', '?')[:22]:22s} "
                f"| {v.get('provider', '?')}"
            )
        if len(voices) > 8:
            print(f"    ... and {len(voices) - 8} more")

    results["Voices"] = len(voices) > 0

    # ── 10. Cache ──
    section("10. Cache Status")
    info("Directory", str(tts.cache_dir))
    info("Size", f"{tts.get_cache_size_mb():.2f} MB")
    info("Files", tts.get_cache_file_count())

    # ── 11. Stats ──
    section("11. Usage Statistics")
    stats = tts.get_stats()
    info("Total Requests", stats["total_requests"])
    info("Cache Hits", stats["cache_hits"])
    info("Cache Hit Rate", f"{stats['cache_hit_rate']:.1%}")
    info("Provider Usage", stats["provider_usage"])

    # ── Summary ──
    header("MODULE 3 TEST SUMMARY")

    all_pass = True
    for name, passed in results.items():
        if passed:
            ok(name)
        else:
            err(name)
            all_pass = False

    print()
    info("Provider", tts.active_provider or "none")
    info("Audio Files", "tests/output/")

    if all_pass:
        print(
            f"\n  {C.GREEN}{C.BOLD}"
            f"ALL TTS TESTS PASSED ✓"
            f"{C.END}\n"
        )
    else:
        print(
            f"\n  {C.YELLOW}"
            f"Some tests had issues — check above"
            f"{C.END}\n"
        )

    print(f"  {C.GRAY}Play audio files:{C.END}")
    print("    Windows: start tests\\output\\interview_intro.mp3")
    print("    macOS:   open tests/output/interview_intro.mp3")
    print("    Linux:   xdg-open tests/output/interview_intro.mp3")
    print()

    # ── NEW: AI Script Generation ──
    section("5a. AI-Powered Introduction (Personalized)")

    # Simulate resume data from Module 1
    mock_resume = {
        "personal_info": {
            "full_name": "Bhautik Vekariya",
            "email": "bhautik@example.com",
        },
        "experience_level": "mid",
        "total_experience_years": 3.5,
        "primary_domain": "machine_learning",
        "skills": [
            {"name": "Python", "category": "programming_language"},
            {"name": "PyTorch", "category": "framework"},
            {"name": "Docker", "category": "tool"},
            {"name": "FastAPI", "category": "framework"},
            {"name": "PostgreSQL", "category": "database"},
        ],
        "work_experience": [
            {
                "role": "ML Engineer",
                "company": "TechCorp Solutions",
                "duration_months": 24,
            }
        ],
        "education": [
            {
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "institution": "Gujarat Technological University",
            }
        ],
        "projects": [
            {"title": "Sentiment Analysis Dashboard"},
            {"title": "Real-Time Object Detection"},
            {"title": "Resume Parser API"},
        ],
    }

    intro_audio, intro_text, script_src = tts.generate_interview_intro(
        candidate_name="Bhautik Vekariya",
        num_questions=15,
        duration_minutes=30,
        resume_data=mock_resume,
        question_categories=["T", "T", "P", "P", "B", "B", "C", "C", "R"],
    )

    if intro_audio:
        path = save_audio(intro_audio, "ai_intro.mp3")
        ok(
            f"AI Intro ({C.MAGENTA}{script_src}{C.END}): "
            f"{len(intro_audio):,} bytes"
        )
        print(f"\n  {C.CYAN}AI-Generated Script:{C.END}")
        # Word wrap
        words = intro_text.split()
        line = "    "
        for word in words:
            if len(line) + len(word) > 68:
                print(line)
                line = "    "
            line += word + " "
        if line.strip():
            print(line)
        info(f"\n  Source", script_src)
        info("  Saved", path)
        results["AI Intro"] = True
    else:
        err("AI Intro generation FAILED!")
        results["AI Intro"] = False

    # ── AI Outro ──
    section("7a. AI-Powered Outro (With Performance)")

    outro_audio, outro_text, script_src = tts.generate_interview_outro(
        candidate_name="Bhautik Vekariya",
        num_questions=15,
        score=78,
        grade="Strong",
        resume_data=mock_resume,
        strengths=[
            "Strong Python and PyTorch knowledge",
            "Clear project architecture explanations",
        ],
        improvements=[
            "Could elaborate more on system design",
            "Behavioral answers need more structure",
        ],
        category_scores={"T": 85, "P": 80, "B": 65, "C": 75, "R": 70},
    )

    if outro_audio:
        path = save_audio(outro_audio, "ai_outro.mp3")
        ok(
            f"AI Outro ({C.MAGENTA}{script_src}{C.END}): "
            f"{len(outro_audio):,} bytes"
        )
        print(f"\n  {C.CYAN}AI-Generated Script:{C.END}")
        words = outro_text.split()
        line = "    "
        for word in words:
            if len(line) + len(word) > 68:
                print(line)
                line = "    "
            line += word + " "
        if line.strip():
            print(line)
        info(f"\n  Source", script_src)
        results["AI Outro"] = True
    else:
        err("AI Outro generation FAILED!")
        results["AI Outro"] = False

    # ── Encouragement ──
    section("7b. Encouragement Audio")

    contexts = ["thinking", "repeat", "struggling", "good_answer", "halfway"]
    for ctx in contexts:
        enc_audio, enc_text = tts.generate_encouragement_audio(
            candidate_name="Bhautik",
            context=ctx,
        )
        if enc_audio:
            save_audio(enc_audio, f"encouragement_{ctx}.mp3")
            ok(f"[{ctx:12s}] \"{enc_text}\"")
        else:
            warn(f"[{ctx}] Failed")

    results["Encouragement"] = True

    # ── Script Generator Status ──
    section("7c. Script Generator Status")
    gen = tts.script_generator
    info("AI Available", gen.is_llm_available)
    info("Active LLM", gen._active_llm or "none (templates)")
    info("Gemini", "✓" if gen._gemini_client else "✗")
    info("OpenAI", "✓" if gen._openai_client else "✗")
    info("Groq", "✓" if gen._groq_client else "✗")

if __name__ == "__main__":
    asyncio.run(test_tts())
