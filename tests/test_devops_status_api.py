"""Tests for DevOps-oriented status endpoints."""

import pytest


class TestTracingStatusEndpoint:
    @pytest.mark.asyncio
    async def test_tracing_status(self, async_client):
        response = await async_client.get("/tracing/status")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] in {True, False}
        assert data["available"] in {True, False}
        assert "service_name" in data


class TestOrchestrationStatusEndpoint:
    @pytest.mark.asyncio
    async def test_orchestration_status(self, async_client):
        response = await async_client.get("/orchestration/status")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["available"] is True
        assert data["total_tools"] >= 8
        assert data["total_workflows"] >= 4

    @pytest.mark.asyncio
    async def test_detailed_status_includes_orchestration_module(self, async_client):
        response = await async_client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "module_11_orchestration" in data["modules"]
        assert data["modules"]["module_11_orchestration"]["total_tools"] >= 8


class TestOrchestrationCatalogEndpoints:
    @pytest.mark.asyncio
    async def test_orchestration_tools(self, async_client):
        response = await async_client.get("/orchestration/tools")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_tools"] >= 8
        tool_ids = {item["id"] for item in data["items"]}
        assert "resume-forensics" in tool_ids
        assert "incident-rewind" in tool_ids

    @pytest.mark.asyncio
    async def test_orchestration_workflows(self, async_client):
        response = await async_client.get("/orchestration/workflows")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_workflows"] >= 4
        workflow_ids = {item["id"] for item in data["items"]}
        assert "deep-signal-screen" in workflow_ids
        assert "executive-calibration-matrix" in workflow_ids


class TestOrchestrationPlanEndpoint:
    @pytest.mark.asyncio
    async def test_orchestration_plan_builds_complex_workflow(self, async_client):
        payload = {
            "resume_data": {
                "experience_level": "senior",
                "primary_domain": "backend platform engineering",
                "top_skills": ["Python", "Kubernetes", "Kafka", "FastAPI"],
                "projects": [
                    {
                        "title": "Realtime Fraud Detection",
                        "technologies": ["Kafka", "Redis", "PyTorch"],
                    }
                ],
                "work_experience": [
                    {"role": "Senior Platform Engineer", "company": "ExampleCorp"}
                ],
            },
            "target_role": "staff platform engineer",
            "job_description": "Lead architecture, incident response, stakeholder communication, and roadmap planning for a payments platform.",
        }

        response = await async_client.post("/orchestration/plan", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["complexity_score"] > 0
        assert len(data["recommended_tools"]) >= 4
        workflow_ids = {workflow["id"] for workflow in data["workflows"]}
        assert "failure-cascade-drill" in workflow_ids
        assert "executive-calibration-matrix" in workflow_ids
        assert any("cognitive load" in risk.lower() for risk in data["risk_flags"])
