/**
 * Settings Page Logic
 * Manages comprehensive configuration for Persona Archetypes, Sliders Tuning,
 * Real-Time Mood, LLM, TTS, Live2D, Anime Wallpapers, SQLite Memory, and System Logs.
 */

let currentConfig = null;
let personaData = null;

document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initProviderPresets();
  initTTSProviders();
  await loadSettings();
  await loadPersonaSettings();
  await loadHistory();
  initLogPolling();
  initAppearanceSettings();
  initActionButtons();
});

// ==========================================
// 1. Tab Navigation
// ==========================================
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));

      tab.classList.add("active");
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add("active");

      if (tab.dataset.tab === "tab-logs") {
        fetchLogs();
      }
    });
  });
}

// ==========================================
// 2. Persona, Archetypes & Mood (Konsep A, B, C)
// ==========================================
async function loadPersonaSettings() {
  try {
    const res = await fetch("/api/persona");
    personaData = await res.json();

    document.getElementById("persona-char-name").value = personaData.character_name || "Ryza";
    document.getElementById("persona-user-call").value = personaData.user_call_name || "Sayang";

    // Sliders
    const aff = personaData.affection_level !== undefined ? personaData.affection_level : 75;
    const tsun = personaData.tsundere_level !== undefined ? personaData.tsundere_level : 60;
    const nrg = personaData.energy_level !== undefined ? personaData.energy_level : 70;

    document.getElementById("slider-affection").value = aff;
    document.getElementById("aff-val").textContent = `${aff}%`;

    document.getElementById("slider-tsundere").value = tsun;
    document.getElementById("tsun-val").textContent = `${tsun}%`;

    document.getElementById("slider-energy").value = nrg;
    document.getElementById("energy-val").textContent = `${nrg}%`;

    // Sliders listeners
    document.getElementById("slider-affection").addEventListener("input", (e) => {
      document.getElementById("aff-val").textContent = `${e.target.value}%`;
    });
    document.getElementById("slider-tsundere").addEventListener("input", (e) => {
      document.getElementById("tsun-val").textContent = `${e.target.value}%`;
    });
    document.getElementById("slider-energy").addEventListener("input", (e) => {
      document.getElementById("energy-val").textContent = `${e.target.value}%`;
    });

    // Mood
    const moodSelect = document.getElementById("persona-mood-select");
    moodSelect.value = personaData.current_mood || "Ceria";

    // Reset mood
    document.getElementById("reset-mood-btn").addEventListener("click", async () => {
      const resetRes = await fetch("/api/mood/reset", { method: "POST" });
      if (resetRes.ok) {
        moodSelect.value = "Ceria";
        showToast("Mood direset ke: Ceria 💖");
      }
    });

    renderArchetypeCards();
  } catch (err) {
    console.error("Failed to load persona data:", err);
  }
}

function renderArchetypeCards() {
  const container = document.getElementById("archetype-list");
  const promptInput = document.getElementById("archetype-prompt-input");
  container.innerHTML = "";

  const archetypes = personaData.archetypes || {};
  const activeKey = personaData.active_archetype || "tsundere";

  for (const [key, item] of Object.entries(archetypes)) {
    const card = document.createElement("div");
    card.className = `archetype-card ${key === activeKey ? "selected" : ""}`;
    card.dataset.key = key;

    card.innerHTML = `
      <div class="archetype-card-title">${item.name || key}</div>
      <div class="archetype-card-desc">${item.description || ""}</div>
    `;

    card.addEventListener("click", () => {
      document.querySelectorAll(".archetype-card").forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      personaData.active_archetype = key;
      promptInput.value = item.prompt || "";
    });

    container.appendChild(card);
  }

  // Set active prompt textarea
  if (archetypes[activeKey]) {
    promptInput.value = archetypes[activeKey].prompt || "";
  }

  // Update prompt on edit
  promptInput.addEventListener("input", (e) => {
    const active = personaData.active_archetype;
    if (active && personaData.archetypes[active]) {
      personaData.archetypes[active].prompt = e.target.value;
    }
  });

  // Add custom archetype button
  document.getElementById("add-archetype-btn").onclick = () => {
    const name = prompt("Masukkan nama archetype baru (misal: Maid, Tomboy, Ratu):");
    if (!name) return;
    const key = name.toLowerCase().replace(/[^a-z0-9]/g, "_");
    const desc = prompt("Masukkan deskripsi singkat archetype ini:") || "";
    const promptText = prompt("Masukkan instruksi prompt persona:", `Kamu memiliki sifat ${name}: ...`) || "";

    if (!personaData.archetypes) personaData.archetypes = {};
    personaData.archetypes[key] = {
      name: name,
      description: desc,
      prompt: promptText,
    };
    personaData.active_archetype = key;
    renderArchetypeCards();
    showToast(`Template '${name}' berhasil ditambahkan!`);
  };
}

// ==========================================
// 3. Dynamic TTS Providers Setup
// ==========================================
function initTTSProviders() {
  const cards = document.querySelectorAll("#tts-provider-grid .provider-card");
  const panels = {
    edge: document.getElementById("panel-edge"),
    kokoro: document.getElementById("panel-kokoro"),
    voicevox: document.getElementById("panel-voicevox"),
    custom_http: document.getElementById("panel-custom_http")
  };
  const titleMap = {
    edge: "Microsoft Edge-TTS (Cloud / Ringan)",
    kokoro: "Kokoro-82M Neural TTS (Lokal Neural)",
    voicevox: "VOICEVOX Engine (Karakter Anime)",
    custom_http: "Custom HTTP / OpenAI API Endpoint"
  };

  cards.forEach((card) => {
    card.addEventListener("click", () => {
      cards.forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      const provider = card.dataset.provider;

      const titleEl = document.getElementById("provider-config-title");
      if (titleEl) titleEl.textContent = `Pengaturan Engine: ${titleMap[provider] || provider}`;

      // Switch panels
      Object.keys(panels).forEach((k) => {
        if (panels[k]) panels[k].style.display = k === provider ? "block" : "none";
      });
    });
  });

  // Slider listeners
  const kokoroSlider = document.getElementById("kokoro-speed-slider");
  if (kokoroSlider) {
    kokoroSlider.addEventListener("input", (e) => {
      const valEl = document.getElementById("kokoro-speed-val");
      if (valEl) valEl.textContent = `${e.target.value}x`;
    });
  }

  const voicevoxSlider = document.getElementById("voicevox-speed-slider");
  if (voicevoxSlider) {
    voicevoxSlider.addEventListener("input", (e) => {
      const valEl = document.getElementById("voicevox-speed-val");
      if (valEl) valEl.textContent = `${e.target.value}x`;
    });
  }

  // VOICEVOX Live Connection Check
  const vvRefreshBtn = document.getElementById("voicevox-refresh-btn");
  if (vvRefreshBtn) {
    vvRefreshBtn.addEventListener("click", async () => {
      vvRefreshBtn.textContent = "Mengecek...";
      vvRefreshBtn.disabled = true;
      try {
        const res = await fetch("/api/tts/voicevox/speakers");
        const data = await res.json();
        const badge = document.getElementById("badge-voicevox");
        if (data.speakers && data.speakers.length > 0) {
          if (badge) {
            badge.className = "status-badge available";
            badge.textContent = `Online (${data.speakers.length} style)`;
          }

          const select = document.getElementById("voicevox-speaker-select");
          if (select) {
            select.innerHTML = "";
            data.speakers.forEach((s) => {
              const opt = document.createElement("option");
              opt.value = s.id;
              opt.textContent = `${s.name} [ID: ${s.id}]`;
              select.appendChild(opt);
            });
          }
          showToast(`Berhasil terhubung ke VOICEVOX (${data.speakers.length} karakter ditemukan)!`);
        } else {
          if (badge) {
            badge.className = "status-badge offline";
            badge.textContent = "Offline (50021)";
          }
          showToast("Engine VOICEVOX belum aktif di port 50021", "#eab308");
        }
      } catch (err) {
        showToast("Gagal menghubungi VOICEVOX: " + err.message, "#ef4444");
      } finally {
        vvRefreshBtn.textContent = "Cek Live";
        vvRefreshBtn.disabled = false;
      }
    });
  }
}

// ==========================================
// 4. Load & Populate LLM, TTS, Live2D
// ==========================================
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const data = await res.json();
    currentConfig = data.config;

    // LLM
    const llm = currentConfig.llm || {};
    document.getElementById("llm-provider").value = llm.provider || "ollama";
    document.getElementById("llm-model").value = llm.model || "qwen2.5:3b";
    document.getElementById("llm-base-url").value = llm.base_url || "http://127.0.0.1:11434/v1";
    document.getElementById("llm-api-key").value = llm.api_key || "";
    document.getElementById("llm-temperature").value = llm.temperature || 0.7;
    document.getElementById("temp-val").textContent = llm.temperature || 0.7;

    // TTS Providers
    const tts = currentConfig.tts || {};
    const activeProvider = tts.active_provider || "edge";
    const providers = tts.providers || {};

    // 1. Edge-TTS
    const edgeCfg = providers.edge || {};
    const edgeSelect = document.getElementById("edge-voice-select");
    if (edgeSelect) {
      edgeSelect.innerHTML = "";
      (edgeCfg.available_voices || []).forEach((v) => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = v.name;
        if (v.id === edgeCfg.default_voice) opt.selected = true;
        edgeSelect.appendChild(opt);
      });
    }
    const edgeRate = document.getElementById("edge-rate-input");
    if (edgeRate) edgeRate.value = edgeCfg.rate || "+5%";
    const edgePitch = document.getElementById("edge-pitch-input");
    if (edgePitch) edgePitch.value = edgeCfg.pitch || "+0Hz";

    // 2. Kokoro
    const kokoroCfg = providers.kokoro || {};
    const kokoroSelect = document.getElementById("kokoro-voice-select");
    if (kokoroSelect) {
      kokoroSelect.innerHTML = "";
      (kokoroCfg.available_voices || []).forEach((v) => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = v.name;
        if (v.id === kokoroCfg.default_voice) opt.selected = true;
        kokoroSelect.appendChild(opt);
      });
    }
    const kokoroLang = document.getElementById("kokoro-lang-select");
    if (kokoroLang) kokoroLang.value = kokoroCfg.lang_code || "j";
    const kokoroSpeed = kokoroCfg.speed !== undefined ? kokoroCfg.speed : 1.0;
    const kokoroSlider = document.getElementById("kokoro-speed-slider");
    if (kokoroSlider) {
      kokoroSlider.value = kokoroSpeed;
      document.getElementById("kokoro-speed-val").textContent = `${kokoroSpeed}x`;
    }
    const kokoroPath = document.getElementById("kokoro-python-path");
    if (kokoroPath) kokoroPath.value = kokoroCfg.python_path || "/home/hideri/coding/kokoro-arch/.venv/bin/python3";

    // 3. VOICEVOX
    const vvCfg = providers.voicevox || {};
    const vvUrl = document.getElementById("voicevox-base-url");
    if (vvUrl) vvUrl.value = vvCfg.base_url || "http://127.0.0.1:50021";
    const vvSelect = document.getElementById("voicevox-speaker-select");
    if (vvSelect) {
      vvSelect.innerHTML = "";
      (vvCfg.available_voices || []).forEach((v) => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = v.name;
        if (v.id === vvCfg.default_voice) opt.selected = true;
        vvSelect.appendChild(opt);
      });
    }
    const vvSpeed = vvCfg.speed !== undefined ? vvCfg.speed : 1.0;
    const vvSlider = document.getElementById("voicevox-speed-slider");
    if (vvSlider) {
      vvSlider.value = vvSpeed;
      document.getElementById("voicevox-speed-val").textContent = `${vvSpeed}x`;
    }

    // 4. Custom HTTP
    const customCfg = providers.custom_http || {};
    const custUrl = document.getElementById("custom-http-url");
    if (custUrl) custUrl.value = customCfg.endpoint_url || "http://127.0.0.1:8000/v1/audio/speech";
    const custKey = document.getElementById("custom-http-key");
    if (custKey) custKey.value = customCfg.api_key || "";
    const custModel = document.getElementById("custom-http-model");
    if (custModel) custModel.value = customCfg.model || "tts-1";
    const custVoice = document.getElementById("custom-http-voice");
    if (custVoice) custVoice.value = customCfg.default_voice || "alloy";
    const custFmt = document.getElementById("custom-http-format");
    if (custFmt) custFmt.value = customCfg.response_format || "mp3";

    // Set Active Provider Card
    const targetCard = document.querySelector(`.provider-card[data-provider="${activeProvider}"]`);
    if (targetCard) targetCard.click();

    // Check Live Status Badges
    if (data.tts_providers) {
      data.tts_providers.forEach((p) => {
        const badge = document.getElementById(`badge-${p.id}`);
        if (badge) {
          if (p.is_available) {
            badge.className = "status-badge available";
            badge.textContent = p.id === "kokoro" ? "Lokal Ready" : "Tersedia";
          } else {
            badge.className = "status-badge offline";
            badge.textContent = p.id === "voicevox" ? "Offline (50021)" : "Offline";
          }
        }
      });
    }

    // Live2D Models
    const l2d = currentConfig.live2d || {};
    const modelSelect = document.getElementById("live2d-default-model");
    modelSelect.innerHTML = "";
    for (const [key, val] of Object.entries(l2d.models || {})) {
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = val.name || key;
      if (key === l2d.default_model) opt.selected = true;
      modelSelect.appendChild(opt);
    }
  } catch (err) {
    console.error("Failed to load settings:", err);
    showToast("Gagal memuat pengaturan dari server", "#ef4444");
  }
}

// Provider presets
function initProviderPresets() {
  const providerSelect = document.getElementById("llm-provider");
  const baseUrlInput = document.getElementById("llm-base-url");
  const modelInput = document.getElementById("llm-model");
  const tempSlider = document.getElementById("llm-temperature");
  const tempVal = document.getElementById("temp-val");

  tempSlider.addEventListener("input", (e) => {
    tempVal.textContent = e.target.value;
  });

  providerSelect.addEventListener("change", (e) => {
    const val = e.target.value;
    if (val === "ollama") {
      baseUrlInput.value = "http://127.0.0.1:11434/v1";
      if (!modelInput.value || modelInput.value.includes("gpt") || modelInput.value.includes("llama")) {
        modelInput.value = "qwen2.5:3b";
      }
    } else if (val === "groq") {
      baseUrlInput.value = "https://api.groq.com/openai/v1";
      modelInput.value = "llama-3.3-70b-versatile";
    } else if (val === "openai") {
      baseUrlInput.value = "https://api.openai.com/v1";
      modelInput.value = "gpt-4o-mini";
    } else if (val === "gemini") {
      baseUrlInput.value = "https://generativelanguage.googleapis.com/v1beta/openai/";
      modelInput.value = "gemini-1.5-flash";
    } else if (val === "deepseek") {
      baseUrlInput.value = "https://api.deepseek.com/v1";
      modelInput.value = "deepseek-chat";
    }
  });
}

// ==========================================
// 5. Save Settings
// ==========================================
async function saveSettings() {
  if (!currentConfig) return;

  // 1. Save Persona
  if (personaData) {
    personaData.character_name = document.getElementById("persona-char-name").value.trim() || "Ryza";
    personaData.user_call_name = document.getElementById("persona-user-call").value.trim() || "Sayang";
    personaData.affection_level = parseInt(document.getElementById("slider-affection").value);
    personaData.tsundere_level = parseInt(document.getElementById("slider-tsundere").value);
    personaData.energy_level = parseInt(document.getElementById("slider-energy").value);
    personaData.current_mood = document.getElementById("persona-mood-select").value;

    const activeKey = personaData.active_archetype;
    if (activeKey && personaData.archetypes[activeKey]) {
      personaData.archetypes[activeKey].prompt = document.getElementById("archetype-prompt-input").value.trim();
    }

    await fetch("/api/persona", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(personaData),
    });
  }

  // 2. Save LLM
  currentConfig.llm = {
    provider: document.getElementById("llm-provider").value,
    model: document.getElementById("llm-model").value.trim(),
    base_url: document.getElementById("llm-base-url").value.trim(),
    api_key: document.getElementById("llm-api-key").value.trim(),
    temperature: parseFloat(document.getElementById("llm-temperature").value),
    system_prompt: currentConfig.llm ? currentConfig.llm.system_prompt : "",
  };

  // 3. Save Multi-Provider TTS
  const activeCard = document.querySelector("#tts-provider-grid .provider-card.selected");
  const activeProvider = activeCard ? activeCard.dataset.provider : "edge";

  if (!currentConfig.tts) currentConfig.tts = {};
  if (!currentConfig.tts.providers) currentConfig.tts.providers = {};

  currentConfig.tts.active_provider = activeProvider;

  currentConfig.tts.providers.edge = {
    ...(currentConfig.tts.providers.edge || {}),
    default_voice: document.getElementById("edge-voice-select").value,
    rate: document.getElementById("edge-rate-input").value.trim(),
    pitch: document.getElementById("edge-pitch-input").value.trim(),
    available_voices: currentConfig.tts.providers.edge ? currentConfig.tts.providers.edge.available_voices : []
  };

  currentConfig.tts.providers.kokoro = {
    ...(currentConfig.tts.providers.kokoro || {}),
    default_voice: document.getElementById("kokoro-voice-select").value,
    lang_code: document.getElementById("kokoro-lang-select").value,
    speed: parseFloat(document.getElementById("kokoro-speed-slider").value),
    python_path: document.getElementById("kokoro-python-path").value.trim(),
    available_voices: currentConfig.tts.providers.kokoro ? currentConfig.tts.providers.kokoro.available_voices : []
  };

  currentConfig.tts.providers.voicevox = {
    ...(currentConfig.tts.providers.voicevox || {}),
    base_url: document.getElementById("voicevox-base-url").value.trim(),
    default_voice: document.getElementById("voicevox-speaker-select").value,
    speed: parseFloat(document.getElementById("voicevox-speed-slider").value),
    available_voices: currentConfig.tts.providers.voicevox ? currentConfig.tts.providers.voicevox.available_voices : []
  };

  currentConfig.tts.providers.custom_http = {
    ...(currentConfig.tts.providers.custom_http || {}),
    endpoint_url: document.getElementById("custom-http-url").value.trim(),
    api_key: document.getElementById("custom-http-key").value.trim(),
    model: document.getElementById("custom-http-model").value.trim(),
    default_voice: document.getElementById("custom-http-voice").value.trim(),
    response_format: document.getElementById("custom-http-format").value,
    available_voices: currentConfig.tts.providers.custom_http ? currentConfig.tts.providers.custom_http.available_voices : []
  };

  // Set default_voice alias for active engine
  if (activeProvider === "edge") {
    currentConfig.tts.default_voice = currentConfig.tts.providers.edge.default_voice;
  } else if (activeProvider === "kokoro") {
    currentConfig.tts.default_voice = currentConfig.tts.providers.kokoro.default_voice;
  } else if (activeProvider === "voicevox") {
    currentConfig.tts.default_voice = currentConfig.tts.providers.voicevox.default_voice;
  } else if (activeProvider === "custom_http") {
    currentConfig.tts.default_voice = currentConfig.tts.providers.custom_http.default_voice;
  }

  currentConfig.live2d.default_model = document.getElementById("live2d-default-model").value;

  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentConfig),
    });
    const result = await res.json();
    if (res.ok) {
      showToast("Semua pengaturan & engine TTS berhasil disimpan!");
    } else {
      showToast("Gagal menyimpan: " + (result.detail || "Error"), "#ef4444");
    }
  } catch (err) {
    showToast("Error saat menghubungi server: " + err.message, "#ef4444");
  }
}

// ==========================================
// 5. Background & Appearance
// ==========================================
function initAppearanceSettings() {
  const currentBg = localStorage.getItem("vtuber_bg") || "custom-url";
  const currentUrl = localStorage.getItem("vtuber_bg_url") || "/backgrounds/room-interior-illustration.jpeg";
  const cards = document.querySelectorAll(".preset-bg-card");

  cards.forEach((card) => {
    const bgVal = card.dataset.bg;
    const urlVal = card.dataset.url;

    if (bgVal === "custom-url" && urlVal === currentUrl) {
      card.classList.add("selected");
    } else if (bgVal === currentBg && bgVal !== "custom-url") {
      card.classList.add("selected");
    } else {
      card.classList.remove("selected");
    }

    card.addEventListener("click", () => {
      cards.forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");

      if (card.dataset.bg === "custom-url" && card.dataset.url) {
        localStorage.setItem("vtuber_bg", "custom-url");
        localStorage.setItem("vtuber_bg_url", card.dataset.url);
        showToast(`Wallpaper diterapkan: ${card.textContent}`);
      } else {
        localStorage.setItem("vtuber_bg", card.dataset.bg);
        localStorage.removeItem("vtuber_bg_url");
        showToast(`Tema diterapkan: ${card.textContent}`);
      }
    });
  });

  // URL Background
  const urlInput = document.getElementById("bg-url-input");
  urlInput.value = currentUrl;
  urlInput.addEventListener("change", (e) => {
    const val = e.target.value.trim();
    if (val) {
      localStorage.setItem("vtuber_bg", "custom-url");
      localStorage.setItem("vtuber_bg_url", val);
      cards.forEach((c) => c.classList.remove("selected"));
      showToast("Wallpaper URL disimpan!");
    }
  });

  // File Upload
  const uploadBtn = document.getElementById("upload-bg-btn");
  const fileInput = document.getElementById("bg-file-input");

  uploadBtn.addEventListener("click", async () => {
    if (!fileInput.files || fileInput.files.length === 0) {
      alert("Pilih file gambar terlebih dahulu.");
      return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
      const res = await fetch("/api/upload-bg", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok && data.url) {
        localStorage.setItem("vtuber_bg", "custom-url");
        localStorage.setItem("vtuber_bg_url", data.url);
        urlInput.value = data.url;
        cards.forEach((c) => c.classList.remove("selected"));
        showToast("Wallpaper berhasil diupload dan diterapkan!");
      } else {
        alert("Upload gagal: " + (data.detail || "Error"));
      }
    } catch (e) {
      alert("Error uploading wallpaper: " + e.message);
    }
  });
}

// ==========================================
// 6. Memory & History (SQLite)
// ==========================================
async function loadHistory() {
  const box = document.getElementById("chat-history-box");
  try {
    const res = await fetch("/api/history?session_id=default");
    const data = await res.json();

    if (!data.messages || data.messages.length === 0) {
      box.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 20px;">Belum ada riwayat pesan tersimpan.</div>';
      return;
    }

    box.innerHTML = "";
    data.messages.forEach((msg) => {
      const item = document.createElement("div");
      item.style.marginBottom = "10px";
      item.style.padding = "8px 12px";
      item.style.borderRadius = "6px";
      item.style.background = msg.role === "user" ? "rgba(139, 92, 246, 0.15)" : "rgba(255, 255, 255, 0.05)";

      const roleBadge = document.createElement("span");
      roleBadge.style.fontWeight = "bold";
      roleBadge.style.fontSize = "0.75rem";
      roleBadge.style.color = msg.role === "user" ? "var(--accent)" : "#10b981";
      roleBadge.textContent = msg.role === "user" ? "Kamu: " : "Ryza: ";

      const content = document.createElement("span");
      content.textContent = msg.content;

      item.appendChild(roleBadge);
      item.appendChild(content);
      box.appendChild(item);
    });

    box.scrollTop = box.scrollHeight;
  } catch (err) {
    box.innerHTML = '<div style="color: #ef4444;">Gagal memuat riwayat chat dari SQLite.</div>';
  }
}

// ==========================================
// 7. Real-time Model & System Logs
// ==========================================
async function fetchLogs() {
  const consoleBox = document.getElementById("log-console");
  try {
    const res = await fetch("/api/logs");
    const data = await res.json();

    if (!data.logs || data.logs.length === 0) {
      consoleBox.innerHTML = '<div style="color: #718096;">[Log Console Ready. Menunggu aktivitas...]</div>';
      return;
    }

    consoleBox.innerHTML = "";
    data.logs.forEach((log) => {
      const line = document.createElement("div");
      line.className = `log-line log-${log.level}`;
      line.textContent = `[${log.timestamp}] [${log.level}] [${log.category}] ${log.message}`;
      consoleBox.appendChild(line);
    });

    consoleBox.scrollTop = consoleBox.scrollHeight;
  } catch (e) {
    console.error("Failed to fetch logs:", e);
  }
}

function initLogPolling() {
  document.getElementById("refresh-logs-btn").addEventListener("click", fetchLogs);
  document.getElementById("clear-logs-btn").addEventListener("click", async () => {
    await fetch("/api/logs/clear", { method: "POST" });
    fetchLogs();
  });
}

// ==========================================
// 8. Action Handlers (Voice Test, Memory Reset)
// ==========================================
function initActionButtons() {
  document.getElementById("save-all-btn").addEventListener("click", saveSettings);

  document.getElementById("tts-test-btn").addEventListener("click", async () => {
    const activeCard = document.querySelector("#tts-provider-grid .provider-card.selected");
    const provider = activeCard ? activeCard.dataset.provider : "edge";

    let voice = "";
    if (provider === "edge") {
      voice = document.getElementById("edge-voice-select").value;
    } else if (provider === "kokoro") {
      voice = document.getElementById("kokoro-voice-select").value;
    } else if (provider === "voicevox") {
      voice = document.getElementById("voicevox-speaker-select").value;
    } else if (provider === "custom_http") {
      voice = document.getElementById("custom-http-voice").value.trim();
    }

    const text = document.getElementById("tts-test-text").value.trim() || "Halo! Ini contoh tes suara.";
    const btn = document.getElementById("tts-test-btn");
    const origHtml = btn.innerHTML;
    btn.textContent = "Membuat Suara...";
    btn.disabled = true;

    try {
      const res = await fetch("/api/tts/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, voice, text }),
      });
      const data = await res.json();
      if (res.ok && data.audio) {
        const audioMime = (provider === "kokoro" || provider === "voicevox") ? "audio/wav" : "audio/mp3";
        const audioSrc = `data:${audioMime};base64,${data.audio}`;

        const playerContainer = document.getElementById("tts-test-player-container");
        const player = document.getElementById("tts-test-audio");
        if (playerContainer && player) {
          playerContainer.style.display = "block";
          player.src = audioSrc;
          player.play();
        } else {
          const audio = new Audio(audioSrc);
          audio.play();
        }
        showToast(`Suara preview (${provider}) berhasil diputar!`);
      } else {
        alert("Gagal menghasilkan suara preview: " + (data.detail || "Error"));
      }
    } catch (e) {
      alert("Error preview voice: " + e.message);
    } finally {
      btn.innerHTML = origHtml;
      btn.disabled = false;
    }
  });

  document.getElementById("reset-memory-btn").addEventListener("click", async () => {
    if (!confirm("Reset memori obrolan saat ini? AI akan melupakan konteks sebelumnya.")) return;
    try {
      const res = await fetch("/api/history/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: "default" }),
      });
      if (res.ok) {
        showToast("Memori sesi telah dibersihkan!");
        loadHistory();
      }
    } catch (e) {
      alert("Gagal reset memori: " + e.message);
    }
  });

  document.getElementById("delete-all-history-btn").addEventListener("click", async () => {
    if (!confirm("HAPUS SELURUH riwayat percakapan dari database SQLite? Tindakan ini tidak bisa dibatalkan.")) return;
    try {
      const res = await fetch("/api/history", { method: "DELETE" });
      if (res.ok) {
        showToast("Seluruh riwayat chat berhasil dihapus.");
        loadHistory();
      }
    } catch (e) {
      alert("Gagal menghapus riwayat: " + e.message);
    }
  });
}

function showToast(msg, bg = "rgba(16, 185, 129, 0.9)") {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.style.background = bg;
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 3500);
}
