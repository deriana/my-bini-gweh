# Personal AI VTuber

Asisten AI pribadi interaktif dengan avatar **Live2D**, suara **Dynamic Multi-Provider TTS** (Edge-TTS, Kokoro-82M, VOICEVOX, Custom HTTP), **Persona & Real-Time Mood Engine**, memori percakapan SQLite, integrasi alat **MCP (Model Context Protocol)**, serta dukungan **Voice & Camera Vision**.

Didesain secara modular, minimalis, bersih, cepat, dan tanpa *bloat/gimmick*.

---

## ✨ Fitur Utama

- **Live2D Multi-Model Switcher & Interactive Canvas:**
  - Dilengkapi model siap pakai: **Mao Pro**, **Shiroko**, dan **Shizuku**.
  - Bebas **Zoom In / Zoom Out** (mouse wheel atau tombol kontrol) dan **Drag & Drop Panning** model avatar.
  - Transparent canvas (Pixi v7 `backgroundAlpha: 0`) dengan wallpaper anime ruangan nyata (`/backgrounds`), custom image upload, atau mode OBS transparan.
  - Reaksi emosi otomatis (`[joy]`, `[sadness]`, `[anger]`, `[blush]`, `[surprise]`) sesuai respons AI.

- **Dynamic Multi-Provider TTS Architecture:**
  - **Microsoft Edge-TTS:** Cloud gratis, ringan, kualitas jernih Indonesia & Multilingual.
  - **Kokoro-82M Neural:** Model neural lokal 82M open-weight dengan suara anime Jepang & Inggris yang sangat natural dan ekspresif.
  - **VOICEVOX Engine:** Integrasi REST API (port 50021) untuk karakter anime ikonik (Zundamon, Shikoku Metan, Kasukabe Tsumugi, dll).
  - **Custom HTTP / OpenAI API:** Kompatibel dengan endpoint `/v1/audio/speech`, ElevenLabs, atau microservice TTS sendiri.
  - Lip-syncing seragam berbasis RMS volume chunks (20ms) untuk semua provider.

- **Manajemen Persona & Real-Time Mood Engine:**
  - **Konsep A (Template Archetype):** Tsundere, Deredere, Kuudere, Onee-san, Yandere, Sahabat, atau buat template kustom baru.
  - **Konsep B (Fine-Tuning Sliders):** Kasih Sayang (Affection), Gengsi (Tsundere), dan Energi/Kehebohan (0-100%).
  - **Konsep C (Real-Time Mood Engine):** Status perasaan dinamis yang dapat bereaksi saat diajak ngobrol (`[mood:ceria]`, `[mood:tersipu]`, `[mood:ngambek]`, dll).

- **Dedicated `/settings` Page:**
  - Halaman konfigurasi sentral lengkap: Model AI & API, Dynamic TTS, Avatar Live2D, Background & Tampilan, Manajemen Memori SQLite, serta Log Sistem & Model.

- **Memori & History Chat Persisten (SQLite):**
  - Riwayat percakapan tersimpan rapi di `data/memory.db`.
  - Fitur reset memori per sesi atau hapus seluruh riwayat chat langsung dari panel settings.

- **Dukungan MCP (Model Context Protocol):**
  - Terkoneksi ke server MCP lokal via `config/mcp_servers.json` (waktu, pencarian web, pembacaan file, terminal, dsb).
  - AI secara mandiri dapat memanggil *tool* lokal untuk menyelesaikan tugas pribadi Anda.

- **Voice on Camera (Vision AI) & STT Input:**
  - Aktifkan kamera web dengan satu klik untuk input visual ke model multimodal.
  - Tombol mikrofon bawaan (Web Speech API) untuk bicara langsung tanpa mengetik.

---

## 🚀 Cara Menjalankan

### 1. Instalasi Dependensi
Pastikan Python 3.10+ sudah terpasang, lalu jalankan:

```bash
pip install -r requirements.txt
```

*(Opsional)* Pastikan `ffmpeg` terinstal di sistem untuk kalkulasi volume chunk audio:
```bash
sudo apt update && sudo apt install -y ffmpeg
```

### 2. Jalankan Server
```bash
./run.sh
# atau
python3 app.py
```
Buka peramban (browser) di:
- Antarmuka Utama: **[http://localhost:8080](http://localhost:8080)**
- Halaman Pengaturan Sentral: **[http://localhost:8080/settings](http://localhost:8080/settings)**

---

## 📂 Struktur Direktori

```text
personal-ai-vtuber/
├── app.py                      # FastAPI server & WebSocket duplex
├── run.sh                      # Shell runner
├── requirements.txt            # Minimal dependencies
├── config/                     # Central configurations
│   ├── config.json             # LLM, Dynamic TTS, Live2D, Persona config
│   └── mcp_servers.json        # MCP tool servers config
├── data/                       # Local SQLite storage & wallpapers
│   ├── memory.db               # SQLite conversation history
│   └── backgrounds/            # Anime room wallpapers
├── src/                        # Modular backend architecture
│   ├── core/                   # Config, DB, Logging, Persona Engine
│   ├── tts/                    # Multi-provider dynamic TTS architecture
│   │   ├── base.py             # BaseTTSProvider abstract class
│   │   ├── manager.py          # Central TTSManager & lip-sync orchestrator
│   │   └── providers/          # Edge, Kokoro, VOICEVOX, Custom HTTP providers
│   ├── live2d/                 # Emotion parser & RMS volume analyzer
│   ├── mcp/                    # MCP client & tool caller
│   └── llm/                    # Streaming LLM service & conversation coordinator
├── live2d-models/              # Live2D Cubism models (mao_pro, shiroko, shizuku)
└── static/                     # Pure SVG glassmorphic frontend UI
    ├── index.html              # Main interactive stage
    ├── settings.html           # Dedicated settings interface
    ├── app.js                  # Pixi.js controller, zoom/pan, webcam
    ├── settings.js             # Settings management logic
    └── style.css               # Glassmorphic dark styling
```

---

## 📜 Lisensi & Atribusi

- **Konsep Arsitektur:** Terinspirasi dari konsep dasar repositori open-source [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) (berlisensi **MIT License**).
- **Model Live2D:** Model sampel (seperti Mao Pro dan Shizuku) tunduk pada lisensi penggunaan data sampel dari [Live2D Inc.](https://www.live2d.com) untuk penggunaan non-komersial/pribadi.
