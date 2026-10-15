"""Providers package exposing interfaces, fakes, and factories."""

from app.providers.base import (
    ChatModel,
    Embedder,
    FileStore,
    PaymentGateway,
    SpeechToText,
    TextToSpeech,
    UsageRecord,
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
from app.providers.registry import (
    get_embedder,
    get_file_store,
    get_flashcards_model,
    get_payment_gateway,
    get_stt,
    get_tts,
    get_tutor_model,
)

__all__ = [
    "ChatModel",
    "Embedder",
    "FakeChatModel",
    "FakeEmbedder",
    "FakeFileStore",
    "FakePayments",
    "FakeSTT",
    "FakeTTS",
    "FileStore",
    "GroqChatModel",
    "LocalFileStore",
    "PaymentGateway",
    "SpeechToText",
    "TextToSpeech",
    "UsageRecord",
    "get_embedder",
    "get_file_store",
    "get_flashcards_model",
    "get_payment_gateway",
    "get_stt",
    "get_tts",
    "get_tutor_model",
]
