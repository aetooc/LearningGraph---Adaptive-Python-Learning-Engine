import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.errors import ApplicationError
from app.schemas import LessonDraft
from app.services.llm import OpenAIGenerator
from tests.drafts import valid_lesson


@pytest.fixture
def sdk(monkeypatch):
    # Replace only the SDK boundary: exercise our configuration and request logic
    # without dependencies on installed SDK packages, keys, or external requests.
    module = ModuleType("openai")
    module.OpenAI = MagicMock()
    module.OpenAIError = type("OpenAIError", (Exception,), {})
    module.APIConnectionError = type("APIConnectionError", (module.OpenAIError,), {})
    module.APITimeoutError = type("APITimeoutError", (module.APIConnectionError,), {})
    monkeypatch.setitem(sys.modules, "openai", module)
    client = module.OpenAI.return_value.__enter__.return_value
    client.responses.parse.return_value = SimpleNamespace(output_parsed=LessonDraft.model_validate(valid_lesson()))
    return module, client


@pytest.mark.parametrize("provider,key_name,model_name,base_url", [
    ("openai", "openai_api_key", "openai_model", "https://api.openai.com/v1"),
    ("groq", "groq_api_key", "groq_model", "https://api.groq.com/openai/v1"),
])
def test_selected_provider_controls_endpoint_key_and_configured_model(sdk, provider, key_name, model_name, base_url):
    module, client = sdk
    settings = Settings(
        llm_provider=provider, openai_api_key="openai-test-key", groq_api_key="groq-test-key",
        openai_model="configured-openai-model", groq_model="configured-groq-model",
    )
    draft = OpenAIGenerator(settings).lesson({"concept_slug": "variables"})
    assert draft.concept_slug == "variables"
    module.OpenAI.assert_called_once_with(
        api_key=getattr(settings, key_name).get_secret_value(), base_url=base_url,
        timeout=30.0, max_retries=0,
    )
    request = client.responses.parse.call_args.kwargs
    assert request["model"] == getattr(settings, model_name)
    assert request["text_format"] is LessonDraft
    assert request["store"] is False


def test_groq_missing_configuration_returns_clean_error_without_call(sdk):
    module, _ = sdk
    settings = Settings(llm_provider="groq", groq_api_key=None, groq_model=None)
    with pytest.raises(ApplicationError, match="GROQ_API_KEY and GROQ_MODEL") as error:
        OpenAIGenerator(settings).lesson({})
    assert error.value.status_code == 503
    module.OpenAI.assert_not_called()


def test_provider_failure_does_not_expose_sdk_error(sdk, caplog):
    module, client = sdk
    client.responses.parse.side_effect = module.OpenAIError("private provider error")
    settings = Settings(llm_provider="groq", groq_api_key="test-key", groq_model="configured-model")
    with pytest.raises(ApplicationError) as error:
        OpenAIGenerator(settings).lesson({})
    assert error.value.status_code == 502
    assert "private" not in error.value.detail
    assert "private" not in caplog.text
    assert "provider=Groq status=None error=OpenAIError" in caplog.text


@pytest.mark.parametrize("status,hint", [
    (401, "rejected the API key"),
    (403, "model permissions"),
    (404, "configured model or endpoint"),
    (400, "strict Structured Outputs"),
    (422, "strict Structured Outputs"),
    (429, "rate limit or quota"),
    (500, "unavailable"),
])
def test_provider_http_failure_explains_category_without_leaking_content(sdk, caplog, status, hint):
    module, client = sdk
    sdk_error = module.OpenAIError("secret-key and generated answer key")
    sdk_error.status_code = status
    sdk_error.body = {"error": {"message": "secret-key", "failed_generation": "answer key"}}
    client.responses.parse.side_effect = sdk_error
    settings = Settings(llm_provider="groq", groq_api_key="secret-key", groq_model="configured-model")
    with pytest.raises(ApplicationError, match=hint) as error:
        OpenAIGenerator(settings).lesson({})
    assert error.value.status_code == 502
    assert "Groq" in error.value.detail
    assert "secret-key" not in error.value.detail + caplog.text
    assert "answer key" not in error.value.detail + caplog.text
    assert f"provider=Groq status={status}" in caplog.text
    client.responses.parse.assert_called_once()


@pytest.mark.parametrize("error_type,hint", [
    ("APIConnectionError", "internet connection"),
    ("APITimeoutError", "too long"),
])
def test_provider_network_failure_distinguishes_timeout(sdk, error_type, hint):
    module, client = sdk
    client.responses.parse.side_effect = getattr(module, error_type)("private network details")
    settings = Settings(llm_provider="groq", groq_api_key="test-key", groq_model="configured-model")
    with pytest.raises(ApplicationError, match=hint) as error:
        OpenAIGenerator(settings).lesson({})
    assert "private" not in error.value.detail


def test_openai_key_error_names_openai_setting(sdk):
    module, client = sdk
    sdk_error = module.OpenAIError("private authentication error")
    sdk_error.status_code = 401
    client.responses.parse.side_effect = sdk_error
    settings = Settings(llm_provider="openai", openai_api_key="test-key", openai_model="configured-model")
    with pytest.raises(ApplicationError, match="OPENAI_API_KEY") as error:
        OpenAIGenerator(settings).lesson({})
    assert "GROQ_API_KEY" not in error.value.detail


def test_empty_structured_output_fails_validation(sdk):
    _, client = sdk
    client.responses.parse.return_value.output_parsed = None
    settings = Settings(llm_provider="groq", groq_api_key="test-key", groq_model="configured-model")
    with pytest.raises(ValueError, match="no structured content"):
        OpenAIGenerator(settings).lesson({})
