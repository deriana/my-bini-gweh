/**
 * Personal AI VTuber - Frontend Application
 * Handles Pixi.js Live2D rendering, interactive Zoom & Pan, Audio Lip-Sync, Mic STT, and Webcam Vision.
 */

// Global State
let pixiApp = null;
let currentModel = null;
let currentModelKey = null;
let appConfig = null;
let ws = null;
let isWsConnected = false;

// Transform State (Pan & Zoom)
let currentScale = 0.3;
let currentPosX = 0;
let currentPosY = 0;
let isDragging = false;
let dragStart = { x: 0, y: 0 };

// Audio Queue & Lip Sync
const audioQueue = [];
let isPlayingAudio = false;
let mouthInterval = null;

// Camera Vision State
let cameraStream = null;
const cameraBox = document.getElementById("camera-preview-box");
const cameraVideo = document.getElementById("camera-video");
const cameraToggleBtn = document.getElementById("camera-toggle-btn");
const cameraCloseBtn = document.getElementById("camera-close-btn");

// Screen Vision (Desktop Co-Pilot) State
let screenStream = null;
const screenBox = document.getElementById("screen-preview-box");
const screenVideo = document.getElementById("screen-video");
const screenToggleBtn = document.getElementById("screen-toggle-btn");
const screenCloseBtn = document.getElementById("screen-close-btn");

// VAD Hands-Free Continuous Voice Mode
let isVadMode = false;
const vadBtn = document.getElementById("vad-btn");

// UI Elements
const canvas = document.getElementById("live2d-canvas");
const statusPill = document.getElementById("status-pill");
const speechBubble = document.getElementById("speech-bubble");
const bubbleText = document.getElementById("bubble-text");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
const zoomInBtn = document.getElementById("zoom-in-btn");
const zoomOutBtn = document.getElementById("zoom-out-btn");
const resetPosBtn = document.getElementById("reset-pos-btn");
let bubbleTimeout = null;

// ==========================================
// 1. Initialization
// ==========================================
async function init() {
  applyStoredBackground();
  initPixi();
  await loadServerConfig();
  connectWebSocket();
  initEventListeners();
  initTransformControls();
  initSpeechRecognition();

  // Proactive greeting after model is loaded
  setTimeout(fetchProactiveGreeting, 2500);
  // Recurring wellness & hydration reminder every 30 minutes
  setInterval(fetchProactiveReminder, 30 * 60 * 1000);
}

// Apply stored custom wallpaper or preset
function applyStoredBackground() {
  const bgType = localStorage.getItem("vtuber_bg") || "anime-room";
  const bgUrl = localStorage.getItem("vtuber_bg_url");

  document.body.className = "";
  document.body.style.backgroundImage = "";

  if (bgType === "custom-url" && bgUrl) {
    document.body.style.backgroundImage = `url('${bgUrl}')`;
    document.body.style.backgroundSize = "cover";
    document.body.style.backgroundPosition = "center";
  } else if (bgType === "gradient-cyberpunk") {
    document.body.classList.add("bg-gradient-cyberpunk");
  } else if (bgType === "solid-dark") {
    document.body.classList.add("bg-solid-dark");
  } else if (bgType === "obs-greenscreen") {
    document.body.classList.add("bg-obs-greenscreen");
  } else if (bgType === "obs-transparent") {
    document.body.classList.add("bg-obs-transparent");
  } else if (bgType === "gradient-dark") {
    document.body.classList.add("bg-gradient-dark");
  } else {
    // Default: High quality anime room wallpaper
    document.body.style.backgroundImage = "url('/backgrounds/room-interior-illustration.jpeg')";
    document.body.style.backgroundSize = "cover";
    document.body.style.backgroundPosition = "center";
  }
}

// Initialize Pixi.js
function initPixi() {
  pixiApp = new PIXI.Application({
    view: canvas,
    backgroundAlpha: 0, // CRITICAL: Makes canvas transparent so anime wallpaper shows through
    autoDensity: true,
    resizeTo: window,
    antialias: true,
  });

  window.addEventListener("resize", () => {
    if (currentModel && appConfig) {
      applyModelPosition();
    }
  });
}

// Fetch server config and load default model
async function loadServerConfig() {
  try {
    const res = await fetch("/api/config");
    appConfig = await res.json();
    const modelToLoad = appConfig.default_model || "mao_pro";
    if (appConfig.persona && appConfig.persona.current_mood) {
      updateMoodBadge(appConfig.persona.current_mood);
    }
    if (appConfig.persona && appConfig.persona.dominant_language) {
      updateLanguageBadge(appConfig.persona.dominant_language);
    } else {
      updateLanguageBadge("ja");
    }
    if (appConfig.active_tts_provider) {
      const ttsPill = document.getElementById("tts-pill");
      if (ttsPill) {
        const names = {
          edge: "Edge-TTS",
          kokoro: "Kokoro-82M",
          voicevox: "VOICEVOX",
          custom_http: "Custom HTTP"
        };
        ttsPill.textContent = `TTS: ${names[appConfig.active_tts_provider] || appConfig.active_tts_provider}`;
      }
    }
    await switchModel(modelToLoad);
  } catch (err) {
    console.error("Failed to load server config:", err);
    updateStatus("Config Error", "status-offline");
  }
}

// Real-time Mood Badge helper
function updateMoodBadge(mood) {
  const moodPill = document.getElementById("mood-pill");
  const moodText = document.getElementById("mood-text");
  const moodIcon = document.getElementById("mood-icon");
  if (!moodPill || !moodText) return;

  const m = (mood || "Ceria").toLowerCase();
  let icon = "💖";

  if (m.includes("ngambek") || m.includes("marah") || m.includes("kesal")) {
    icon = "😤";
    moodPill.style.borderColor = "rgba(239, 68, 68, 0.5)";
    moodPill.style.color = "#f87171";
  } else if (m.includes("tersipu") || m.includes("malu") || m.includes("blush")) {
    icon = "😳";
    moodPill.style.borderColor = "rgba(244, 114, 182, 0.5)";
    moodPill.style.color = "#f472b6";
  } else if (m.includes("khawatir") || m.includes("sedih")) {
    icon = "🥺";
    moodPill.style.borderColor = "rgba(96, 165, 250, 0.5)";
    moodPill.style.color = "#60a5fa";
  } else if (m.includes("manja") || m.includes("sayang")) {
    icon = "🥰";
    moodPill.style.borderColor = "rgba(236, 72, 153, 0.5)";
    moodPill.style.color = "#ec4899";
  } else {
    icon = "✨";
    moodPill.style.borderColor = "rgba(16, 185, 129, 0.5)";
    moodPill.style.color = "#34d399";
  }

  if (moodIcon) moodIcon.textContent = icon;
  moodText.textContent = `Mood: ${mood}`;
}

// Dominant Language Badge & Quick Toggle helper
const LANG_MAP = {
  ja: { icon: "🇯🇵", label: "JA", title: "Bahasa Respon: Jepang (VOICEVOX Native + Romaji)" },
  id: { icon: "🇮🇩", label: "ID", title: "Bahasa Respon: Indonesia (VOICEVOX Katakana Phonetics)" },
  en: { icon: "🇺🇸", label: "EN", title: "Bahasa Respon: Inggris (VOICEVOX Katakana Phonetics)" },
  auto: { icon: "🌐", label: "AUTO", title: "Bahasa Respon: Otomatis Ikuti Input User" }
};

function updateLanguageBadge(lang) {
  const code = (lang || "ja").toLowerCase();
  const info = LANG_MAP[code] || { icon: "🌐", label: code.toUpperCase(), title: `Bahasa: ${code}` };
  const btn = document.getElementById("lang-quick-btn");
  const iconEl = document.getElementById("lang-quick-icon");
  const textEl = document.getElementById("lang-quick-text");
  if (iconEl) iconEl.textContent = info.icon;
  if (textEl) textEl.textContent = info.label;
  if (btn) btn.title = `${info.title} (Klik untuk Ganti Cepat)`;
}

async function toggleLanguageQuick() {
  const order = ["ja", "id", "en", "auto"];
  const current = (appConfig?.persona?.dominant_language || "ja").toLowerCase();
  const nextIdx = (order.indexOf(current) + 1) % order.length;
  const nextLang = order[nextIdx];

  if (!appConfig) appConfig = {};
  if (!appConfig.persona) appConfig.persona = {};
  appConfig.persona.dominant_language = nextLang;
  updateLanguageBadge(nextLang);

  try {
    const res = await fetch("/api/persona", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dominant_language: nextLang })
    });
    console.log("Updated dominant language to:", nextLang);
  } catch (err) {
    console.error("Failed to update language:", err);
  }
}

// ==========================================
// 2. Live2D Model Management & Positioning
// ==========================================
async function switchModel(modelKey) {
  if (!appConfig || !appConfig.models[modelKey]) return;
  const modelCfg = appConfig.models[modelKey];
  currentModelKey = modelKey;

  updateStatus("Loading Model...", "status-thinking");

  // Remove previous model
  if (currentModel) {
    pixiApp.stage.removeChild(currentModel);
    currentModel.destroy();
    currentModel = null;
  }

  try {
    currentModel = await PIXI.live2d.Live2DModel.from(modelCfg.path, {
      autoInteract: true,
    });

    pixiApp.stage.addChild(currentModel);

    // Load saved transform from localStorage or defaults
    const saved = getSavedTransform(modelKey);
    currentScale = saved.scale || modelCfg.scale || 0.3;
    currentPosX = saved.x !== undefined ? saved.x : (pixiApp.renderer.width / 2 + (modelCfg.x || 0) * pixiApp.renderer.width);
    currentPosY = saved.y !== undefined ? saved.y : (pixiApp.renderer.height * 0.5 + (modelCfg.y || 0) * pixiApp.renderer.height);

    applyModelPosition();

    // Enable drag and pointer interactions
    currentModel.interactive = true;
    enableModelDragging();

    updateStatus("Online", "status-online");

    // Trigger proactive greeting upon startup/model switch
    if (!window.__hasGreeted) {
      window.__hasGreeted = true;
      setTimeout(fetchProactiveGreeting, 1200);
    }
  } catch (err) {
    console.error("Failed to load Live2D model:", err);
    updateStatus("Model Error", "status-offline");
  }
}

function applyModelPosition() {
  if (!currentModel) return;
  currentModel.scale.set(currentScale);
  currentModel.anchor.set(0.5, 0.5);
  currentModel.x = currentPosX;
  currentModel.y = currentPosY;
}

// LocalStorage Transform Helper
function getSavedTransform(modelKey) {
  try {
    const raw = localStorage.getItem(`vtuber_transform_${modelKey}`);
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

function saveTransform() {
  if (!currentModelKey) return;
  const data = { scale: currentScale, x: currentPosX, y: currentPosY };
  localStorage.setItem(`vtuber_transform_${currentModelKey}`, JSON.stringify(data));
}

// Drag & Drop Model Pan, Eye/Head Mouse Tracking, and Touch Reactions
let pointerDownPos = { x: 0, y: 0 };
let pointerDownTime = 0;

function enableModelDragging() {
  if (!currentModel) return;

  currentModel.on("pointerdown", (event) => {
    isDragging = true;
    dragStart.x = event.data.global.x - currentModel.x;
    dragStart.y = event.data.global.y - currentModel.y;
    pointerDownPos = { x: event.data.global.x, y: event.data.global.y };
    pointerDownTime = Date.now();
  });

  pixiApp.stage.interactive = true;
  pixiApp.stage.on("pointermove", (event) => {
    if (isDragging && currentModel) {
      currentPosX = event.data.global.x - dragStart.x;
      currentPosY = event.data.global.y - dragStart.y;
      currentModel.x = currentPosX;
      currentModel.y = currentPosY;
    } else if (currentModel && typeof currentModel.focus === "function") {
      // Real-time eye & head mouse tracking
      currentModel.focus(event.data.global.x, event.data.global.y);
    }
  });

  currentModel.on("pointerup", (event) => {
    if (isDragging) {
      isDragging = false;
      saveTransform();

      // Check if action was a pure tap/click rather than a drag
      const dist = Math.hypot(event.data.global.x - pointerDownPos.x, event.data.global.y - pointerDownPos.y);
      const elapsed = Date.now() - pointerDownTime;
      if (dist < 15 && elapsed < 450) {
        const bounds = currentModel.getBounds();
        const relY = (event.data.global.y - bounds.y) / (bounds.height || 1);
        let touchType = "headpat";
        if (relY > 0.52) {
          touchType = "body";
        } else if (relY > 0.28) {
          touchType = "poke";
        }
        triggerTouchReaction(touchType);
      }
    }
  });

  pixiApp.stage.on("pointerup", () => {
    if (isDragging) {
      isDragging = false;
      saveTransform();
    }
  });

  pixiApp.stage.on("pointerupoutside", () => {
    if (isDragging) {
      isDragging = false;
      saveTransform();
    }
  });
}

// Helper to escape HTML safely
function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Sets speech bubble content with optional Romaji furigana/subtitle
function setBubbleContent(item) {
  if (item && item.romaji && item.clean_text) {
    bubbleText.innerHTML = `<span class="bubble-jp">${escapeHtml(item.clean_text)}</span><span class="bubble-romaji">${escapeHtml(item.romaji)}</span>`;
  } else if (item && item.display_text) {
    bubbleText.textContent = item.display_text;
  } else if (typeof item === "string") {
    bubbleText.textContent = item;
  } else {
    bubbleText.textContent = (item && (item.clean_text || item.text)) || "";
  }
}

// Helper to show speech bubble
function showSpeechBubble(text, romaji = null) {
  if (romaji) {
    bubbleText.innerHTML = `<span class="bubble-jp">${escapeHtml(text)}</span><span class="bubble-romaji">${escapeHtml(romaji)}</span>`;
  } else {
    bubbleText.textContent = text;
  }
  speechBubble.classList.remove("hidden");
  if (bubbleTimeout) clearTimeout(bubbleTimeout);
  bubbleTimeout = setTimeout(() => {
    speechBubble.classList.add("hidden");
  }, 4500);
}

// Touch Reaction Trigger (Headpat, Poke, Body Tap)
async function triggerTouchReaction(touchType) {
  if (isPlayingAudio) return;
  try {
    const res = await fetch("/api/interact/touch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        touch_type: touchType,
        model: currentModelKey || "mao_pro",
        voice: (appConfig && appConfig.default_voice) ? appConfig.default_voice : "3",
        session_id: "default"
      })
    });
    const data = await res.json();
    if (res.ok && data.text) {
      if (data.audio) {
        queueAudioPayload({
          text: data.text,
          clean_text: data.text,
          audio: data.audio,
          volumes: data.volumes || [],
          expression_index: data.expression_index
        });
      } else {
        if (data.expression_index !== null && data.expression_index !== undefined) {
          setModelExpression(data.expression_index);
        }
        showSpeechBubble(data.text);
      }
    }
  } catch (err) {
    console.error("Touch reaction error:", err);
  }
}

// Autonomous Proactive Greeting (Time-based Greeting on Startup)
async function fetchProactiveGreeting() {
  if (isPlayingAudio) return;
  try {
    const res = await fetch(`/api/proactive/greeting?model=${currentModelKey || "mao_pro"}`);
    const data = await res.json();
    if (res.ok && data.text) {
      if (data.audio) {
        queueAudioPayload({
          text: data.text,
          clean_text: data.text,
          audio: data.audio,
          volumes: data.volumes || [],
          expression_index: data.expression_index
        });
      } else {
        if (data.expression_index !== null && data.expression_index !== undefined) {
          setModelExpression(data.expression_index);
        }
        showSpeechBubble(data.text);
      }
    }
  } catch (err) {
    console.error("Proactive greeting error:", err);
  }
}

// Periodic Wellness & Break Reminder
async function fetchProactiveReminder() {
  if (isPlayingAudio) return;
  try {
    const res = await fetch(`/api/proactive/reminder?model=${currentModelKey || "mao_pro"}`);
    const data = await res.json();
    if (res.ok && data.text) {
      if (data.audio) {
        queueAudioPayload({
          text: data.text,
          clean_text: data.text,
          audio: data.audio,
          volumes: data.volumes || [],
          expression_index: data.expression_index
        });
      } else {
        if (data.expression_index !== null && data.expression_index !== undefined) {
          setModelExpression(data.expression_index);
        }
        showSpeechBubble(data.text);
      }
    }
  } catch (err) {
    console.error("Proactive reminder error:", err);
  }
}

// Zoom & Transform Controls
function initTransformControls() {
  // Mouse Wheel Zoom
  canvas.addEventListener("wheel", (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
    adjustZoom(zoomFactor);
  }, { passive: false });

  // Zoom In Button
  zoomInBtn.addEventListener("click", () => adjustZoom(1.15));

  // Zoom Out Button
  zoomOutBtn.addEventListener("click", () => adjustZoom(0.85));

  // Reset Position Button
  resetPosBtn.addEventListener("click", () => {
    if (!currentModel || !appConfig || !appConfig.models[currentModelKey]) return;
    const modelCfg = appConfig.models[currentModelKey];
    currentScale = modelCfg.scale || 0.3;
    currentPosX = pixiApp.renderer.width / 2 + (modelCfg.x || 0) * pixiApp.renderer.width;
    currentPosY = pixiApp.renderer.height * 0.5 + (modelCfg.y || 0) * pixiApp.renderer.height;
    applyModelPosition();
    saveTransform();
  });
}

function adjustZoom(factor) {
  if (!currentModel) return;
  currentScale = Math.min(Math.max(0.08, currentScale * factor), 3.0);
  currentModel.scale.set(currentScale);
  saveTransform();
}

// Set model expression by index
function setModelExpression(index) {
  if (!currentModel || index === null || index === undefined) return;
  try {
    if (typeof currentModel.expression === "function") {
      currentModel.expression(index);
    }
  } catch (e) {
    console.debug("Expression set failed:", e);
  }
}

// Set model mouth parameter
function setMouthOpen(value) {
  if (!currentModel || !currentModel.internalModel) return;
  try {
    const core = currentModel.internalModel.coreModel;
    if (core && typeof core.setParameterValueById === "function") {
      core.setParameterValueById("ParamMouthOpenY", value);
    }
  } catch (e) {}
}

// ==========================================
// 3. Audio Lip-Sync Queue
// ==========================================
function queueAudioPayload(payload) {
  audioQueue.push(payload);
  if (!isPlayingAudio) {
    playNextAudio();
  }
}

function playNextAudio() {
  if (audioQueue.length === 0) {
    isPlayingAudio = false;
    speechBubble.classList.remove("speaking");
    if (bubbleTimeout) clearTimeout(bubbleTimeout);
    bubbleTimeout = setTimeout(() => {
      speechBubble.classList.add("hidden");
    }, 4500);

    // Hands-Free VAD Mode: resume listening automatically after speaking finishes
    if (isVadMode) {
      setTimeout(() => {
        if (isVadMode && !isPlayingAudio && !isRecording) {
          startVadListening();
        }
      }, 400);
    }
    return;
  }

  isPlayingAudio = true;
  const item = audioQueue.shift();

  // Show speech bubble
  setBubbleContent(item);
  speechBubble.classList.remove("hidden");
  speechBubble.classList.add("speaking");
  if (bubbleTimeout) clearTimeout(bubbleTimeout);

  // Trigger emotion expression if present
  if (item.expression_index !== null && item.expression_index !== undefined) {
    setModelExpression(item.expression_index);
  }

  // Play audio
  const audio = new Audio("data:audio/mp3;base64," + item.audio);
  const volumes = item.volumes || [];
  const chunkLengthMs = 20;
  let startTime = null;

  audio.onplay = () => {
    startTime = performance.now();
    speechBubble.classList.add("speaking");
    if (mouthInterval) clearInterval(mouthInterval);

    mouthInterval = setInterval(() => {
      if (audio.paused || audio.ended) {
        clearInterval(mouthInterval);
        setMouthOpen(0);
        return;
      }
      const elapsedMs = performance.now() - startTime;
      const index = Math.floor(elapsedMs / chunkLengthMs);
      const vol = volumes[index] !== undefined ? volumes[index] : 0;
      setMouthOpen(Math.min(1.0, vol * 1.3));
    }, chunkLengthMs);
  };

  audio.onended = () => {
    if (mouthInterval) clearInterval(mouthInterval);
    setMouthOpen(0);
    playNextAudio();
  };

  audio.onerror = (e) => {
    console.error("Audio playback error:", e);
    speechBubble.classList.remove("speaking");
    if (mouthInterval) clearInterval(mouthInterval);
    setMouthOpen(0);
    playNextAudio();
  };

  audio.play().catch((e) => {
    console.warn("Autoplay was blocked or failed:", e);
    speechBubble.classList.remove("speaking");
    playNextAudio();
  });
}

// ==========================================
// 4. WebSocket Communication
// ==========================================
function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    isWsConnected = true;
    updateStatus("Online", "status-online");
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);

      if (msg.type === "status") {
        updateStatus(msg.status, "status-thinking");
      } else if (msg.type === "mood_update") {
        updateMoodBadge(msg.mood);
      } else if (msg.type === "audio") {
        queueAudioPayload(msg);
        updateStatus("Berbicara...", "status-online");
      } else if (msg.type === "text") {
        setBubbleContent(msg);
        speechBubble.classList.remove("hidden");
      } else if (msg.type === "done") {
        updateStatus("Online", "status-online");
      }
    } catch (e) {
      console.error("Error parsing WS message:", e);
    }
  };

  ws.onclose = () => {
    isWsConnected = false;
    updateStatus("Offline (Reconnecting...)", "status-offline");
    setTimeout(connectWebSocket, 3000);
  };

  ws.onerror = () => {
    isWsConnected = false;
    updateStatus("Offline", "status-offline");
  };
}

function updateStatus(text, className) {
  statusPill.textContent = text;
  statusPill.className = `pill ${className}`;
}

// ==========================================
// 5. Sending Messages & Camera / Screen Capture
// ==========================================
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text && !cameraStream && !screenStream) return;
  if (!isWsConnected) {
    alert("Koneksi ke server terputus. Silakan tunggu sebentar.");
    return;
  }

  let capturedImage = null;

  // Screen Vision has priority if sharing screen, otherwise webcam
  if (screenStream) {
    capturedImage = captureScreenFrame();
  } else if (cameraStream) {
    capturedImage = captureCameraFrame();
  }

  // Clear input
  chatInput.value = "";

  // Stop recording if speaking
  if (recognition && isRecording) {
    recognition.stop();
  }

  // Send to server
  ws.send(
    JSON.stringify({
      type: "chat",
      text: text,
      image: capturedImage,
      model: currentModelKey,
      voice: appConfig ? appConfig.default_voice : "3",
      session_id: "default",
    })
  );

  updateStatus("Berpikir...", "status-thinking");
}

function captureCameraFrame() {
  if (!cameraVideo.videoWidth) return null;
  const offscreenCanvas = document.createElement("canvas");
  offscreenCanvas.width = cameraVideo.videoWidth;
  offscreenCanvas.height = cameraVideo.videoHeight;
  const ctx = offscreenCanvas.getContext("2d");
  ctx.drawImage(cameraVideo, 0, 0, offscreenCanvas.width, offscreenCanvas.height);
  return offscreenCanvas.toDataURL("image/jpeg", 0.7);
}

// ==========================================
// 6. Camera Controls
// ==========================================
async function toggleCamera() {
  if (cameraStream) {
    stopCamera();
  } else {
    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 } },
      });
      cameraVideo.srcObject = cameraStream;
      cameraBox.classList.remove("hidden");
      cameraToggleBtn.classList.add("active");
    } catch (err) {
      alert("Gagal mengakses kamera: " + err.message);
    }
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }
  cameraBox.classList.add("hidden");
  cameraToggleBtn.classList.remove("active");
}

// ==========================================
// 6b. Screen Sharing Controls (Desktop Co-Pilot)
// ==========================================
async function toggleScreen() {
  if (screenStream) {
    stopScreen();
  } else {
    try {
      screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: { cursor: "always" },
        audio: false,
      });
      screenVideo.srcObject = screenStream;
      screenBox.classList.remove("hidden");
      if (screenToggleBtn) screenToggleBtn.classList.add("active");

      // Handle user stopping screen share from browser banner
      screenStream.getVideoTracks()[0].onended = () => {
        stopScreen();
      };
    } catch (err) {
      console.warn("Screen share cancelled or failed:", err);
    }
  }
}

function stopScreen() {
  if (screenStream) {
    screenStream.getTracks().forEach((track) => track.stop());
    screenStream = null;
  }
  screenBox.classList.add("hidden");
  if (screenToggleBtn) screenToggleBtn.classList.remove("active");
}

function captureScreenFrame() {
  if (!screenVideo.videoWidth) return null;
  const offscreenCanvas = document.createElement("canvas");
  offscreenCanvas.width = screenVideo.videoWidth;
  offscreenCanvas.height = screenVideo.videoHeight;
  const ctx = offscreenCanvas.getContext("2d");
  ctx.drawImage(screenVideo, 0, 0, offscreenCanvas.width, offscreenCanvas.height);
  return offscreenCanvas.toDataURL("image/jpeg", 0.7);
}

// ==========================================
// 7. Voice Input (Speech Recognition) & VAD
// ==========================================
let recognition = null;
let isRecording = false;

function initSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    micBtn.style.display = "none";
    if (vadBtn) vadBtn.style.display = "none";
    console.warn("Web Speech API tidak didukung di browser ini.");
    return;
  }

  recognition = new SpeechRec();
  recognition.lang = "id-ID";
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onstart = () => {
    isRecording = true;
    micBtn.classList.add("recording");
    updateStatus("Mendengarkan...", "status-thinking");
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    chatInput.value = transcript;
    sendMessage();
  };

  recognition.onerror = (event) => {
    console.warn("Speech recognition error:", event.error);
    stopRecording();
  };

  recognition.onend = () => {
    stopRecording();
    // In VAD hands-free mode, restart listening automatically if AI isn't speaking
    if (isVadMode && !isPlayingAudio) {
      setTimeout(() => {
        if (isVadMode && !isPlayingAudio && !isRecording) {
          startVadListening();
        }
      }, 400);
    }
  };
}

function toggleRecording() {
  if (!recognition) return;
  if (isRecording) {
    recognition.stop();
    stopRecording();
  } else {
    try {
      recognition.start();
    } catch (e) {
      console.warn("Recognition start error:", e);
    }
  }
}

function stopRecording() {
  isRecording = false;
  micBtn.classList.remove("recording");
  if (isWsConnected) updateStatus("Online", "status-online");
}

// Hands-Free Continuous Voice Mode (VAD)
function toggleVadMode() {
  isVadMode = !isVadMode;
  if (isVadMode) {
    if (vadBtn) {
      vadBtn.classList.add("active");
      vadBtn.title = "Hands-Free Voice: ON";
    }
    startVadListening();
  } else {
    if (vadBtn) {
      vadBtn.classList.remove("active");
      vadBtn.title = "Mode Bicara Otomatis Tanpa Tangan (Hands-Free VAD Mode)";
    }
    if (isRecording) {
      stopRecording();
    }
  }
}

function startVadListening() {
  if (!recognition || isPlayingAudio || isRecording) return;
  try {
    recognition.start();
  } catch (e) {
    // Recognition might already be starting
  }
}

// ==========================================
// 8. Event Listeners
// ==========================================
function initEventListeners() {
  cameraToggleBtn.addEventListener("click", toggleCamera);
  cameraCloseBtn.addEventListener("click", stopCamera);
  if (screenToggleBtn) screenToggleBtn.addEventListener("click", toggleScreen);
  if (screenCloseBtn) screenCloseBtn.addEventListener("click", stopScreen);
  micBtn.addEventListener("click", toggleRecording);
  if (vadBtn) vadBtn.addEventListener("click", toggleVadMode);
  sendBtn.addEventListener("click", sendMessage);

  const langQuickBtn = document.getElementById("lang-quick-btn");
  if (langQuickBtn) {
    langQuickBtn.addEventListener("click", toggleLanguageQuick);
  }

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
}

// Start application
document.addEventListener("DOMContentLoaded", init);
