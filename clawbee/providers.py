"""Model-agnostic provider adapter.

Design (from research/mcp-models.md): OpenAI-compatible Chat Completions
is the narrow waist; LiteLLM Proxy (MIT core) is the only gateway in
production. This prototype implements the adapter *interface* with a
deterministic stub backend — no network, no API keys, no inference —
so orchestration and factory logic are testable without any provider.

Production backends (not in this prototype): Ollama (dev) -> vLLM/SGLang
(prod GPU) -> llama.cpp (CPU/edge) -> OpenRouter / HF Inference Providers.
Fallback chains must fail closed, never silently swap model or licence.
"""
from __future__ import annotations


class ProviderError(RuntimeError):
    pass


class ProviderAdapter:
    """Interface every provider backend must implement."""

    name = "base"

    def complete(self, messages: list[dict], **kwargs) -> dict:
        raise NotImplementedError

    def health(self) -> dict:
        return {"adapter": self.name, "ok": True}


class StubAdapter(ProviderAdapter):
    """Deterministic echo stub for local testing. Returns the last user
    message prefixed, so tests can assert routing without any model."""

    name = "stub"

    def complete(self, messages: list[dict], **kwargs) -> dict:
        user_text = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_text = m.get("content", "")
                break
        return {
            "adapter": "stub",
            "model": kwargs.get("model", "stub-0"),
            "content": f"[stub] {user_text}",
            "usage": {"prompt_tokens": len(user_text), "completion_tokens": len(user_text) + 7},
        }


def get_adapter(name: str) -> ProviderAdapter:
    adapters = {"stub": StubAdapter}
    if name not in adapters:
        raise ProviderError(
            f"unknown provider adapter {name!r}; available: {sorted(adapters)} "
            "(production backends are configured via LiteLLM Proxy, not here)"
        )
    return adapters[name]()


def litellm_config(models: list[dict]) -> dict:
    """Build a LiteLLM Proxy model_list config (data only, no network).
    Each model: {model_name, litellm_params: {model, api_base?}}.
    """
    if not models:
        raise ProviderError("litellm_config needs at least one model")
    return {
        "model_list": [
            {"model_name": m["model_name"], "litellm_params": m["litellm_params"]}
            for m in models
        ],
        "general_settings": {"master_key": "env://LITELLM_MASTER_KEY"},
    }
