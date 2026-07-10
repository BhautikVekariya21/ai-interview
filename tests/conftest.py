"""
Shared test fixtures and configuration.
"""

import os
import sys
import inspect
import asyncio
import pytest

# Ensure pydantic settings parse in tests even if .env has non-boolean DEBUG
os.environ["DEBUG"] = "false"
# app.main refuses to start with DEBUG=false and the default JWT secret; give
# tests a non-default secret so the startup guard doesn't fail collection.
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-not-for-production-use")
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app


class AsyncCompatClient:
    """Async-like wrapper over TestClient for environments without pytest-asyncio."""

    def __init__(self, client: TestClient):
        self._client = client

    async def get(self, *args, **kwargs):
        return self._client.get(*args, **kwargs)

    async def post(self, *args, **kwargs):
        return self._client.post(*args, **kwargs)

    async def put(self, *args, **kwargs):
        return self._client.put(*args, **kwargs)

    async def patch(self, *args, **kwargs):
        return self._client.patch(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        return self._client.delete(*args, **kwargs)


def pytest_pyfunc_call(pyfuncitem):
    """Run async tests without external asyncio plugins."""
    test_fn = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_fn):
        kwargs = {
            name: pyfuncitem.funcargs[name]
            for name in pyfuncitem._fixtureinfo.argnames
        }
        asyncio.run(test_fn(**kwargs))
        return True
    return None


# ==================== SAMPLE RESUME DATA ====================

SAMPLE_RESUME_TEXT = """
John Smith
john.smith@email.com | +1-555-123-4567
San Francisco, CA
linkedin.com/in/johnsmith | github.com/johnsmith

SUMMARY
Experienced Software Engineer with 5+ years in backend development,
machine learning, and cloud infrastructure.

EDUCATION
Master of Science in Computer Science
Stanford University, 2019
GPA: 3.9/4.0

Bachelor of Technology in Computer Science and Engineering
IIT Delhi, 2017
GPA: 8.5/10.0

WORK EXPERIENCE
Senior Software Engineer at Google | 2021 - Present
• Designed and implemented microservices architecture serving 10M+ users
• Led migration from monolithic to distributed system using Kubernetes
• Reduced API latency by 40% through caching and query optimization
• Technologies: Python, Go, gRPC, Kubernetes, BigQuery

Software Engineer at Amazon | 2019 - 2021
• Built real-time recommendation engine using collaborative filtering
• Developed ETL pipelines processing 500GB daily data
• Implemented A/B testing framework for feature rollouts
• Technologies: Java, Python, AWS, DynamoDB, Apache Spark

TECHNICAL SKILLS
Languages: Python, Java, Go, JavaScript, SQL
Frameworks: Django, FastAPI, React, Spring Boot
ML/AI: PyTorch, PyTorch Lightning, scikit-learn, Hugging Face
Cloud: AWS, GCP, Docker, Kubernetes, Terraform
Databases: PostgreSQL, MongoDB, Redis, DynamoDB

PROJECTS
AI-Powered Code Review Bot
Built an automated code review system using GPT-4 and static analysis.
Technologies: Python, OpenAI API, GitHub Actions, FastAPI

Real-time Fraud Detection System
Developed ML pipeline for detecting fraudulent transactions in real-time.
Technologies: Python, PyTorch, Apache Kafka, Redis

CERTIFICATIONS
AWS Certified Solutions Architect - Professional, 2023
Google Cloud Professional Data Engineer, 2022
Certified Kubernetes Administrator (CKA), 2021

ACHIEVEMENTS
• Best Paper Award at ICML 2023 Workshop
• Google Peer Bonus Award, 2022
• Hackathon Winner - TechCrunch Disrupt 2020
"""

SIMPLE_RESUME = """
Jane Doe
jane.doe@gmail.com
+1-555-987-6543
New York, NY

EDUCATION
Bachelor of Science in Computer Science
MIT, 2022
GPA: 3.8/4.0

EXPERIENCE
Software Engineer at Microsoft | 2022 - Present
• Developed REST APIs using C# and .NET
• Implemented CI/CD pipelines with Azure DevOps

SKILLS
Python, C#, JavaScript, React, .NET, Azure, Docker, Git

PROJECTS
Task Management App
Built a full-stack task manager using React and Node.js.

CERTIFICATIONS
Azure Developer Associate, 2023
"""


# ==================== FIXTURES ====================

@pytest.fixture
def sample_resume_text():
    """Full sample resume text."""
    return SAMPLE_RESUME_TEXT


@pytest.fixture
def simple_resume_text():
    """Simple resume text."""
    return SIMPLE_RESUME


@pytest.fixture
def sample_resume_bytes():
    """Sample resume as bytes."""
    return SAMPLE_RESUME_TEXT.encode("utf-8")


@pytest.fixture
def simple_resume_bytes():
    """Simple resume as bytes."""
    return SIMPLE_RESUME.encode("utf-8")


@pytest.fixture
def empty_resume_bytes():
    """Empty/minimal content."""
    return b"Hello"


@pytest.fixture
def async_client():
    """Async-compatible HTTP client fixture."""
    with TestClient(app, base_url="http://test") as client:
        yield AsyncCompatClient(client)


@pytest.fixture
def file_extractor():
    """File extractor instance."""
    from app.services.file_extractor import FileExtractor
    return FileExtractor()


@pytest.fixture
def preprocessor():
    """Text preprocessor instance."""
    from app.services.text_preprocessor import TextPreprocessor
    return TextPreprocessor()


@pytest.fixture
def skill_normalizer():
    """Skill normalizer instance."""
    from app.services.skill_normalizer import SkillNormalizer
    return SkillNormalizer()


@pytest.fixture
def section_detector():
    """Section detector instance."""
    from app.services.section_detector import SectionDetector
    return SectionDetector()


@pytest.fixture
def ner_engine():
    """NER engine instance (without model loaded)."""
    from app.services.ner_engine import NEREngine
    return NEREngine()


@pytest.fixture
def entity_extractor(ner_engine, skill_normalizer):
    """Entity extractor instance."""
    from app.services.entity_extractor import EntityExtractor
    return EntityExtractor(ner_engine, skill_normalizer)


@pytest.fixture
def resume_parser():
    """Full resume parser instance."""
    from app.services.resume_parser import ResumeParser
    return ResumeParser()


@pytest.fixture
def pdf_path(tmp_path):
    """Optional PDF path for manual pipeline test helper."""
    return str(tmp_path / "sample.pdf")
