import io
from typing import Optional

import pdfplumber
from loguru import logger

from app.services.llm_service import get_llm
from app.schemas.cover_letter_schemas import CoverLetterResponse


def _llm_is_available(llm: object) -> bool:
    available = getattr(llm, "is_available", True)
    if callable(available):
        available = available()
    return bool(available)


class CoverLetterService:
    def __init__(self):
        self.llm = get_llm()

    def generate_cover_letter(self, job_description: str, file_content: Optional[bytes] = None, filename: Optional[str] = None) -> CoverLetterResponse:
        logger.info("Generating cover letter...")
        
        extracted_text = ""
        if file_content and filename:
            if filename.lower().endswith(".pdf"):
                try:
                    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                        text_parts = []
                        for page in pdf.pages:
                            text_parts.append(page.extract_text() or "")
                        extracted_text = "\n".join(text_parts)
                except Exception as e:
                    logger.error(f"Failed to read PDF for cover letter: {e}")
            elif filename.lower().endswith(".txt"):
                try:
                    extracted_text = file_content.decode("utf-8")
                except Exception as e:
                    logger.error(f"Failed to read TXT for cover letter: {e}")
                    
        system_prompt = (
            "You are an expert career coach and executive resume writer. "
            "Your task is to write a highly professional, engaging, and tailored cover letter "
            "based on the provided job description and the candidate's resume (if provided). "
            "The cover letter should highlight how the candidate's skills and experiences align "
            "with the job requirements. Keep it under 400 words, use standard professional formatting, "
            "and do not include placeholder brackets like [Your Name] unless absolutely necessary; if data is missing, make it general enough to avoid placeholders if possible."
        )

        user_prompt = f"""
Job Description:
\"\"\"
{job_description}
\"\"\"

Candidate Resume (use this to tailor the letter, if empty, write a generic excellent cover letter for the role):
\"\"\"
{extracted_text[:6000]}
\"\"\"

Output EXACTLY AND ONLY a valid JSON object with a single string field `cover_letter` containing the written cover letter text. Keep paragraphs intact using newline (\\n) characters inside the string.
Example format:
{{
  "cover_letter": "Dear Hiring Manager,\\n\\nI am writing to express my interest in..."
}}
"""

        data = self.llm.generate_json(prompt=user_prompt, system_prompt=system_prompt, max_tokens=1500)
        
        if not data:
            if not _llm_is_available(self.llm):
                raise ValueError("No LLM API keys configured. Please add an API key (e.g. GROQ_API_KEY) to your .env file.")
            raise ValueError("Failed to generate cover letter from AI.")
            
        return CoverLetterResponse(
            success=True,
            cover_letter=data.get("cover_letter", "Could not generate cover letter.")
        )

_cover_letter_service_instance = None

def get_cover_letter_service() -> CoverLetterService:
    global _cover_letter_service_instance
    if _cover_letter_service_instance is None:
        _cover_letter_service_instance = CoverLetterService()
    return _cover_letter_service_instance
