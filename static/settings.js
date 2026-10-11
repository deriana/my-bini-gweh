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
// 3. Load & Populate LLM, TTS, Live2D
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

    // TTS
    const tts = currentConfig.tts || {};
    const voiceSelect = document.getElementById("tts-voice");
    voiceSelect.innerHTML = "";
    (tts.available_voices || []).forEach((v) => {
      const opt = document.createElement("option");
      opt.value = v.id;
      opt.textContent = v.name;
      if (v.id === tts.default_voice) opt.selected = true;
      voiceSelect.appendChild(opt);
    });

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
// 4. Save Settings
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

  // 2. Save LLM & TTS
  currentConfig.llm = {
    provider: document.getElementById("llm-provider").value,
    model: document.getElementById("llm-model").value.trim(),
    base_url: document.getElementById("llm-base-url").value.trim(),
    api_key: document.getElementById("llm-api-key").value.trim(),
    temperature: parseFloat(document.getElementById("llm-temperature").value),
    system_prompt: currentConfig.llm ? currentConfig.llm.system_prompt : "",
  };

  currentConfig.tts.default_voice = document.getElementById("tts-voice").value;
  currentConfig.live2d.default_model = document.getElementById("live2d-default-model").value;

  try {
    const res = await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentConfig),
    });
    const result = await res.json();
    if (res.ok) {
      showToast("Semua pengaturan & sifat karakter berhasil disimpan!");
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
    const voice = document.getElementById("tts-voice").value;
    const text = document.getElementById("tts-test-text").value.trim() || "Halo! Ini contoh tes suara.";
    const btn = document.getElementById("tts-test-btn");
    btn.textContent = "Membuat Suara...";
    btn.disabled = true;

    try {
      const res = await fetch("/api/tts/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice, text }),
      });
      const data = await res.json();
      if (res.ok && data.audio) {
        const audio = new Audio("data:audio/mp3;base64," + data.audio);
        audio.play();
      } else {
        alert("Gagal menghasilkan suara preview.");
      }
    } catch (e) {
      alert("Error preview voice: " + e.message);
    } finally {
      btn.textContent = "Dengarkan Suara";
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
