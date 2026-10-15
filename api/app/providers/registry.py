"""Provider registry and factory resolving active implementations from config."""

from app.config import Settings, get_settings
from app.providers.base import (
    ChatModel,
    Embedder,
    FileStore,
    PaymentGateway,
    SpeechToText,
    TextToSpeech,
)
from app.providers.fakes import (
    FakeChatModel,
    FakeEmbedder,
    FakeFileStore,
    FakePayments,
    FakeSTT,
    FakeTTS,
)
from app.providers.groq import GroqChatModel
from app.providers.local_store import LocalFileStore


def get_tutor_model(settings: Settings | None = None) -> ChatModel:
    s = settings or get_settings()
    spec = s.providers.chat.tutor  # type: ignore
    if spec.provider == "fake" or s.APP_ENV == "test" and not s.GROQ_API_KEY:
        return FakeChatModel()
    if spec.provider == "groq":
        return GroqChatModel(model=spec.model or "openai/gpt-oss-120b", api_key=s.GROQ_API_KEY)
    raise ValueError(f"Unsupported chat tutor provider: {spec.provider}")


def get_flashcards_model(settings: Settings | None = None) -> ChatModel:
    s = settings or get_settings()
    spec = s.providers.chat.flashcards  # type: ignore
    if spec.provider == "fake" or s.APP_ENV == "test" and not s.GROQ_API_KEY:
        return FakeChatModel()
    if spec.provider == "groq":
        return GroqChatModel(model=spec.model or "openai/gpt-oss-20b", api_key=s.GROQ_API_KEY)
    raise ValueError(f"Unsupported flashcard model provider: {spec.provider}")


def get_embedder(settings: Settings | None = None) -> Embedder:
    s = settings or get_settings()
    spec = s.providers.embedder  # type: ignore
    if spec.provider == "fake" or s.APP_ENV == "test":
        # Tests always use FakeEmbedder to ensure fast, deterministic vectors without 2GB download
        return FakeEmbedder()
    raise ValueError(f"Unsupported embedder provider: {spec.provider}")


def get_tts(settings: Settings | None = None) -> TextToSpeech:
    s = settings or get_settings()
    spec = s.providers.tts  # type: ignore
    if spec.provider == "fake" or s.APP_ENV == "test" or not s.GOOGLE_APPLICATION_CREDENTIALS:
        return FakeTTS()
    raise ValueError(f"Unsupported TTS provider: {spec.provider}")


def get_stt(settings: Settings | None = None) -> SpeechToText:
    s = settings or get_settings()
    spec = s.providers.stt  # type: ignore
    if spec.provider in ("fake", "none") or s.APP_ENV == "test":
        return FakeSTT()
    raise ValueError(f"Unsupported STT provider: {spec.provider}")


def get_file_store(settings: Settings | None = None) -> FileStore:
    s = settings or get_settings()
    spec = s.providers.storage  # type: ignore
    if spec.provider == "fake":
        return FakeFileStore()
    if spec.provider == "local":
        return LocalFileStore(base_path=spec.path or "./data/files")
    raise ValueError(f"Unsupported storage provider: {spec.provider}")


def get_payment_gateway(settings: Settings | None = None) -> PaymentGateway:
    s = settings or get_settings()
    spec = s.providers.payments  # type: ignore
    # Under Phase 1-4, automated tests and test mode use FakePayments
    if spec.provider in ("fake", "chapa"):
        return FakePayments()
    raise ValueError(f"Unsupported payments provider: {spec.provider}")
