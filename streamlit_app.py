"""
Streamlit UI for AI-Powered Interview System.
WITH TTS (Text-to-Speech) for questions.

Run:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import uuid
import io
from typing import Any, Dict, List

import requests
import streamlit as st

# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AI Interview System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════
# CUSTOM CSS
# ═══════════════════════════════════════════════════════════════

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .question-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .success-banner {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 1.5rem;
        margin: 1rem 0;
    }
    .warning-banner {
        background: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 1.5rem;
        margin: 1rem 0;
    }
    .error-banner {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-size: 1.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════


def api_url(path: str) -> str:
    """Build API URL."""
    base = st.session_state.get("api_base", "http://localhost:8000").rstrip("/")
    return f"{base}{path}"


def ensure_state() -> None:
    """Initialize session state."""
    defaults = {
        "session_id": str(uuid.uuid4()),
        "resume_json": None,
        "questions": [],
        "answers": {},
        "evaluations": {},
        "interview_ended": False,
        "final_results": None,
        "api_base": "http://localhost:8000",
        "candidate_name": "Candidate",
        "tts_audio": None,  # Store TTS audio
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def post_file(path: str, upload, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """POST file to API."""
    files = {"file": (upload.name, upload.getvalue(), upload.type or "application/octet-stream")}
    resp = requests.post(api_url(path), files=files, params=params, timeout=300)
    resp.raise_for_status()
    return resp.json()


def post_json(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST JSON to API."""
    resp = requests.post(api_url(path), json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()


def get_tts_audio(text: str) -> bytes:
    """Get TTS audio from API or generate locally."""
    try:
        # Try API first
        resp = requests.post(
            api_url("/tts"),
            params={"text": text, "language": "en", "slow": False},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.content
    except Exception as e:
        st.warning(f"API TTS failed: {e}, using local gTTS")
    
    # Fallback to local gTTS
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    except ImportError:
        st.error("gTTS not installed. Run: pip install gTTS")
        return None
    except Exception as e:
        st.error(f"TTS failed: {e}")
        return None


def get_category_name(code: str) -> str:
    """Get full category name from code."""
    names = {
        "T": "Technical",
        "P": "Project",
        "B": "Behavioral",
        "C": "Conceptual",
        "R": "Role Fit"
    }
    return names.get(code, code)


def get_grade_color(grade: str) -> str:
    """Get color emoji for grade."""
    colors = {
        "Exceptional": "🟢",
        "Strong": "🔵",
        "Adequate": "🟡",
        "Needs Work": "🟠",
        "Insufficient": "🔴",
    }
    return colors.get(grade, "⚪")


ensure_state()

# ═══════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("⚙️ Settings")
    st.text_input("API Base URL", key="api_base")
    
    st.divider()
    
    # API Health Check
    if st.button("🔍 Check API Health"):
        try:
            r = requests.get(api_url("/health"), timeout=15)
            r.raise_for_status()
            data = r.json()
            st.success("✅ Backend connected")
            with st.expander("Details"):
                st.json(data)
        except Exception as exc:
            st.error(f"❌ Connection failed: {exc}")
    
    st.divider()
    
    # Session Info
    st.write(f"**Session ID:**")
    st.code(st.session_state.session_id[:16] + "...")
    
    if st.session_state.candidate_name != "Candidate":
        st.write(f"**Candidate:** {st.session_state.candidate_name}")
    
    # Progress
    if st.session_state.questions:
        total = len(st.session_state.questions)
        answered = len([a for a in st.session_state.answers.values() if a.strip()])
        progress = answered / total if total > 0 else 0
        st.progress(progress)
        st.write(f"**Progress:** {answered}/{total} answered")
    
    st.divider()
    
    # Reset Session
    if st.button("🔄 New Interview", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════

st.markdown('<div class="main-header">🎯 AI-Powered Interview System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Resume → Questions → Voice Interview → AI Evaluation</div>', unsafe_allow_html=True)

# Check if interview has ended
if st.session_state.interview_ended and st.session_state.final_results:
    # ═══════════════════════════════════════════════════════════════
    # FINAL RESULTS VIEW
    # ═══════════════════════════════════════════════════════════════
    
    results = st.session_state.final_results
    
    st.header("📊 Interview Results")
    st.divider()
    
    # Hire Decision Banner
    hire_decision = results.get("hire_decision", "")
    if "STRONG HIRE" in hire_decision:
        st.markdown(f'<div class="success-banner">{hire_decision}</div>', unsafe_allow_html=True)
    elif "HIRE" in hire_decision and "NO" not in hire_decision:
        st.info(f"### {hire_decision}")
    elif "MAYBE" in hire_decision:
        st.markdown(f'<div class="warning-banner">{hire_decision}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="error-banner">{hire_decision}</div>', unsafe_allow_html=True)
    
    # Overall Scores
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Overall Score", f"{results.get('overall_score', 0):.0f}/100")
    
    with col2:
        grade = results.get("overall_grade", "N/A")
        st.metric("Grade", f"{get_grade_color(grade)} {grade}")
    
    with col3:
        st.metric("Answered", f"{results.get('answered_questions', 0)}/{results.get('total_questions', 0)}")
    
    with col4:
        st.metric("Duration", results.get("interview_duration_estimate", "~10 min"))
    
    st.divider()
    
    # Recommendation
    st.subheader("📋 Recommendation")
    st.info(results.get("recommendation", ""))
    
    # Summary
    st.subheader("📝 Summary")
    st.write(results.get("summary", ""))
    
    # Category Breakdown
    st.subheader("📊 Performance by Category")
    
    cat_breakdown = results.get("category_breakdown", {})
    if cat_breakdown:
        cat_cols = st.columns(min(len(cat_breakdown), 5))
        for idx, (cat_name, cat_data) in enumerate(cat_breakdown.items()):
            with cat_cols[idx % len(cat_cols)]:
                if isinstance(cat_data, dict):
                    score = cat_data.get("average_score", 0)
                    count = cat_data.get("questions_count", 0)
                    grade = cat_data.get("grade", "N/A")
                else:
                    score = getattr(cat_data, "average_score", 0)
                    count = getattr(cat_data, "questions_count", 0)
                    grade = getattr(cat_data, "grade", "N/A")
                
                st.metric(cat_name, f"{score:.0f}/100")
                st.caption(f"{count} questions • {grade}")
    
    st.divider()
    
    # Strengths and Improvements
    col_str, col_imp = st.columns(2)
    
    with col_str:
        st.subheader("💪 Overall Strengths")
        strengths = results.get("strengths_overall", [])
        if strengths:
            for s in strengths:
                st.write(f"✅ {s}")
        else:
            st.write("_No specific strengths identified_")
    
    with col_imp:
        st.subheader("📈 Areas to Improve")
        improvements = results.get("improvements_overall", [])
        if improvements:
            for i in improvements:
                st.write(f"🔸 {i}")
        else:
            st.write("_No specific improvements needed_")
    
    st.divider()
    
    # Individual Question Breakdown
    st.subheader("📋 Detailed Question Breakdown")
    
    evaluations = results.get("evaluations", [])
    for ev in evaluations:
        q_num = ev.get("question_number", "?")
        category = ev.get("category", "T")
        score = ev.get("score", 0)
        grade = ev.get("grade", "N/A")
        
        icon = get_grade_color(grade)
        
        with st.expander(f"{icon} Q{q_num} [{get_category_name(category)}] — {score}/100 ({grade})"):
            st.write(f"**Question:** {ev.get('question', '')}")
            
            answer = ev.get("answer", "")
            if answer:
                st.write(f"**Your Answer:** {answer}")
            else:
                st.write("**Your Answer:** _Not answered_")
            
            st.divider()
            
            col_s, col_i = st.columns(2)
            
            with col_s:
                if ev.get("strengths"):
                    st.write("**✅ Strengths:**")
                    for s in ev["strengths"]:
                        st.write(f"  • {s}")
            
            with col_i:
                if ev.get("improvements"):
                    st.write("**🔸 Improvements:**")
                    for i in ev["improvements"]:
                        st.write(f"  • {i}")
            
            st.write(f"**💬 Feedback:** {ev.get('feedback', '')}")
    
    st.divider()
    
    # Actions
    col_restart, col_download = st.columns(2)
    
    with col_restart:
        if st.button("🔄 Start New Interview", type="primary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    with col_download:
        report_lines = [
            "="*60,
            "AI INTERVIEW REPORT",
            "="*60,
            f"Candidate: {results.get('candidate_name', 'Unknown')}",
            f"Session: {st.session_state.session_id}",
            "",
            "OVERALL RESULTS",
            "-"*60,
            f"Score: {results.get('overall_score', 0):.0f}/100",
            f"Grade: {results.get('overall_grade', 'N/A')}",
            f"Decision: {results.get('hire_decision', 'N/A')}",
            f"Recommendation: {results.get('recommendation', '')}",
            "",
            "SUMMARY",
            "-"*60,
            results.get('summary', ''),
            "",
            "DETAILED SCORES",
            "-"*60,
        ]
        
        for ev in evaluations:
            report_lines.extend([
                "",
                f"Q{ev.get('question_number')}: {ev.get('question', '')[:80]}...",
                f"Score: {ev.get('score', 0)}/100 ({ev.get('grade', 'N/A')})",
                f"Answer: {ev.get('answer', 'Not answered')[:100]}...",
            ])
        
        report = "\n".join(report_lines)
        
        st.download_button(
            "📥 Download Report",
            data=report,
            file_name=f"interview_report_{st.session_state.session_id[:8]}.txt",
            mime="text/plain",
            use_container_width=True
        )

else:
    # ═══════════════════════════════════════════════════════════════
    # INTERVIEW VIEW
    # ═══════════════════════════════════════════════════════════════
    
    # Step 1 & 2: Resume + Questions
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Step 1: Upload Resume")
        resume_file = st.file_uploader(
            "Upload resume (PDF/DOCX/TXT)",
            type=["pdf", "docx", "txt"],
            key="resume_upload",
            help="Upload your resume to generate personalized questions"
        )
        
        parse_disabled = resume_file is None
        
        if st.button("🔍 Parse Resume", disabled=parse_disabled, use_container_width=True):
            with st.spinner("Parsing resume..."):
                try:
                    data = post_file("/parse-resume", resume_file)
                    st.session_state.resume_json = data.get("data", {})
                    
                    # Extract candidate name
                    personal_info = st.session_state.resume_json.get("personal_info", {})
                    if isinstance(personal_info, dict):
                        st.session_state.candidate_name = personal_info.get("full_name", "Candidate")
                    
                    st.success("✅ Resume parsed successfully")
                except Exception as exc:
                    st.error(f"❌ Parse failed: {exc}")
        
        if st.session_state.resume_json:
            with st.expander("📋 View Parsed Resume"):
                st.json(st.session_state.resume_json)
    
    with col2:
        st.subheader("❓ Step 2: Generate Questions")
        num_q = st.slider("Number of questions", 5, 20, 12, help="More questions = longer interview")
        
        gen_disabled = resume_file is None
        
        if st.button("🎯 Generate Questions", disabled=gen_disabled, use_container_width=True):
            with st.spinner("Generating personalized interview questions..."):
                try:
                    payload = post_file(
                        "/start-interview",
                        resume_file,
                        params={"num_questions": num_q}
                    )
                    interview_data = payload.get("interview_session", {})
                    st.session_state.questions = interview_data.get("questions", [])
                    
                    candidate_data = interview_data.get("candidate", {})
                    if isinstance(candidate_data, dict):
                        st.session_state.candidate_name = candidate_data.get("name", "Candidate")
                    
                    st.success(f"✅ Generated {len(st.session_state.questions)} questions")
                except Exception as exc:
                    st.error(f"❌ Failed: {exc}")
        
        if st.session_state.questions:
            cats = sorted({q.get("category", "?") for q in st.session_state.questions})
            st.write("**Categories:**", ", ".join([get_category_name(c) for c in cats]))
    
    st.divider()
    
    # Step 3: Interview Questions
    if st.session_state.questions:
        st.subheader("🎤 Step 3: Answer Interview Questions")
        
        # Question navigation
        total_q = len(st.session_state.questions)
        
        col_nav1, col_nav2 = st.columns([3, 1])
        
        with col_nav1:
            q_index = st.number_input(
                "Select question",
                min_value=1,
                max_value=total_q,
                value=1,
                step=1,
                label_visibility="collapsed"
            )
        
        with col_nav2:
            answered_count = len([a for a in st.session_state.answers.values() if a.strip()])
            st.metric("Answered", f"{answered_count}/{total_q}")
        
        q = st.session_state.questions[q_index - 1]
        q_id = q.get("id", str(q_index))
        question_text = q.get("question", "")
        
        # ═══════════════════════════════════════════════════════════════
        # QUESTION DISPLAY WITH TTS
        # ═══════════════════════════════════════════════════════════════
        
        st.markdown(f'<div class="question-box">', unsafe_allow_html=True)
        st.markdown(f"### Q{q_index}: {question_text}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Question metadata and TTS
        col_meta1, col_meta2, col_meta3, col_tts = st.columns([1, 1, 1, 1])
        
        with col_meta1:
            st.caption(f"**Category:** {get_category_name(q.get('category', 'T'))}")
        with col_meta2:
            st.caption(f"**Difficulty:** {q.get('difficulty', 'Medium')}")
        with col_meta3:
            st.caption(f"**Time Limit:** {q.get('time_limit', 120)}s")
        
        with col_tts:
            # TTS BUTTON - Speak the question
            if st.button("🔊 Speak Question", key=f"tts_btn_{q_index}", use_container_width=True):
                with st.spinner("Generating audio..."):
                    audio_bytes = get_tts_audio(question_text)
                    if audio_bytes:
                        st.session_state.tts_audio = audio_bytes
        
        # Display TTS audio player if available
        if st.session_state.get("tts_audio"):
            st.audio(st.session_state.tts_audio, format="audio/mp3")
        
        st.divider()
        
        # Answer input
        current_answer = st.session_state.answers.get(q_id, "")
        
        col_audio, col_text = st.columns([1, 1])
        
        with col_audio:
            st.markdown("**🎙️ Voice Input**")
            audio = st.audio_input("Record your answer", key=f"audio_{q_index}")
            
            if audio is not None:
                if st.button("📝 Transcribe Audio", key=f"transcribe_{q_index}", use_container_width=True):
                    with st.spinner("Transcribing..."):
                        try:
                            files = {"file": ("answer.wav", audio.getvalue(), "audio/wav")}
                            r = requests.post(
                                api_url("/asr/transcribe-simple"),
                                files=files,
                                timeout=180,
                            )
                            r.raise_for_status()
                            data = r.json()
                            transcript = data.get("transcript", "") or data.get("text", "")
                            
                            if transcript and data.get("success", False):
                                st.session_state.answers[q_id] = transcript
                                st.success(f"✅ Transcribed ({data.get('word_count', 0)} words)")
                                
                                filler = data.get("filler_analysis")
                                if filler and filler.get("total_fillers", 0) > 0:
                                    with st.expander("Filler Word Analysis"):
                                        st.write(f"**Total Fillers:** {filler.get('total_fillers', 0)}")
                                        st.write(f"**Severity:** {filler.get('severity', 'low')}")
                                
                                st.rerun()
                            else:
                                st.warning("⚠️ No transcript returned")
                        except Exception as exc:
                            st.warning(f"⚠️ ASR Error: {exc}")
                            st.info("💡 You can type your answer in the text box →")
        
        with col_text:
            st.markdown("**✍️ Text Input**")
            answer_text = st.text_area(
                "Type or edit your answer:",
                value=current_answer,
                height=200,
                key=f"answer_{q_index}",
                help="You can type directly or transcribe from audio"
            )
            
            if st.button("💾 Save Answer", key=f"save_{q_index}", use_container_width=True):
                if answer_text.strip():
                    st.session_state.answers[q_id] = answer_text.strip()
                    # Clear TTS audio when moving to save
                    st.session_state.tts_audio = None
                    st.success("✅ Answer saved")
                    st.rerun()
                else:
                    st.warning("⚠️ Please enter an answer first")
        
        # Quick navigation
        st.divider()
        st.write("**Quick Navigation:**")
        
        nav_cols = st.columns(min(total_q, 12))
        
        for i in range(min(12, total_q)):
            idx = i + 1
            qid = st.session_state.questions[i].get("id", str(idx))
            answered = bool(st.session_state.answers.get(qid, "").strip())
            
            with nav_cols[i]:
                icon = "✅" if answered else "⬜"
                label = f"{icon}{idx}"
                
                if st.button(label, key=f"nav_{idx}", use_container_width=True):
                    st.session_state.tts_audio = None  # Clear audio on navigation
                    st.rerun()
        
        # ═══════════════════════════════════════════════════════════════
        # END INTERVIEW SECTION
        # ═══════════════════════════════════════════════════════════════
        
        st.divider()
        st.subheader("🏁 End Interview & Get Results")
        
        answered_count = len([a for a in st.session_state.answers.values() if a.strip()])
        
        col_info, col_btn = st.columns([2, 1])
        
        with col_info:
            st.write(f"**Progress:** {answered_count}/{total_q} questions answered")
            
            if answered_count < total_q:
                st.warning(f"⚠️ {total_q - answered_count} questions unanswered. You can still end the interview.")
            else:
                st.success("✅ All questions answered! Ready to evaluate.")
        
        with col_btn:
            end_disabled = answered_count == 0
            
            if st.button(
                "🏁 END INTERVIEW",
                type="primary",
                use_container_width=True,
                disabled=end_disabled,
                help="Evaluate all answers and see comprehensive results"
            ):
                with st.spinner("🔄 Evaluating all answers... This may take 30-60 seconds."):
                    try:
                        # Build Q&A pairs - use dict format
                        qa_pairs = []
                        for i, q in enumerate(st.session_state.questions):
                            qid = q.get("id", str(i + 1))
                            qa_pairs.append({
                                "question": q.get("question", ""),
                                "answer": st.session_state.answers.get(qid, ""),
                                "category": q.get("category", "T"),
                                "question_id": qid,
                                "question_number": i + 1,
                            })
                        
                        # Call batch evaluation
                        payload = {
                            "session_id": st.session_state.session_id,
                            "qa_pairs": qa_pairs,
                            "resume_context": st.session_state.resume_json,
                            "candidate_name": st.session_state.candidate_name,
                        }
                        
                        result = post_json("/evaluation/evaluate-batch", payload)
                        
                        st.session_state.final_results = result
                        st.session_state.interview_ended = True
                        st.success("✅ Evaluation complete!")
                        st.rerun()
                        
                    except requests.exceptions.HTTPError as exc:
                        st.error(f"❌ Evaluation API error: {exc}")
                        if exc.response:
                            try:
                                error_detail = exc.response.json()
                                with st.expander("Error Details"):
                                    st.json(error_detail)
                            except:
                                st.text(exc.response.text[:500])
                    except Exception as exc:
                        st.error(f"❌ Evaluation failed: {exc}")
        
        if answered_count == 0:
            st.info("💡 Answer at least one question to end the interview and see results.")
    
    else:
        st.info("👆 Upload a resume and generate questions to start the interview.")

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════

st.divider()
st.caption("🎯 AI-Powered Interview System | Built with FastAPI + Streamlit | TTS + ASR Enabled")
