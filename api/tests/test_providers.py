import pytest

from app.config import Settings
from app.providers.fakes import (
    FakeChatModel,
    FakeEmbedder,
    FakeFileStore,
    FakePayments,
    FakeSTT,
    FakeTTS,
)
from app.providers.registry import (
    get_embedder,
    get_file_store,
    get_payment_gateway,
    get_stt,
    get_tts,
)


@pytest.mark.asyncio
async def test_fake_chat_model_streaming_and_usage():
    model = FakeChatModel(fixed_answer="ይህ የሙከራ መልስ ነው። [Biology, p. 10]")
    messages = [{"role": "user", "content": "ጥያቄ"}]

    chunks = []
    async for chunk in model.stream(messages):
        chunks.append(chunk)

    full_answer = "".join(chunks)
    assert full_answer == "ይህ የሙከራ መልስ ነው። [Biology, p. 10]"
    assert "[Biology, p. 10]" in full_answer
    assert len(model.recorded_messages) == 1
    assert model.recorded_messages[0] == messages

    usage = model.last_usage()
    assert usage.kind == "chat"
    assert usage.units_out > 0


def test_fake_embedder_deterministic_and_dimensions():
    embedder = FakeEmbedder(dimensions=1024)
    texts = ["ኦክሲጅን", "ሳይንስ"]

    vectors, usage = embedder.embed(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 1024
    assert len(vectors[1]) == 1024
    assert usage.kind == "embed"
    assert usage.units_in == 2

    # Determinism: same input yields exact same vector
    vectors2, _ = embedder.embed(["ኦክሲጅን"])
    assert vectors[0] == vectors2[0]


def test_fake_tts_synthesize():
    tts = FakeTTS()
    audio, usage = tts.synthesize("ሰላም", voice="am-ET-Wavenet-B")
    assert len(audio) > 0
    assert usage.kind == "tts"
    assert usage.units_in == 3  # 3 Amharic characters: ሰ-ላ-ም
    assert len(tts.synthesized_calls) == 1


def test_fake_stt_transcribe():
    stt = FakeSTT(fixed_transcript="የታሪክ ጥያቄ")
    text, usage = stt.transcribe(b"dummy_audio_bytes" * 1000)
    assert text == "የታሪክ ጥያቄ"
    assert usage.kind == "stt"
    assert usage.units_in > 0


def test_fake_file_store():
    store = FakeFileStore()
    stored_path = store.put("audio/test.mp3", b"audio-data")
    assert stored_path == "audio/test.mp3"
    assert store.get("audio/test.mp3") == b"audio-data"
    assert "audio/test.mp3" in store.url("audio/test.mp3")

    with pytest.raises(FileNotFoundError):
        store.get("non-existent.txt")


def test_fake_payments_flow():
    gateway = FakePayments()
    # Checkout
    res = gateway.checkout(
        amount_birr=250.0,
        email="student@example.com",
        phone="0911223344",
        tx_ref="tx_123",
        callback_url="http://localhost:8000/callback",
    )
    assert res["status"] == "success"
    assert "checkout_url" in res["data"]

    # Verify
    verify_res = gateway.verify("tx_123")
    assert verify_res["status"] == "success"
    assert verify_res["data"]["amount"] == 250.0

    # Webhook & duplicate safety
    webhook_1 = gateway.process_webhook("tx_123")
    assert webhook_1["status"] == "processed"

    webhook_duplicate = gateway.process_webhook("tx_123")
    assert webhook_duplicate["status"] == "duplicate"


def test_provider_registry_factory():
    settings = Settings(APP_ENV="test", AUTH_MODE="none")
    # In test mode without external calls, fake providers are chosen
    embedder = get_embedder(settings)
    assert isinstance(embedder, FakeEmbedder)

    tts = get_tts(settings)
    assert isinstance(tts, FakeTTS)

    stt = get_stt(settings)
    assert isinstance(stt, FakeSTT)

    file_store = get_file_store(settings)
    assert file_store is not None

    payments = get_payment_gateway(settings)
    assert isinstance(payments, FakePayments)
