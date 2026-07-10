from types import SimpleNamespace

from app.core.config import Settings
from app.services import llm_service


class DummyCache:
    def __init__(self):
        self.store = {}

    def make_key(self, namespace: str, payload: str) -> str:
        return f"{namespace}:{payload}"

    def get(self, key: str):
        return self.store.get(key)

    def set(self, key: str, value, ttl_seconds: int | None = None):
        self.store[key] = value


class DummyGroqCompletions:
    def __init__(self):
        self.calls = []

    def create(self, *, model, messages, temperature, max_tokens, top_p):
        self.calls.append(model)
        if model == "bad-model":
            raise Exception(
                "The model `bad-model` has been decommissioned and is no longer supported."
            )

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="This is a healthy fallback response with enough text to pass."
                    )
                )
            ]
        )


class DummyGroqClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=DummyGroqCompletions())


def build_llm_with_groq_queue(groq_client: DummyGroqClient):
    service = llm_service.LLMService.__new__(llm_service.LLMService)
    service._openrouter_api_key = ""
    service._openrouter_model_queue = []
    service._claude_api_key = ""
    service._claude_model_queue = []
    service._aiml_api_key = ""
    service._aiml_model_queue = []
    service._mistral_api_key = ""
    service._mistral_model_queue = []
    service._groq_client = groq_client
    service._groq_model_queue = ["bad-model", "good-model"]
    service._xai_api_key = ""
    service._xai_model_queue = []
    service._gemini_api_key = ""
    service._gemini_model_queue = []
    service._hf_api_key = ""
    service._hf_model_queue = []
    service._hf_clients = {}
    service._cache = DummyCache()
    service.active_provider = None
    service.available_providers = ["groq:bad-model", "groq:good-model"]
    service._failure_counts = {"groq:bad-model": 0, "groq:good-model": 0}
    service._last_failure_time = {"groq:bad-model": 0.0, "groq:good-model": 0.0}
    return service


def test_generate_skips_decommissioned_groq_model_without_retrying_dead_model():
    groq_client = DummyGroqClient()
    service = build_llm_with_groq_queue(groq_client)

    result = service.generate(
        prompt="Write one paragraph about backend engineering.",
        system_prompt="Be concise.",
        max_tokens=200,
    )

    assert result == "This is a healthy fallback response with enough text to pass."
    assert groq_client.chat.completions.calls == ["bad-model", "good-model"]
    assert service.active_provider == "groq:good-model"


def test_settings_filter_decommissioned_groq_model_from_env_override(monkeypatch):
    monkeypatch.setenv(
        "GROQ_MODEL_QUEUE",
        '["llama-3.1-70b-versatile","llama-3.3-70b-versatile","mixtral-8x7b-32768"]',
    )

    settings = Settings()

    assert settings.GROQ_MODEL_QUEUE == [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
    ]
