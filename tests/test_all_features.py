import os
import sys
import asyncio
from fastapi.testclient import TestClient

# Ensure root directory in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from src.core import tts_engine, llm_service, persona_engine, db

client = TestClient(app)


def test_routes():
    print("\n--- 1. Testing HTTP Pages & Endpoints ---")
    
    # 1. Page routes
    r = client.get("/")
    assert r.status_code == 200, f"GET / failed with {r.status_code}"
    print("  [PASS] GET / (Main Stage Page)")

    r = client.get("/settings")
    assert r.status_code == 200, f"GET /settings failed with {r.status_code}"
    print("  [PASS] GET /settings (Dedicated Settings Page)")

    r = client.get("/overlay")
    assert r.status_code == 200, f"GET /overlay failed with {r.status_code}"
    assert "live2d-canvas" in r.text
    print("  [PASS] GET /overlay (OBS Transparent Stream Overlay)")

    # 2. Config & Settings
    r = client.get("/api/config")
    assert r.status_code == 200 and "models" in r.json(), "GET /api/config failed"
    data = r.json()
    print(f"  [PASS] GET /api/config (Active TTS: {data.get('active_tts_provider')}, Live2D Models: {list(data.get('models', {}).keys())})")

    r = client.get("/api/settings")
    assert r.status_code == 200 and "tts_providers" in r.json(), "GET /api/settings failed"
    print(f"  [PASS] GET /api/settings (Registered TTS Engines: {len(r.json()['tts_providers'])})")

    # 3. Persona & Mood
    r = client.get("/api/persona")
    assert r.status_code == 200 and "archetypes" in r.json(), "GET /api/persona failed"
    print(f"  [PASS] GET /api/persona (Archetypes: {list(r.json()['archetypes'].keys())})")

    r = client.get("/api/mood")
    assert r.status_code == 200 and "mood" in r.json(), "GET /api/mood failed"
    print(f"  [PASS] GET /api/mood (Current: {r.json()['mood']})")

    # 4. History & Memory
    r = client.get("/api/history?session_id=test")
    assert r.status_code == 200, "GET /api/history failed"
    print("  [PASS] GET /api/history (SQLite Connection)")

    # 5. Logs
    r = client.get("/api/logs")
    assert r.status_code == 200 and "logs" in r.json(), "GET /api/logs failed"
    print(f"  [PASS] GET /api/logs (Total Logs: {len(r.json()['logs'])})")

    # 6. Interactive Touch Reactions
    for touch in ["headpat", "poke", "body"]:
        r = client.post("/api/interact/touch", json={"touch_type": touch, "model": "mao_pro"})
        assert r.status_code == 200, f"POST /api/interact/touch failed for {touch}"
        t_data = r.json()
        assert "text" in t_data and "emotion" in t_data
        print(f"  [PASS] POST /api/interact/touch ({touch}) -> \"{t_data['text']}\" [{t_data['emotion']}]")

    # 7. Autonomous Proactive Greetings & Reminders
    r = client.get("/api/proactive/greeting?model=mao_pro")
    assert r.status_code == 200, "GET /api/proactive/greeting failed"
    g_data = r.json()
    assert "text" in g_data and "period" in g_data
    print(f"  [PASS] GET /api/proactive/greeting ({g_data['period']}) -> \"{g_data['text']}\" [{g_data['emotion']}]")

    r = client.get("/api/proactive/reminder?model=mao_pro")
    assert r.status_code == 200, "GET /api/proactive/reminder failed"
    rem_data = r.json()
    assert "text" in rem_data and "emotion" in rem_data
    print(f"  [PASS] GET /api/proactive/reminder -> \"{rem_data['text']}\" [{rem_data['emotion']}]")


async def test_ollama_llm():
    print("\n--- 2. Testing Ollama (Windows Host / Qwen 2.5) ---")
    try:
        messages = [
            {"role": "system", "content": persona_engine.build_system_prompt()},
            {"role": "user", "content": "Halo Ryza! Sebutkan namamu secara singkat dengan tag emosi."}
        ]
        response = await llm_service.client.chat.completions.create(
            model=llm_service.model,
            messages=messages,
            max_tokens=60,
            temperature=0.7
        )
        content = response.choices[0].message.content
        print(f"  [PASS] Ollama response: {content}")
        assert content and len(content) > 0
    except Exception as e:
        print(f"  [FAIL] Ollama connection error: {e}")
        raise e


async def test_tts_engines():
    print("\n--- 3. Testing All TTS Engines ---")

    # A. Edge-TTS (Cloud)
    print("  -> Testing Microsoft Edge-TTS...")
    res_edge = await tts_engine.generate_audio("Halo! Ini tes suara Edge TTS bahasa Indonesia.", provider_id="edge", voice="id-ID-GadisNeural")
    assert res_edge is not None, "Edge-TTS synthesis failed"
    path, b64, vols = res_edge
    print(f"     [PASS] Edge-TTS: {path} | Volume Chunks: {len(vols)} | Base64 Length: {len(b64)}")

    # B. Kokoro-82M (WSL Local Neural)
    print("  -> Testing Kokoro-82M Neural TTS (WSL Local)...")
    res_kokoro = await tts_engine.generate_audio("こんにちは！Kokoroの音声テストです。", provider_id="kokoro", voice="jf_alpha")
    assert res_kokoro is not None, "Kokoro synthesis failed"
    path, b64, vols = res_kokoro
    print(f"     [PASS] Kokoro (jf_alpha): {path} | Volume Chunks: {len(vols)} | Base64 Length: {len(b64)}")

    # C. VOICEVOX (Windows Host Port 50021)
    print("  -> Testing VOICEVOX Engine (Windows Port 50021)...")
    res_vv = await tts_engine.generate_audio("ずんだもんなのだ！テストなのだ！", provider_id="voicevox", voice="3")
    if res_vv is not None:
        path, b64, vols = res_vv
        print(f"     [PASS] VOICEVOX (Zundamon 3): {path} | Volume Chunks: {len(vols)} | Base64 Length: {len(b64)}")
    else:
        print("     [WARN] VOICEVOX endpoint not responsive, check engine port 50021.")


def test_websocket_duplex():
    print("\n--- 4. Testing Interactive WebSocket Duplex Connection ---")
    with client.websocket_connect("/ws") as ws:
        # Ping test
        ws.send_json({"type": "ping"})
        data = ws.receive_json()
        assert data.get("type") == "pong", "WebSocket ping failed"
        print("  [PASS] WebSocket /ws Ping-Pong Response")

        # Chat test
        ws.send_json({
            "type": "chat",
            "text": "Hai cantik!",
            "model": "mao_pro",
            "voice": "id-ID-GadisNeural",
            "session_id": "test_session"
        })

        received_types = []
        full_text = ""
        while True:
            msg = ws.receive_json()
            t = msg.get("type")
            received_types.append(t)
            if t == "audio":
                full_text += msg.get("text", "")
            elif t == "done":
                break

        print(f"  [PASS] WebSocket Flow Completed! Events Received: {set(received_types)}")
        print(f"         AI Streamed Reply: {msg.get('full_text')}")


def main():
    print("==================================================")
    print(" STARTING COMPREHENSIVE VTUBER TEST SUITE ")
    print("==================================================")

    test_routes()
    asyncio.run(test_ollama_llm())
    asyncio.run(test_tts_engines())
    test_websocket_duplex()

    print("\n==================================================")
    print(" ALL TESTS PASSED SUCCESSFULLY! ")
    print("==================================================")


if __name__ == "__main__":
    main()
