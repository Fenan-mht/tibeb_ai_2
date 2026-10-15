import pytest

from app.config import Settings, get_settings


def test_config_loads_default_values():
    settings = get_settings()
    assert settings.APP_ENV in ("development", "test", "production")
    assert settings.providers is not None
    assert settings.providers.chat.tutor.provider in ("groq", "fake")
    assert settings.providers.embedder.model == "BAAI/bge-m3"


def test_production_refuses_auth_mode_none():
    """Security check: Server MUST refuse to run with AUTH_MODE=none when APP_ENV=production."""
    with pytest.raises(ValueError, match="AUTH_MODE cannot be 'none' when APP_ENV is 'production'"):
        Settings(APP_ENV="production", AUTH_MODE="none")


def test_production_allows_auth_mode_sms():
    settings = Settings(APP_ENV="production", AUTH_MODE="sms")
    assert settings.APP_ENV == "production"
    assert settings.AUTH_MODE == "sms"


def test_custom_config_path_loading(tmp_path):
    custom_yaml = tmp_path / "custom.yaml"
    custom_yaml.write_text(
        """
chat:
  tutor: { provider: fake, model: test-tutor }
  flashcards: { provider: fake, model: test-cards }
embedder: { provider: fake, model: test-bge }
stt: { provider: fake }
tts: { provider: fake, voice: am-ET-Wavenet-B }
storage: { provider: fake, path: ./tmp }
payments: { provider: fake, mode: test }
"""
    )
    settings = Settings(CONFIG_PATH=str(custom_yaml), APP_ENV="test", AUTH_MODE="none")
    assert settings.providers.chat.tutor.provider == "fake"
    assert settings.providers.chat.tutor.model == "test-tutor"
    assert settings.providers.embedder.provider == "fake"
