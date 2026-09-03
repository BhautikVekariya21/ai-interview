"""
Pydantic schemas defining the structured JSON output of the resume parser.
Every field includes confidence scores and optional metadata.
"""

from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator
from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"        # > 0.85
    MEDIUM = "medium"    # 0.6 - 0.85
    LOW = "low"          # < 0.6


class ExtractionMeta(BaseModel):
    """Metadata about how a field was extracted."""
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score of extraction"
    )
    source: str = Field(
        description="Extraction method: 'ner', 'regex', 'heuristic', 'spacy'"
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Original text from which this was extracted"
    )


class PersonalInfo(BaseModel):
    """Candidate's personal/contact information."""
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    meta: Dict[str, ExtractionMeta] = Field(default_factory=dict)


class Education(BaseModel):
    """Single education entry."""
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    gpa: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    gpa_scale: Optional[float] = Field(default=4.0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    honors: Optional[str] = None
    relevant_coursework: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class WorkExperience(BaseModel):
    """Single work experience entry."""
    company: str
    role: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    duration_months: Optional[int] = None
    responsibilities: List[str] = Field(default_factory=list)
    technologies_used: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Skill(BaseModel):
    """Individual skill with categorization."""
    name: str
    category: str = Field(
        description="Category: 'language', 'framework', 'tool', "
                    "'platform', 'database', 'methodology', 'soft_skill', 'other'"
    )
    proficiency_level: Optional[str] = Field(
        default=None,
        description="Proficiency: 'beginner', 'intermediate', 'advanced', 'expert'"
    )
    years_of_experience: Optional[float] = None
    last_used: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Project(BaseModel):
    """Single project entry."""
    title: str
    description: Optional[str] = None
    role: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Certification(BaseModel):
    """Single certification entry."""
    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Publication(BaseModel):
    """Single publication entry."""
    title: str
    authors: List[str] = Field(default_factory=list)
    venue: Optional[str] = None  # journal, conference, etc.
    date: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class Achievement(BaseModel):
    """Single achievement/award entry."""
    title: str
    description: Optional[str] = None
    date: Optional[str] = None
    issuer: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExperienceLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"          # 0-2 years
    MID_LEVEL = "mid_level"    # 2-5 years
    SENIOR = "senior"          # 5-10 years
    LEAD = "lead"              # 10+ years
    EXECUTIVE = "executive"


class ParsedResume(BaseModel):
    """
    Complete structured output of the resume parser.
    This is the master schema that Module 2 (Question Generator) consumes.
    """
    # === Core Sections ===
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    education: List[Education] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)

    # === Derived Metadata ===
    total_experience_years: float = Field(
        default=0.0,
        description="Calculated total years of professional experience"
    )
    experience_level: ExperienceLevel = Field(
        default=ExperienceLevel.JUNIOR,
        description="Inferred experience level"
    )
    primary_domain: Optional[str] = Field(
        default=None,
        description="Primary professional domain (e.g., 'backend', 'ML', 'frontend')"
    )
    top_skills: List[str] = Field(
        default_factory=list,
        description="Top 10 most prominent skills"
    )
    skill_categories: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Skills grouped by category"
    )

    # === Parser Metadata ===
    parser_version: str = "1.0.0"
    parse_timestamp: Optional[str] = None
    source_file_name: Optional[str] = None
    source_file_type: Optional[str] = None
    raw_text_length: int = 0
    overall_parse_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Overall confidence in the parsing quality"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Any parsing warnings or issues encountered"
    )


class ResumeUploadResponse(BaseModel):
    """API response wrapper for resume upload."""
    success: bool
    message: str
    data: Optional[ParsedResume] = None
    plagiarism_report: Optional[Dict[str, Any]] = None
    ats_report: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class HealthCheckResponse(BaseModel):
    """API health check response."""
    status: str
    version: str
    ner_model_loaded: bool
    uptime_seconds: float


class ResumeAnalyticsRequest(BaseModel):
    """Batch analytics request for resume datasets."""
    resumes: List[Dict[str, Any]] = Field(default_factory=list)
    dataset_path: Optional[str] = None
    top_n: int = Field(default=10, ge=1, le=50)

    @field_validator("dataset_path")
    @classmethod
    def normalize_dataset_path(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ResumeAnalyticsSummary(BaseModel):
    total_resumes: int
    average_experience_years: float
    experience_level_distribution: Dict[str, int] = Field(default_factory=dict)
    top_skills: List[Dict[str, Any]] = Field(default_factory=list)
    top_domains: List[Dict[str, Any]] = Field(default_factory=list)
    top_companies: List[Dict[str, Any]] = Field(default_factory=list)


class ResumeAnalyticsResponse(BaseModel):
    success: bool
    engine: str
    storage: str
    dataset_path: Optional[str] = None
    summary: ResumeAnalyticsSummary


class AnalyticsEngineStatus(BaseModel):
    enabled: bool
    available: bool
    engine: str
    master_url: str



class TracingStatusResponse(BaseModel):
    enabled: bool
    available: bool
    service_name: str
    exporter_endpoint: Optional[str] = None
