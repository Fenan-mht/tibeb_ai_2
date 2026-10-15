"""Fake provider implementations for automated testing (Playbook testing rules).

No automated test ever contacts external APIs, spends money, or exhausts free-tier quota.
All fakes record inputs and return deterministic, repeatable outputs with usage units.
"""

import hashlib
import math
from collections.abc import AsyncIterator
from typing import Any

from app.providers.base import (
    ChatModel,
    Embedder,
    FileStore,
    PaymentGateway,
    SpeechToText,
    TextToSpeech,
    UsageRecord,
)


class FakeChatModel(ChatModel):
    """Fake chat model streaming fixed answers with citations and recording prompts."""

    def __init__(
        self,
        fixed_answer: str = "የተሰጠው ምላሽ በገጽ 45 ላይ ይገኛል። [Grade 12 Biology, p. 45]",
        chunk_size: int = 15,
    ):
        self.fixed_answer = fixed_answer
        self.chunk_size = chunk_size
        self.recorded_messages: list[list[dict[str, str]]] = []
        self._last_usage = UsageRecord(
            kind="chat", units_in=0, units_out=0, model="fake-chat", provider="fake"
        )

    async def stream(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 800,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        self.recorded_messages.append(messages)
        # Approximate input tokens by character count / 4
        total_in = sum(len(m.get("content", "")) for m in messages) // 4
        total_out = len(self.fixed_answer) // 4
        self._last_usage = UsageRecord(
            kind="chat",
            units_in=total_in,
            units_out=total_out,
            cost_usd=0.0,
            model="fake-chat",
            provider="fake",
        )

        for i in range(0, len(self.fixed_answer), self.chunk_size):
            yield self.fixed_answer[i : i + self.chunk_size]

    def last_usage(self) -> UsageRecord:
        return self._last_usage


class FakeEmbedder(Embedder):
    """Deterministic vector embeddings (1024 numbers) generated from text MD5 hashes."""

    def __init__(self, dimensions: int = 1024):
        self.dimensions = dimensions
        self.recorded_texts: list[str] = []

    def embed(self, texts: list[str]) -> tuple[list[list[float]], UsageRecord]:
        self.recorded_texts.extend(texts)
        vectors = []
        for text in texts:
            # Deterministic pseudo-random vector from MD5 digest
            h = hashlib.md5(text.encode("utf-8")).digest()
            vec = []
            for i in range(self.dimensions):
                byte_val = h[i % len(h)]
                # Map to range [-1.0, 1.0] with sin modulation for spread
                val = math.sin((byte_val + i) * 0.1)
                vec.append(val)
            # Normalize vector to unit length (L2 norm)
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            vectors.append([x / norm for x in vec])

        usage = UsageRecord(
            kind="embed",
            units_in=sum(len(t.split()) for t in texts),
            units_out=0,
            cost_usd=0.0,
            model="fake-bge-m3",
            provider="fake",
        )
        return vectors, usage


class FakeTTS(TextToSpeech):
    """Fake TTS returning minimal valid MP3 header bytes and counting characters."""

    def __init__(self):
        self.synthesized_calls: list[tuple[str, str]] = []

    def synthesize(self, text: str, voice: str = "am-ET-Wavenet-B") -> tuple[bytes, UsageRecord]:
        self.synthesized_calls.append((text, voice))
        # 128 bytes dummy audio payload
        dummy_audio = b"\xff\xfb\x90\x64" + (b"\x00" * 124)
        usage = UsageRecord(
            kind="tts",
            units_in=len(text),
            units_out=len(dummy_audio),
            cost_usd=0.0,
            model=voice,
            provider="fake",
        )
        return dummy_audio, usage


class FakeSTT(SpeechToText):
    """Fake STT returning fixed Amharic transcription and audio length."""

    def __init__(self, fixed_transcript: str = "የሴል ክፍሎች ምንድን ናቸው?"):
        self.fixed_transcript = fixed_transcript
        self.transcribed_calls: list[bytes] = []

    def transcribe(self, audio: bytes, lang: str = "am-ET") -> tuple[str, UsageRecord]:
        self.transcribed_calls.append(audio)
        # Approximate 1 sec per 16000 bytes
        audio_seconds = max(1, len(audio) // 16000)
        usage = UsageRecord(
            kind="stt",
            units_in=audio_seconds,
            units_out=len(self.fixed_transcript),
            cost_usd=0.0,
            model="fake-stt",
            provider="fake",
        )
        return self.fixed_transcript, usage


class FakeFileStore(FileStore):
    """In-memory dictionary file store for isolated testing."""

    def __init__(self, base_url: str = "http://localhost:8000/files"):
        self.storage: dict[str, bytes] = {}
        self.base_url = base_url

    def put(self, path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.storage[path] = data
        return path

    def get(self, path: str) -> bytes:
        if path not in self.storage:
            raise FileNotFoundError(f"File not found in fake store: {path}")
        return self.storage[path]

    def url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"


class FakePayments(PaymentGateway):
    """Simulates Chapa payment gateway checkout, webhook triggers, and verify responses."""

    def __init__(self):
        self.transactions: dict[str, dict[str, Any]] = {}
        self.simulate_failure: bool = False
        self.processed_webhooks: set = set()

    def checkout(
        self,
        amount_birr: float,
        email: str,
        phone: str,
        tx_ref: str,
        callback_url: str,
    ) -> dict[str, Any]:
        if self.simulate_failure:
            return {"status": "failed", "message": "Simulated payment initialization failure"}
        checkout_url = f"https://checkout.chapa.co/test-checkout/{tx_ref}"
        self.transactions[tx_ref] = {
            "tx_ref": tx_ref,
            "amount": amount_birr,
            "email": email,
            "phone": phone,
            "status": "pending",
        }
        return {
            "status": "success",
            "message": "Hosted Link",
            "data": {"checkout_url": checkout_url},
        }

    def verify(self, tx_ref: str) -> dict[str, Any]:
        if tx_ref not in self.transactions:
            return {"status": "failed", "message": "Transaction not found"}
        tx = self.transactions[tx_ref]
        return {
            "status": "success",
            "message": "Payment details",
            "data": {
                "tx_ref": tx_ref,
                "amount": tx["amount"],
                "status": "success" if not self.simulate_failure else "failed",
            },
        }

    def process_webhook(self, tx_ref: str) -> dict[str, Any]:
        """Simulate incoming webhook with duplicate detection."""
        if tx_ref in self.processed_webhooks:
            return {"status": "duplicate", "tx_ref": tx_ref}
        self.processed_webhooks.add(tx_ref)
        if tx_ref in self.transactions:
            self.transactions[tx_ref]["status"] = "success"
        return {"status": "processed", "tx_ref": tx_ref}
