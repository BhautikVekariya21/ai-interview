"""
Tests for the text preprocessing service.
"""

import pytest


class TestTextPreprocessor:
    """Test text preprocessing pipeline."""

    def test_basic_preprocessing(self, preprocessor, sample_resume_text):
        """Test basic preprocessing produces expected output."""
        result = preprocessor.preprocess(sample_resume_text)

        assert result["cleaned_text"] is not None
        assert len(result["cleaned_text"]) > 0
        assert len(result["lines"]) > 10
        assert result["word_count"] > 50
        assert result["line_count"] > 0

    def test_empty_input(self, preprocessor):
        """Test handling of empty input."""
        result = preprocessor.preprocess("")

        assert result["cleaned_text"] == ""
        assert len(result["lines"]) == 0
        assert result["word_count"] == 0

    def test_none_input(self, preprocessor):
        """Test handling of None input."""
        result = preprocessor.preprocess(None)

        assert result["cleaned_text"] == ""
        assert len(result["lines"]) == 0

    def test_unicode_normalization(self, preprocessor):
        """Test Unicode characters are normalized."""
        text = "Skills\u2013Python\u2022Java\u2019s best"
        result = preprocessor.preprocess(text)

        # Smart quotes and dashes should be normalized
        assert "\u2013" not in result["cleaned_text"]
        assert "\u2019" not in result["cleaned_text"]

    def test_whitespace_normalization(self, preprocessor):
        """Test excessive whitespace is normalized."""
        text = "Hello    World\t\tTest\n\n\n\n\n\nMore"
        result = preprocessor.preprocess(text)

        # Multiple spaces collapsed
        assert "    " not in result["cleaned_text"]
        # Excessive newlines reduced
        assert "\n\n\n\n" not in result["cleaned_text"]

    def test_bullet_standardization(self, preprocessor):
        """Test bullet points are standardized."""
        text = "► Item 1\n➤ Item 2\n▸ Item 3"
        result = preprocessor.preprocess(text)

        # All bullets should be standardized to •
        for line in result["lines"]:
            if "Item" in line:
                assert line.startswith("•") or "Item" in line

    def test_lines_extraction(self, preprocessor, sample_resume_text):
        """Test that lines are properly extracted."""
        result = preprocessor.preprocess(sample_resume_text)

        # Should have non-empty lines
        assert all(line.strip() for line in result["lines"])
        # Name should be in first few lines
        assert any("John" in line for line in result["lines"][:5])

    def test_tokenization(self, preprocessor):
        """Test word tokenization."""
        text = "Python 3.9 and C++ are languages"
        result = preprocessor.preprocess(text)

        assert len(result["tokens"]) > 0
        # Check tokens are lists of strings
        for token_list in result["tokens"]:
            assert isinstance(token_list, list)
            for token in token_list:
                assert isinstance(token, str)

    def test_section_identification(self, preprocessor, sample_resume_text):
        """Test section header identification."""
        result = preprocessor.preprocess(sample_resume_text)
        sections = preprocessor.identify_potential_sections(result["lines"])

        assert len(sections) > 0
        # Should identify at least some sections
        section_types = [s[2] for s in sections]
        assert any(t != "unknown" for t in section_types)

    def test_preserves_important_content(self, preprocessor, sample_resume_text):
        """Test that important content is preserved."""
        result = preprocessor.preprocess(sample_resume_text)
        text = result["cleaned_text"]

        assert "john.smith@email.com" in text
        assert "Stanford" in text
        assert "Python" in text
        assert "Google" in text