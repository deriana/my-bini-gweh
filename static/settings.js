/**
 * Settings Page Logic
 * Manages comprehensive configuration for LLM, TTS, Live2D, Custom Wallpaper, SQLite Memory, and System Logs.
 */

let currentConfig = null;

document.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initProviderPresets();
  await loadSettings();
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

      // Auto load logs when log tab is clicked
      if (tab.dataset.tab === "tab-logs") {
        fetchLogs();
      }
    });
  });
}

// ==========================================
// 2. Load & Populate Settings
// ==========================================
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    const data = await res.json();
    currentConfig = data.config;

    // 1. LLM
    const llm = currentConfig.llm || {};
    document.getElementById("llm-provider").value = llm.provider || "ollama";
    document.getElementById("llm-model").value = llm.model || "qwen2.5:3b";
    document.getElementById("llm-base-url").value = llm.base_url || "http://127.0.0.1:11434/v1";
    document.getElementById("llm-api-key").value = llm.api_key || "";
    document.getElementById("llm-temperature").value = llm.temperature || 0.7;
    document.getElementById("temp-val").textContent = llm.temperature || 0.7;
    document.getElementById("llm-system-prompt").value = llm.system_prompt || "";

    // 2. TTS
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

    // 3. Live2D Models
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
// 3. Save Settings
// ==========================================
async function saveSettings() {
  if (!currentConfig) return;

  // Build updated config
  currentConfig.llm = {
    provider: document.getElementById("llm-provider").value,
    model: document.getElementById("llm-model").value.trim(),
    base_url: document.getElementById("llm-base-url").value.trim(),
    api_key: document.getElementById("llm-api-key").value.trim(),
    temperature: parseFloat(document.getElementById("llm-temperature").value),
    system_prompt: document.getElementById("llm-system-prompt").value.trim(),
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
      showToast(result.message || "Pengaturan berhasil disimpan!");
    } else {
      showToast("Gagal menyimpan: " + (result.detail || "Error"), "#ef4444");
    }
  } catch (err) {
    showToast("Error saat menghubungi server: " + err.message, "#ef4444");
  }
}

// ==========================================
// 4. Background & Appearance
// ==========================================
function initAppearanceSettings() {
  const currentBg = localStorage.getItem("vtuber_bg") || "gradient-dark";
  const cards = document.querySelectorAll(".preset-bg-card");

  cards.forEach((card) => {
    if (card.dataset.bg === currentBg) {
      card.classList.add("selected");
    } else {
      card.classList.remove("selected");
    }

    card.addEventListener("click", () => {
      cards.forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      localStorage.setItem("vtuber_bg", card.dataset.bg);
      showToast(`Wallpaper diubah ke: ${card.textContent}`);
    });
  });

  // URL Background
  const urlInput = document.getElementById("bg-url-input");
  urlInput.value = localStorage.getItem("vtuber_bg_url") || "";
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
// 5. Memory & History (SQLite)
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
// 6. Real-time Model & System Logs
// ==========================================
let logPollInterval = null;

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
// 7. Action Handlers (Voice Test, Memory Reset)
// ==========================================
function initActionButtons() {
  // Save All Button
  document.getElementById("save-all-btn").addEventListener("click", saveSettings);

  // Test Voice
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

  // Reset Memory
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

  // Delete All History
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
