"""
Tests for the ProviderChain-driven family ordering adopted by LLMService.

These lock in the two capabilities the shared ProviderChain adds over the old
hand-rolled phase blocks: a forced-provider override (LLM_PROVIDER) and a
configurable priority order (LLM_PROVIDER_PRIORITY).
"""

from app.services import llm_service


def build_llm_with_families(available, priority, forced=None, monkeypatch=None):
    """
    Build an LLMService whose _available_families() yields exactly `available`,
    with settings.LLM_PROVIDER_PRIORITY=`priority` and LLM_PROVIDER=`forced`.

    Bypasses __init__ (no network / no real keys); only the attributes read by
    _available_families() and _get_family_order() are populated.
    """
    service = llm_service.LLMService.__new__(llm_service.LLMService)

    # Every family off by default; switch on the requested ones.
    service._openrouter_api_key = ""
    service._groq_client = None
    service._claude_api_key = ""
    service._aiml_api_key = ""
    service._mistral_api_key = ""
    service._xai_api_key = ""
    service._gemini_models = {}
    service._hf_clients = {}

    if "openrouter" in available:
        service._openrouter_api_key = "k"
    if "groq" in available:
        service._groq_client = object()
    if "claude" in available:
        service._claude_api_key = "k"
    if "aiml" in available:
        service._aiml_api_key = "k"
    if "mistral" in available:
        service._mistral_api_key = "k"
    if "xai" in available:
        service._xai_api_key = "k"
    if "gemini" in available:
        service._gemini_models = {"gemini-x": object()}
    if "huggingface" in available:
        service._hf_clients = {"hf-x": object()}

    monkeypatch.setattr(llm_service.settings, "LLM_PROVIDER_PRIORITY", priority)
    monkeypatch.setattr(llm_service.settings, "LLM_PROVIDER", forced)
    # HuggingFace availability is env-gated regardless of clients.
    monkeypatch.setenv("ENABLE_HUGGINGFACE_FALLBACK", "true")
    return service


def test_family_order_follows_priority_setting(monkeypatch):
    service = build_llm_with_families(
        available=["groq", "openrouter", "gemini"],
        priority=["openrouter", "groq", "claude", "aiml", "mistral", "xai", "gemini", "huggingface"],
        monkeypatch=monkeypatch,
    )
    assert service._get_family_order() == ["openrouter", "groq", "gemini"]


def test_reordering_priority_changes_family_order(monkeypatch):
    # Same available families, but gemini promoted ahead of openrouter.
    service = build_llm_with_families(
        available=["groq", "openrouter", "gemini"],
        priority=["gemini", "groq", "openrouter"],
        monkeypatch=monkeypatch,
    )
    assert service._get_family_order() == ["gemini", "groq", "openrouter"]


def test_forced_provider_moves_to_front(monkeypatch):
    service = build_llm_with_families(
        available=["openrouter", "groq", "gemini"],
        priority=["openrouter", "groq", "claude", "aiml", "mistral", "xai", "gemini", "huggingface"],
        forced="gemini",
        monkeypatch=monkeypatch,
    )
    order = service._get_family_order()
    assert order[0] == "gemini"
    assert set(order) == {"openrouter", "groq", "gemini"}


def test_forced_unavailable_provider_is_ignored(monkeypatch):
    # claude is forced but has no key → fall back to priority order.
    service = build_llm_with_families(
        available=["openrouter", "groq"],
        priority=["openrouter", "groq", "claude", "aiml", "mistral", "xai", "gemini", "huggingface"],
        forced="claude",
        monkeypatch=monkeypatch,
    )
    assert service._get_family_order() == ["openrouter", "groq"]


def test_requested_preferred_takes_precedence(monkeypatch):
    service = build_llm_with_families(
        available=["openrouter", "groq", "gemini"],
        priority=["openrouter", "groq", "claude", "aiml", "mistral", "xai", "gemini", "huggingface"],
        monkeypatch=monkeypatch,
    )
    order = service._get_family_order(preferred="groq")
    assert order[0] == "groq"
    assert set(order) == {"openrouter", "groq", "gemini"}


def test_huggingface_requires_env_flag(monkeypatch):
    service = build_llm_with_families(
        available=["groq", "huggingface"],
        priority=["groq", "huggingface"],
        monkeypatch=monkeypatch,
    )
    # Flag on (set by builder) → huggingface present.
    assert service._get_family_order() == ["groq", "huggingface"]
    # Flag off → huggingface filtered out even with clients loaded.
    monkeypatch.setenv("ENABLE_HUGGINGFACE_FALLBACK", "false")
    assert service._get_family_order() == ["groq"]
