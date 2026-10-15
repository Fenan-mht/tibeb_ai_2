"""Smoke check script for external provider credentials.

Performs one tiny call per configured service to verify API keys and connectivity.
Prints usage estimates before execution (Playbook Rule 17).
Gracefully skips deferred services (Google TTS and Chapa) with clear messages.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load api/.env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def main():
    print("========================================")
    print("   Tibeb AI — Provider Smoke Check     ")
    print("========================================")

    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    database_url = os.getenv("DATABASE_URL", "").strip()
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    chapa_key = os.getenv("CHAPA_SECRET_KEY", "").strip()

    # Playbook Rule 17: print characters and tokens before calling real services
    estimated_groq_tokens = 30
    estimated_tts_chars = 10 if google_creds else 0

    print("\nPlanned provider usage:")
    print(f" - Groq LLM: ~{estimated_groq_tokens} tokens (free tier)")
    print(" - Supabase: 2 lightweight SQL queries (SELECT 1, extension check)")
    if google_creds:
        print(f" - Google TTS: ~{estimated_tts_chars} Amharic characters")
    else:
        print(" - Google TTS: SKIPPED (no credentials configured)")
    if chapa_key:
        print(" - Chapa: 1 test transaction initialization")
    else:
        print(" - Chapa: SKIPPED (no secret key configured)")
    print("----------------------------------------\n")

    passed = []
    failed = []

    # 1. Groq Check
    print("[1/4] Checking Groq LLM API...")
    if not groq_api_key or groq_api_key.startswith("gsk_your_"):
        print("  FAILED: GROQ_API_KEY is not set in api/.env")
        failed.append("Groq")
    else:
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_api_key,
            )
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a helpful tutor."},
                    {"role": "user", "content": "Say 'ጤና ይስጥልኝ' and nothing else."},
                ],
                model="openai/gpt-oss-20b",
                max_tokens=20,
            )
            raw_content = chat_completion.choices[0].message.content
            response_text = raw_content.strip() if raw_content else ""
            tokens_used = chat_completion.usage.total_tokens if chat_completion.usage else "?"
            print(f'  OK: Groq response: "{response_text}" (tokens used: {tokens_used})')
            passed.append("Groq")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED: Groq error: {e}")
            failed.append("Groq")

    # 2. Supabase Check
    print("\n[2/4] Checking Supabase Database & pgvector...")
    if not database_url or "[PASSWORD]" in database_url:
        print("  FAILED: DATABASE_URL is not set or has placeholder in api/.env")
        failed.append("Supabase")
    else:
        try:
            import psycopg

            with psycopg.connect(database_url) as conn, conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
                cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
                row = cur.fetchone()
                if row and row[0] == "vector":
                    print("  OK: Supabase connected (SELECT 1 = 1, pgvector extension active)")
                    passed.append("Supabase")
                else:
                    print("  FAILED: Connected to Supabase, but 'vector' extension was not found.")
                    failed.append("Supabase")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED: Supabase connection error: {e}")
            failed.append("Supabase")

    # 3. Google TTS Check
    print("\n[3/4] Checking Google Cloud Text-to-Speech...")
    if not google_creds:
        print("  SKIPPED: no Google credentials (deferred to Phase 4)")
    else:
        creds_path = Path(google_creds)
        if not creds_path.is_absolute():
            creds_path = Path(__file__).parent.parent / creds_path
        if not creds_path.exists():
            print(f"  FAILED: Credentials file not found at {creds_path}")
            failed.append("Google TTS")
        else:
            try:
                from google.cloud import texttospeech

                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)
                tts_client = texttospeech.TextToSpeechClient()
                s_input = texttospeech.SynthesisInput(text="ሰላም ተማሪ")
                voice = texttospeech.VoiceSelectionParams(
                    language_code="am-ET",
                    name="am-ET-Wavenet-B",
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3
                )
                response = tts_client.synthesize_speech(
                    input=s_input, voice=voice, audio_config=audio_config
                )
                out_path = Path(__file__).parent.parent / "data" / "smoke.mp3"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(response.audio_content)
                print(
                    f"  OK: Google TTS generated audio saved to {out_path} ({len(response.audio_content)} bytes)"
                )
                passed.append("Google TTS")
            except Exception as e:  # noqa: BLE001
                print(f"  FAILED: Google TTS error: {e}")
                failed.append("Google TTS")

    # 4. Chapa Check
    print("\n[4/4] Checking Chapa Payment Gateway...")
    if not chapa_key:
        print("  SKIPPED: no Chapa key (deferred to Phase 5)")
    else:
        try:
            import httpx

            headers = {"Authorization": f"Bearer {chapa_key}"}
            resp = httpx.get("https://api.chapa.co/v1/banks", headers=headers, timeout=10)
            if resp.status_code == 200:
                print("  OK: Chapa API reachable and authenticated")
                passed.append("Chapa")
            else:
                print(f"  FAILED: Chapa returned status {resp.status_code}: {resp.text}")
                failed.append("Chapa")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED: Chapa error: {e}")
            failed.append("Chapa")

    print("\n========================================")
    print("            Smoke Check Summary         ")
    print("========================================")
    print(f"Passed: {', '.join(passed) if passed else 'None'}")
    if failed:
        print(f"Failed: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("Status: ALL ACTIVE CHECKS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
