"""
API endpoint tests using FastAPI TestClient.
"""

import pytest


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """Test /health returns 200 with correct schema."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "ner_model_loaded" in data
        assert "uptime_seconds" in data

    @pytest.mark.asyncio
    async def test_health_check_uptime(self, async_client):
        """Test that uptime is a positive number."""
        response = await async_client.get("/health")
        data = response.json()
        assert data["uptime_seconds"] >= 0


class TestParseResumeEndpoint:
    """Test resume parsing endpoint."""

    @pytest.mark.asyncio
    async def test_parse_txt_resume(self, async_client, sample_resume_bytes):
        """Test parsing a TXT resume."""
        response = await async_client.post(
            "/parse-resume",
            files={"file": ("resume.txt", sample_resume_bytes, "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is not None
        assert data["processing_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_parse_returns_email(self, async_client, sample_resume_bytes):
        """Test that email is extracted."""
        response = await async_client.post(
            "/parse-resume",
            files={"file": ("resume.txt", sample_resume_bytes, "text/plain")},
        )

        data = response.json()
        assert data["data"]["personal_info"]["email"] == "john.smith@email.com"

    @pytest.mark.asyncio
    async def test_parse_returns_skills(self, async_client, sample_resume_bytes):
        """Test that skills are returned."""
        response = await async_client.post(
            "/parse-resume",
            files={"file": ("resume.txt", sample_resume_bytes, "text/plain")},
        )

        data = response.json()
        assert len(data["data"]["skills"]) >= 3

    @pytest.mark.asyncio
    async def test_reject_unsupported_format(self, async_client):
        """Test that unsupported formats return 415."""
        response = await async_client.post(
            "/parse-resume",
            files={"file": ("resume.xyz", b"test content", "application/octet-stream")},
        )
        assert response.status_code == 415

    @pytest.mark.asyncio
    async def test_reject_empty_file(self, async_client):
        """Test that empty files return 400."""
        response = await async_client.post(
            "/parse-resume",
            files={"file": ("resume.txt", b"", "text/plain")},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_simple_resume_parse(self, async_client, simple_resume_bytes):
        """Test parsing a simple resume."""
        response = await async_client.post(
            "/parse-resume",
            files={"file": ("simple.txt", simple_resume_bytes, "text/plain")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["personal_info"]["email"] == "jane.doe@gmail.com"


class TestSupportedSkillsEndpoint:
    """Test supported skills endpoint."""

    @pytest.mark.asyncio
    async def test_list_skills(self, async_client):
        """Test /supported-skills returns skill taxonomy."""
        response = await async_client.get("/supported-skills")

        assert response.status_code == 200
        data = response.json()
        assert data["total_skills"] > 50
        assert "categories" in data
        assert "languages" in data["categories"]
        assert "Python" in data["categories"]["languages"]

    @pytest.mark.asyncio
    async def test_skills_have_multiple_categories(self, async_client):
        """Test that multiple categories exist."""
        response = await async_client.get("/supported-skills")
        data = response.json()
        assert len(data["categories"]) >= 5


class TestNERTagsEndpoint:
    """Test NER tags endpoint."""

    @pytest.mark.asyncio
    async def test_list_ner_tags(self, async_client):
        """Test /ner-tags returns tag information."""
        response = await async_client.get("/ner-tags")

        assert response.status_code == 200
        data = response.json()
        assert data["total_tags"] > 10
        assert "SKILL" in data["entity_types"]
        assert "NAME" in data["entity_types"]

    @pytest.mark.asyncio
    async def test_ner_tags_include_bio(self, async_client):
        """Test that tags include BIO format tags."""
        response = await async_client.get("/ner-tags")
        data = response.json()
        assert "B-SKILL" in data["tags"]
        assert "I-SKILL" in data["tags"]
        assert "O" in data["tags"]


class TestRootEndpoint:
    """Test root endpoint."""

    @pytest.mark.asyncio
    async def test_root(self, async_client):
        """Test / returns service info."""
        response = await async_client.get("/")

        assert response.status_code == 200


class TestFrontend:
    """Test frontend serving."""

    @pytest.mark.asyncio
    async def test_frontend_served(self, async_client):
        """Test that frontend HTML is served at root."""
        response = await async_client.get("/")
        assert response.status_code == 200
