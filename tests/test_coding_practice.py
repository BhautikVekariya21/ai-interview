"""
Coding practice endpoint tests.
"""

import pytest


class TestCodingPracticeProblems:
    @pytest.mark.asyncio
    async def test_problem_list_returns_full_backend_dataset(self, async_client):
        response = await async_client.get("/coding-practice/problems")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 100
        assert data[0]["title"]

    @pytest.mark.asyncio
    async def test_problem_detail_includes_language_templates(self, async_client):
        response = await async_client.get("/coding-practice/problems/1")

        assert response.status_code == 200
        data = response.json()
        assert "starterTemplates" in data
        assert "python" in data["starterTemplates"]
        assert "javascript" in data["starterTemplates"]
        assert "java" in data["starterTemplates"]

    @pytest.mark.asyncio
    async def test_language_list_includes_requested_languages(self, async_client):
        response = await async_client.get("/coding-practice/languages")

        assert response.status_code == 200
        data = response.json()
        ids = {item["id"] for item in data}
        assert {"python", "javascript", "java", "cpp", "c", "rust"}.issubset(ids)


class TestCodingPracticeExecution:
    @pytest.mark.asyncio
    async def test_execute_endpoint_returns_execution_payload(self, async_client, monkeypatch):
        from app.api import coding_practice_routes

        monkeypatch.setattr(
            coding_practice_routes,
            "execute_problem",
            lambda problem_id, code, language: {
                "success": True,
                "language": language,
                "provider": "judge0",
                "total_tests": 3,
                "passed_tests": 3,
                "all_passed": True,
                "results": [
                    {
                        "input": "[[2,7,11,15],9]",
                        "expected": "[0,1]",
                        "actual": "[0,1]",
                        "passed": True,
                        "error": None,
                        "time_ms": 12.0,
                        "status": "Accepted",
                    }
                ]
                * 3,
            },
        )

        response = await async_client.post(
            "/coding-practice/execute/1",
            json={"language": "python", "code": "def solve(nums, target): return [0, 1]"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "python"
        assert data["provider"] == "judge0"
        assert data["all_passed"] is True
        assert data["passed_tests"] == data["total_tests"]
