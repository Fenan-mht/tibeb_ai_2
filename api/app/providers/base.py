"""Provider interface definitions for external services.

Every outside service (LLM, embeddings, voice, storage, payments) is accessed
exclusively through these abstract interfaces, ensuring clean separation
and zero dependency on third-party SDKs in business logic (Playbook Rule 7).
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass
class UsageRecord:
    kind: str  # chat, embed, practice, speech_script, tts, stt
    units_in: int = 0
    units_out: int = 0
    cost_usd: float = 0.0
    model: str = ""
    provider: str = ""


class ChatModel(ABC):
    """Abstract interface for LLM chat and text completion models."""

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 800,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """Stream response tokens one by one."""

    @abstractmethod
    def last_usage(self) -> UsageRecord:
        """Return the usage record from the most recent stream call."""


class Embedder(ABC):
    """Abstract interface for dense text embedding models (1024 dimensions for BGE-M3)."""

    @abstractmethod
    def embed(self, texts: list[str]) -> tuple[list[list[float]], UsageRecord]:
        """Generate 1024-dimensional normalized vector embeddings for input texts."""


class TextToSpeech(ABC):
    """Abstract interface for speech synthesis."""

    @abstractmethod
    def synthesize(self, text: str, voice: str = "am-ET-Wavenet-B") -> tuple[bytes, UsageRecord]:
        """Convert text into audio bytes (MP3/Opus) and report character usage."""


class SpeechToText(ABC):
    """Abstract interface for speech transcription."""

    @abstractmethod
    def transcribe(self, audio: bytes, lang: str = "am-ET") -> tuple[str, UsageRecord]:
        """Transcribe audio into text and report audio seconds usage."""


class FileStore(ABC):
    """Abstract interface for file and media storage."""

    @abstractmethod
    def put(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Save file bytes and return storage path or identifier."""

    @abstractmethod
    def get(self, path: str) -> bytes:
        """Retrieve file bytes by path."""

    @abstractmethod
    def url(self, path: str) -> str:
        """Return a public or signed URL for playback/download."""


class PaymentGateway(ABC):
    """Abstract interface for payment processing (Chapa)."""

    @abstractmethod
    def checkout(
        self,
        amount_birr: float,
        email: str,
        phone: str,
        tx_ref: str,
        callback_url: str,
    ) -> dict[str, Any]:
        """Initialize payment transaction and return checkout URL."""

    @abstractmethod
    def verify(self, tx_ref: str) -> dict[str, Any]:
        """Verify transaction status with payment gateway."""
