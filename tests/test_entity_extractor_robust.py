"""
Robust parsing tests for EntityExtractor edge cases.
"""


def test_extract_date_range_month_year(entity_extractor):
    text = "Senior Engineer at ACME | Jan 2021 - Present"
    dr = entity_extractor._extract_date_range(text)
    assert dr is not None
    assert "2021" in dr


def test_parse_experience_header_line_with_at_pattern(entity_extractor):
    line = "Senior Software Engineer at Google | 2021 - Present"
    parsed = entity_extractor._parse_experience_header_line(line)
    assert parsed is not None
    assert parsed.get("role", "").lower().startswith("senior software engineer")
    assert parsed.get("company", "").lower() == "google"
    assert "date_range" in parsed


def test_parse_experience_section_handles_mixed_headers(entity_extractor):
    lines = [
        "Senior Software Engineer at Google | 2021 - Present",
        "- Led migration from monolith to microservices",
        "- Reduced latency by 40%",
        "",
        "Software Engineer - Amazon - 2019 - 2021",
        "- Built ETL pipelines processing 500GB daily",
    ]
    entries = entity_extractor._parse_experience_section(lines)
    assert len(entries) >= 2
    assert any("google" in (e.get("company", "").lower()) for e in entries)
    assert any("amazon" in (e.get("company", "").lower()) for e in entries)
    assert any(len(e.get("responsibilities", [])) >= 1 for e in entries)


def test_parse_education_section_infers_institution_and_dedup(entity_extractor):
    lines = [
        "Master of Science in Computer Science",
        "Stanford University",
        "GPA: 3.9/4.0",
        "2019 - 2021",
        "",
        "Master of Science in Computer Science",
        "Stanford University",
        "2019 - 2021",
    ]
    entries = entity_extractor._parse_education_section(lines)
    assert len(entries) >= 1
    assert any("stanford" in (e.get("institution", "").lower()) for e in entries)
    # dedupe should not explode duplicates
    assert len(entries) <= 2
