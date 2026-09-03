"""
Tests for the skill normalization service.
"""

import pytest


class TestSkillNormalizer:
    """Test skill normalization and categorization."""

    def test_exact_match(self, skill_normalizer):
        """Test exact skill name matching."""
        results = skill_normalizer.normalize(["Python"])
        assert len(results) == 1
        assert results[0]["name"] == "Python"
        assert results[0]["confidence"] == 1.0
        assert results[0]["category"] == "languages"

    def test_case_insensitive_match(self, skill_normalizer):
        """Test case-insensitive matching."""
        results = skill_normalizer.normalize(["python"])
        assert len(results) == 1
        assert results[0]["name"] == "Python"

    def test_alias_match(self, skill_normalizer):
        """Test matching by alias."""
        results = skill_normalizer.normalize(["nodejs"])
        assert len(results) == 1
        assert results[0]["name"] == "Node.js"

    def test_alias_match_react(self, skill_normalizer):
        """Test React alias matching."""
        results = skill_normalizer.normalize(["reactjs"])
        assert len(results) == 1
        assert results[0]["name"] == "React"

    def test_fuzzy_match(self, skill_normalizer):
        """Test fuzzy skill matching."""
        results = skill_normalizer.normalize(["scikit learn"])
        assert len(results) == 1
        assert results[0]["name"] == "scikit-learn"

    def test_multiple_skills(self, skill_normalizer):
        """Test normalizing multiple skills."""
        results = skill_normalizer.normalize([
            "Python", "React", "Docker", "PostgreSQL"
        ])
        assert len(results) == 4
        names = {r["name"] for r in results}
        assert "Python" in names
        assert "React" in names
        assert "Docker" in names
        assert "PostgreSQL" in names

    def test_deduplication(self, skill_normalizer):
        """Test that duplicate skills are removed."""
        results = skill_normalizer.normalize([
            "Python", "python", "python3", "PYTHON"
        ])
        assert len(results) == 1
        assert results[0]["name"] == "Python"

    def test_category_assignment(self, skill_normalizer):
        """Test correct category assignment."""
        test_cases = [
            ("Python", "languages"),
            ("React", "frameworks"),
            ("PyTorch", "ml_frameworks"),
            ("PostgreSQL", "databases"),
            ("Docker", "tools"),
            ("AWS", "platforms"),
        ]

        for skill_name, expected_cat in test_cases:
            results = skill_normalizer.normalize([skill_name])
            assert len(results) == 1, f"No result for {skill_name}"
            assert results[0]["category"] == expected_cat, \
                f"{skill_name}: expected {expected_cat}, got {results[0]['category']}"

    def test_unknown_skill(self, skill_normalizer):
        """Test handling of unknown skills."""
        results = skill_normalizer.normalize(["SomeObscureLibrary123"])
        assert len(results) == 1
        assert results[0]["category"] == "other"
        assert results[0]["confidence"] < 0.5

    def test_categorize_skills(self, skill_normalizer):
        """Test skill grouping by category."""
        results = skill_normalizer.normalize([
            "Python", "Java", "React", "Docker", "PostgreSQL"
        ])
        categories = skill_normalizer.categorize_skills(results)

        assert "languages" in categories
        assert "Python" in categories["languages"]
        assert "frameworks" in categories
        assert "tools" in categories

    def test_empty_input(self, skill_normalizer):
        """Test handling of empty input."""
        results = skill_normalizer.normalize([])
        assert len(results) == 0

    def test_whitespace_skill(self, skill_normalizer):
        """Test handling of whitespace-only skills."""
        results = skill_normalizer.normalize(["", "  ", "\t"])
        assert len(results) == 0

    def test_golang_alias(self, skill_normalizer):
        """Test Go/Golang alias."""
        results = skill_normalizer.normalize(["golang"])
        assert len(results) == 1
        assert results[0]["name"] == "Go"

    def test_csharp_alias(self, skill_normalizer):
        """Test C# alias."""
        results = skill_normalizer.normalize(["csharp"])
        assert len(results) == 1
        assert results[0]["name"] == "C#"

    def test_k8s_alias(self, skill_normalizer):
        """Test Kubernetes alias."""
        results = skill_normalizer.normalize(["k8s"])
        assert len(results) == 1
        assert results[0]["name"] == "Kubernetes"
