"""
Tests for the file extraction service.
"""

import pytest
from app.core.exceptions import (
    UnsupportedFileFormatError,
    FileSizeLimitError,
    EmptyResumeError,
    FileExtractionError,
)


class TestFileExtractor:
    """Test file extraction from different formats."""

    @pytest.mark.asyncio
    async def test_extract_txt_file(self, file_extractor, sample_resume_bytes):
        """Test extracting text from a .txt file."""
        text, ext = await file_extractor.extract(
            sample_resume_bytes, "resume.txt"
        )
        assert len(text) > 100
        assert ext == ".txt"
        assert "John Smith" in text
        assert "john.smith@email.com" in text

    @pytest.mark.asyncio
    async def test_extract_preserves_content(self, file_extractor, sample_resume_bytes):
        """Test that important content is preserved."""
        text, _ = await file_extractor.extract(
            sample_resume_bytes, "resume.txt"
        )
        assert "Stanford University" in text
        assert "Python" in text
        assert "Google" in text
        assert "EDUCATION" in text

    @pytest.mark.asyncio
    async def test_reject_unsupported_format(self, file_extractor):
        """Test that unsupported formats raise error."""
        with pytest.raises(UnsupportedFileFormatError):
            await file_extractor.extract(b"test content", "resume.xyz")

    @pytest.mark.asyncio
    async def test_reject_unsupported_format_jpg(self, file_extractor):
        """Test that image files without OCR available raise an extraction error."""
        # .jpg is a supported format handled via OCR; when Tesseract isn't
        # installed (as in this test environment), extraction fails instead
        # of the format being rejected outright.
        with pytest.raises(FileExtractionError):
            await file_extractor.extract(b"fake image", "photo.jpg")

    @pytest.mark.asyncio
    async def test_reject_oversized_file(self, file_extractor):
        """Test that files exceeding size limit are rejected."""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(FileSizeLimitError):
            await file_extractor.extract(large_content, "big.txt")

    @pytest.mark.asyncio
    async def test_reject_empty_file(self, file_extractor):
        """Test that empty/minimal files are rejected."""
        with pytest.raises(EmptyResumeError):
            await file_extractor.extract(b"", "empty.txt")

    @pytest.mark.asyncio
    async def test_reject_too_short_content(self, file_extractor):
        """Test that very short content is rejected."""
        with pytest.raises(EmptyResumeError):
            await file_extractor.extract(b"Hi", "short.txt")

    @pytest.mark.asyncio
    async def test_handle_utf8_encoding(self, file_extractor):
        """Test handling of UTF-8 encoded files."""
        content = "Résumé of José García\nSkills: café, naïve Bayes\n" * 5
        text, _ = await file_extractor.extract(
            content.encode("utf-8"), "resume.txt"
        )
        assert "José" in text or "Jose" in text

    @pytest.mark.asyncio
    async def test_handle_latin1_encoding(self, file_extractor):
        """Test handling of Latin-1 encoded files."""
        content = "Resume content here\nWith enough text to pass validation\n" * 5
        text, _ = await file_extractor.extract(
            content.encode("latin-1"), "resume.txt"
        )
        assert len(text) > 50

    @pytest.mark.asyncio
    async def test_different_txt_extensions(self, file_extractor, sample_resume_bytes):
        """Test .txt extension works."""
        text, ext = await file_extractor.extract(
            sample_resume_bytes, "my_resume.txt"
        )
        assert ext == ".txt"
        assert len(text) > 100