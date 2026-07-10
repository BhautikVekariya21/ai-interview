from io import BytesIO

import pdfplumber
from loguru import logger

from app.schemas.roaster_schemas import RoastResponse
from app.services.llm_service import get_llm


def _llm_is_available(llm: object) -> bool:
    available = getattr(llm, "is_available", True)
    if callable(available):
        available = available()
    return bool(available)


class ResumeRoasterService:
    def __init__(self):
        self.llm = get_llm()

    def roast_resume(self, file_content: bytes, filename: str) -> RoastResponse:
        logger.info(f"Extracting text from {filename} for roasting...")
        
        extracted_text = ""
        if filename.lower().endswith(".pdf"):
            try:
                with pdfplumber.open(BytesIO(file_content)) as pdf:
                    text_parts = []
                    for page in pdf.pages:
                        text_parts.append(page.extract_text() or "")
                    extracted_text = "\n".join(text_parts)
            except Exception as e:
                logger.error(f"Failed to read PDF for roasting: {e}")
                extracted_text = ""
        else:
            try:
                extracted_text = file_content.decode("utf-8")
            except Exception:
                extracted_text = str(file_content)

        if not extracted_text.strip():
            raise ValueError("Could not extract readable text from the file.")

        logger.info("Generating roast via LLM...")
        
        system_prompt = (
            "You are an expert, brutally honest tech recruiter and AI resume roaster. "
            "Your job is to rip apart this resume, find the glaring weaknesses, but also begrudgingly "
            "admit if there are actual strengths. "
            "You MUST output valid JSON ONLY, with NO markdown formatting blocks."
        )

        user_prompt = f"""
Here is the raw text of a candidate's resume:
\"\"\"
{extracted_text[:4000]}
\"\"\"

Analyze this resume and provide a brutal, funny, but ultimately constructive roast. 
Return the result EXACTLY as a JSON object with this structure:
{{
  "score": (integer out of 10, e.g. 4),
  "strengths": ["string", "string", "string"],
  "weaknesses": ["string", "string", "string"],
  "brutal_roast": "A 1-2 paragraph brutally honest and witty summary of what a recruiter actually thinks when they see this."
}}
"""

        data = self.llm.generate_json(prompt=user_prompt, system_prompt=system_prompt, max_tokens=1500)
        
        if not data:
            if not _llm_is_available(self.llm):
                raise ValueError("No LLM API keys configured. Please add an API key (e.g. GROQ_API_KEY) to your .env file.")
            raise ValueError("Failed to generate roast from AI.")
            
        return RoastResponse(
            success=True,
            score=int(data.get("score", 5)),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            brutal_roast=str(data.get("brutal_roast", "It's so generic I fell asleep reading it."))
        )

def get_resume_roaster() -> ResumeRoasterService:
    return ResumeRoasterService()
