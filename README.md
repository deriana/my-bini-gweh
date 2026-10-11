# Personal AI VTuber

Asisten AI pribadi interaktif dengan avatar **Live2D**, suara **Edge-TTS**, integrasi alat **MCP (Model Context Protocol)**, serta dukungan **Voice & Camera Vision**.

Didesain secara minimalis, bersih, cepat, dan tanpa *bloat/gimmick*.

---

## ✨ Fitur Utama

- **Live2D Multi-Model Switcher:**
  - Dilengkapi model siap pakai: **Mao Pro**, **Shiroko**, dan **Shizuku**.
  - Ganti karakter kapan saja langsung dari dropdown menu di antarmuka web.
  - Reaksi emosi otomatis (`[joy]`, `[sadness]`, `[anger]`, `[blush]`, `[surprise]`) sesuai jawaban AI.
- **Lip-Syncing Akurat:**
  - Mulut avatar bergerak secara proporsional mengikuti volume audio suara yang diucapkan.
- **Edge-TTS Suara Fleksibel (Gratis & Natural):**
  - Ganti pilihan suara kapan saja:
    - 🇮🇩 **Bahasa Indonesia:** Gadis (Ceria), Ardi (Tenang)
    - 🇯🇵 **Bahasa Jepang:** Nanami (Anime/Lucu), Keita
    - 🇺🇸 **Bahasa Inggris & Multilingual:** Ava, Jenny
  - Penyesuaian nada (*pitch*) dan kecepatan (*rate*) otomatis berdasarkan emosi kalimat.
- **Dukungan MCP (Model Context Protocol):**
  - Terkoneksi ke server MCP lokal via `mcp_servers.json` (waktu, pencarian web, pembacaan file, terminal, dsb).
  - AI secara mandiri dapat memanggil *tool* lokal untuk menyelesaikan tugas pribadi Anda.
- **Voice on Camera (Vision AI):**
  - Aktifkan kamera web dengan satu klik.
  - Tangkapan frame kamera dikirim langsung ke LLM Vision saat mengobrol.
- **Voice Input (STT):**
  - Tombol mikrofon bawaan untuk langsung mengobrol menggunakan suara tanpa mengetik.
- **Universal LLM Backend:**
  - Berbasis standar OpenAI API: kompatibel langsung dengan **Ollama (Qwen 2.5)**, LM Studio, Groq, DeepSeek, Gemini, atau OpenAI.

---

## 🚀 Cara Menjalankan

### 1. Instalasi Dependensi
Pastikan Python 3.10+ sudah terpasang, lalu jalankan:

```bash
pip install -r requirements.txt
```

*(Opsional)* Pastikan `ffmpeg` terinstal di sistem untuk pemrosesan chunk audio pydub:
```bash
sudo apt update && sudo apt install -y ffmpeg
```

### 2. Konfigurasi LLM (Opsional)
Secara default, aplikasi akan mencoba terhubung ke Ollama lokal di `http://127.0.0.1:11434/v1` dengan model `qwen2.5:3b`.

Untuk menggunakan model/API lain (seperti Groq, OpenAI, atau Gemini):
Ubah `config.json` atau set *environment variables*:
```bash
export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
export OPENAI_API_KEY="gsk_..."
export LLM_MODEL="llama-3.3-70b-versatile"
```

### 3. Jalankan Server
```bash
python app.py
```
Buka peramban (browser) di: **[http://localhost:8000](http://localhost:8000)**

---

## 📂 Struktur Direktori

```text
personal-ai-vtuber/
├── app.py                 # Backend FastAPI (WebSocket, Streaming LLM, MCP, Vision)
├── tts_engine.py          # Edge-TTS engine & base64 volume chunk calculator
├── live2d_helper.py       # Parser tag emosi ([joy], dll) & audio RMS lip-sync
├── mcp_manager.py         # MCP stdio client & OpenAI tool caller
├── mcp_servers.json       # Daftar server tool MCP pribadi
├── config.json            # Konfigurasi model Live2D, TTS, dan LLM
├── requirements.txt       # Dependensi Python minimalis
├── live2d-models/         # Berisi model mao_pro, shiroko, shizuku
└── static/
    ├── index.html         # Antarmuka web modern
    ├── app.js             # Controller Pixi.js, Audio Lip-sync, Mic, Kamera
    ├── style.css          # Desain UI glassmorphism dark-mode
    └── libs/              # Library Cubism SDK & PixiJS
```

---

## 📜 Lisensi & Atribusi

- **Konsep Arsitektur:** Terinspirasi dari konsep dasar repositori open-source [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) (berlisensi **MIT License**).
- **Model Live2D:** Model sampel (seperti Mao Pro dan Shizuku) tunduk pada lisensi penggunaan data sampel dari [Live2D Inc.](https://www.live2d.com) untuk penggunaan non-komersial/pribadi.
