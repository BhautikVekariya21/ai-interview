use once_cell::sync::Lazy;
use pyo3::prelude::*;
use regex::Regex;
use unicode_normalization::UnicodeNormalization;

static MULTISPACE_RE: Lazy<Regex> = Lazy::new(|| Regex::new(r"[^\S\n]+").unwrap());
static TRAILING_SPACE_RE: Lazy<Regex> = Lazy::new(|| Regex::new(r" +\n").unwrap());
static MULTINEWLINE_RE: Lazy<Regex> = Lazy::new(|| Regex::new(r"\n{3,}").unwrap());
static BULLET_RE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?m)^[\s]*[\u{2022}\u{25cf}\u{25cb}\u{25aa}\u{25b8}\u{25ba}\u{27a4}\u{27a2}\-\u{2013}\u{2014}\*\+>]\s*").unwrap()
});
static SKILL_CLEAN_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"[^\w\s.\#+/\-]").unwrap());
static TOKEN_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"[A-Za-z0-9+#\.-]+").unwrap());
static PREPROCESS_TOKEN_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"\b[\w+#.]+\b|[^\w\s]").unwrap());
static SENTENCE_SPLIT_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"[.!?\n]+").unwrap());
static PROJECT_HINT_RE: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"(?i)\b(project|built|developed|implemented)\b").unwrap());

fn apply_unicode_replacements(input: &str) -> String {
    input
        .replace('\u{2018}', "'")
        .replace('\u{2019}', "'")
        .replace('\u{201c}', "\"")
        .replace('\u{201d}', "\"")
        .replace('\u{2013}', "-")
        .replace('\u{2014}', "-")
        .replace('\u{2022}', "\u{2022}")
        .replace('\u{2026}', "...")
        .replace('\u{00a0}', " ")
        .replace('\u{f0b7}', "\u{2022}")
        .replace('\u{f0a7}', "\u{2022}")
}

#[pyfunction]
fn normalize_unicode(text: &str) -> String {
    apply_unicode_replacements(text).nfkd().collect()
}

#[pyfunction]
fn normalize_whitespace(text: &str) -> String {
    let tabs = text.replace('\t', "    ");
    let compact = MULTISPACE_RE.replace_all(&tabs, " ");
    let trimmed_lines = TRAILING_SPACE_RE.replace_all(&compact, "\n");
    let collapsed = MULTINEWLINE_RE.replace_all(&trimmed_lines, "\n\n");
    collapsed.trim().to_string()
}

#[pyfunction]
fn standardize_bullets(text: &str) -> String {
    BULLET_RE.replace_all(text, "\u{2022} ").to_string()
}

#[pyfunction]
fn extract_lines(text: &str) -> Vec<String> {
    text.lines()
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .map(str::to_string)
        .collect()
}

#[pyfunction]
fn normalize_skill_text(text: &str) -> String {
    let lowered = text.trim().to_lowercase();
    SKILL_CLEAN_RE.replace_all(&lowered, "").trim().to_string()
}

#[pyfunction]
fn tokenize_words(text: &str) -> Vec<String> {
    TOKEN_RE
        .find_iter(&text.to_lowercase())
        .map(|m| m.as_str().to_string())
        .collect()
}

#[pyfunction]
fn tokenize_preprocessor(text: &str) -> Vec<String> {
    PREPROCESS_TOKEN_RE
        .find_iter(text)
        .map(|m| m.as_str().to_string())
        .collect()
}

#[pyfunction]
fn split_sentences(text: &str) -> Vec<String> {
    SENTENCE_SPLIT_RE
        .split(text)
        .map(str::trim)
        .filter(|part| !part.is_empty())
        .map(str::to_string)
        .collect()
}

#[pyfunction]
fn dedupe_strings(items: Vec<String>) -> Vec<String> {
    let mut seen = std::collections::HashSet::new();
    let mut out = Vec::new();

    for item in items {
        let key = item.to_lowercase();
        if seen.insert(key) {
            out.push(item);
        }
    }

    out
}

#[pyfunction]
fn fallback_project_lines(text: &str, max_len: usize) -> Vec<String> {
    let mut out = Vec::new();
    for line in text.lines().map(str::trim).filter(|line| !line.is_empty()) {
        if PROJECT_HINT_RE.is_match(line) && line.len() >= 6 && line.len() <= 120 {
            let truncated: String = line.chars().take(max_len).collect();
            out.push(truncated);
        }
    }
    dedupe_strings(out)
}

#[pymodule]
fn ai_interview_accel(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(normalize_unicode, module)?)?;
    module.add_function(wrap_pyfunction!(normalize_whitespace, module)?)?;
    module.add_function(wrap_pyfunction!(standardize_bullets, module)?)?;
    module.add_function(wrap_pyfunction!(extract_lines, module)?)?;
    module.add_function(wrap_pyfunction!(normalize_skill_text, module)?)?;
    module.add_function(wrap_pyfunction!(tokenize_words, module)?)?;
    module.add_function(wrap_pyfunction!(tokenize_preprocessor, module)?)?;
    module.add_function(wrap_pyfunction!(split_sentences, module)?)?;
    module.add_function(wrap_pyfunction!(dedupe_strings, module)?)?;
    module.add_function(wrap_pyfunction!(fallback_project_lines, module)?)?;
    Ok(())
}
