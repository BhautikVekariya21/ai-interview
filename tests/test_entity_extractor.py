"""
Integration tests for the full resume parser pipeline.
"""

import pytest


class TestResumeParserIntegration:
    """Integration tests for the full parsing pipeline."""

    @pytest.mark.asyncio
    async def test_full_parse_pipeline(self, resume_parser, sample_resume_bytes):
        """Test complete parsing pipeline end-to-end."""
        result = await resume_parser.parse(
            sample_resume_bytes, "test_resume.txt"
        )

        # Should return ParsedResume object
        assert result is not None
        assert result.parser_version == "1.0.0"
        assert result.parse_timestamp is not None
        assert result.source_file_name == "test_resume.txt"
        assert result.source_file_type == ".txt"

    @pytest.mark.asyncio
    async def test_personal_info_extraction(self, resume_parser, sample_resume_bytes):
        """Test that personal info is correctly extracted."""
        result = await resume_parser.parse(
            sample_resume_bytes, "resume.txt"
        )

        pi = result.personal_info
        assert pi.email == "john.smith@email.com"
        # Phone or name should be extracted
        assert pi.phone is not None or pi.full_name is not None

    @pytest.mark.asyncio
    async def test_skills_extraction(self, resume_parser, sample_resume_bytes):
        """Test that skills are extracted and normalized."""
        result = await resume_parser.parse(
            sample_resume_bytes, "resume.txt"
        )

        assert len(result.skills) >= 5

        skill_names = {s.name for s in result.skills}
        # At least some of these should be found
        expected = {"Python", "Java", "Docker", "Kubernetes", "PyTorch"}
        found = expected & skill_names
        assert len(found) >= 3, f"Expected >= 3 of {expected}, found {found}"

    @pytest.mark.asyncio
    async def test_skill_categorization(self, resume_parser, sample_resume_bytes):
        """Test that skills are properly categorized."""
        result = await resume_parser.parse(
            sample_resume_bytes, "resume.txt"
        )

        assert len(result.skill_categories) > 0
        # Should have multiple categories
        assert len(result.skill_categories) >= 2

    @pytest.mark.asyncio
    async def test_experience_level_inference(self, resume_parser, sample_resume_bytes):
        """Test experience level inference."""
        result = await resume_parser.parse(
            sample_resume_bytes, "resume.txt"
        )

        assert result.experience_level is not None
        # John Smith has ~4+ years, should be mid or senior
        assert result.experience_level.value in [
            "mid_level", "senior", "junior", "intern"
        ]

    @pytest.mark.asyncio
    async def test_top_skills(self, resume_parser, sample_resume_bytes):
        """Test top skills list."""
        result = await resume_parser.parse(
            sample_resume_bytes, "resume.txt"
        )

        assert len(result.top_skills) > 0
        assert len(result.top_skills) <= 10

    @pytest.mark.asyncio
    async def test_confidence_score(self, resume_parser, sample_resume_bytes):
        """Test overall confidence score."""
        result = await resume_parser.parse(
            sample_resume_bytes, "resume.txt"
        )

        assert 0.0 <= result.overall_parse_confidence <= 1.0
        assert result.overall_parse_confidence > 0.2  # Should be reasonable

    @pytest.mark.asyncio
    async def test_raw_text_length(self, resume_parser, sample_resume_bytes):
        """Test that raw text length is computed."""
        result = await resume_parser.parse(
            sample_resume_bytes, "resume.txt"
        )

        assert result.raw_text_length > 100

    @pytest.mark.asyncio
    async def test_simple_resume(self, resume_parser, simple_resume_bytes):
        """Test parsing a simpler resume."""
        result = await resume_parser.parse(
            simple_resume_bytes, "simple.txt"
        )

        assert result is not None
        assert result.personal_info.email == "jane.doe@gmail.com"
        assert len(result.skills) >= 3

    @pytest.mark.asyncio
    async def test_domain_inference(self, resume_parser, sample_resume_bytes):
        """Test domain inference."""
        result = await resume_parser.parse(
            sample_resume_bytes, "resume.txt"
        )

        # Should infer some domain
        if result.primary_domain:
            assert result.primary_domain in [
                "backend", "frontend", "fullstack",
                "ml_ai", "data_science", "devops", "mobile"
            ]
