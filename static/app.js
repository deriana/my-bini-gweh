/**
 * Personal AI VTuber - Frontend Application
 * Handles Pixi.js Live2D rendering, Audio Queue Lip-Sync, Mic STT, and Webcam Vision.
 */

// Global State
let pixiApp = null;
let currentModel = null;
let currentModelKey = null;
let appConfig = null;
let ws = null;
let isWsConnected = false;

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

// UI Elements
const statusPill = document.getElementById("status-pill");
const modelSelect = document.getElementById("model-select");
const voiceSelect = document.getElementById("voice-select");
const speechBubble = document.getElementById("speech-bubble");
const bubbleText = document.getElementById("bubble-text");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const micBtn = document.getElementById("mic-btn");
let bubbleTimeout = null;

// ==========================================
// 1. Initialization
// ==========================================
async function init() {
  initPixi();
  await loadServerConfig();
  connectWebSocket();
  initEventListeners();
  initSpeechRecognition();
}

// Initialize Pixi.js
function initPixi() {
  const canvas = document.getElementById("live2d-canvas");
  pixiApp = new PIXI.Application({
    view: canvas,
    transparent: true,
    autoDensity: true,
    resizeTo: window,
    antialias: true,
  });

  window.addEventListener("resize", () => {
    if (currentModel && appConfig) {
      positionModel(appConfig.models[currentModelKey]);
    }
  });
}

// Fetch server config and populate dropdowns
async function loadServerConfig() {
  try {
    const res = await fetch("/api/config");
    appConfig = await res.json();

    // Populate Models
    modelSelect.innerHTML = "";
    for (const [key, model] of Object.entries(appConfig.models)) {
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = model.name;
      if (key === appConfig.default_model) opt.selected = true;
      modelSelect.appendChild(opt);
    }

    // Populate Voices
    voiceSelect.innerHTML = "";
    for (const voice of appConfig.voices) {
      const opt = document.createElement("option");
      opt.value = voice.id;
      opt.textContent = voice.name;
      if (voice.id === appConfig.default_voice) opt.selected = true;
      voiceSelect.appendChild(opt);
    }

    // Load initial model
    await switchModel(appConfig.default_model);
  } catch (err) {
    console.error("Failed to load server config:", err);
    updateStatus("Config Error", "status-offline");
  }
}

// ==========================================
// 2. Live2D Model Management
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
    positionModel(modelCfg);

    // Make interactive (drag/track mouse)
    currentModel.interactive = true;

    updateStatus("Online", "status-online");
  } catch (err) {
    console.error("Failed to load Live2D model:", err);
    updateStatus("Model Error", "status-offline");
  }
}

function positionModel(modelCfg) {
  if (!currentModel || !modelCfg) return;
  const renderer = pixiApp.renderer;

  currentModel.scale.set(modelCfg.scale || 0.3);
  currentModel.anchor.set(0.5, 0.5);

  currentModel.x = renderer.width / 2 + (modelCfg.x || 0) * renderer.width;
  currentModel.y = renderer.height * 0.5 + (modelCfg.y || 0) * renderer.height;
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
    // Set timer to hide speech bubble
    if (bubbleTimeout) clearTimeout(bubbleTimeout);
    bubbleTimeout = setTimeout(() => {
      speechBubble.classList.add("hidden");
    }, 4000);
    return;
  }

  isPlayingAudio = true;
  const item = audioQueue.shift();

  // Show speech bubble
  bubbleText.textContent = item.clean_text || item.text;
  speechBubble.classList.remove("hidden");
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
    if (mouthInterval) clearInterval(mouthInterval);
    setMouthOpen(0);
    playNextAudio();
  };

  audio.play().catch((e) => {
    console.warn("Autoplay was blocked or failed:", e);
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
      } else if (msg.type === "audio") {
        queueAudioPayload(msg);
        updateStatus("Berbicara...", "status-online");
      } else if (msg.type === "text") {
        bubbleText.textContent = msg.clean_text || msg.text;
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
// 5. Sending Messages & Camera Capture
// ==========================================
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text && !cameraStream) return;
  if (!isWsConnected) {
    alert("Koneksi ke server terputus. Silakan tunggu.");
    return;
  }

  let capturedImage = null;

  // If camera is active, capture frame
  if (cameraStream) {
    capturedImage = captureCameraFrame();
  }

  // Clear input
  chatInput.value = "";

  // Send to server
  ws.send(
    JSON.stringify({
      type: "chat",
      text: text,
      image: capturedImage,
      model: modelSelect.value,
      voice: voiceSelect.value,
    })
  );

  updateStatus("Berpikir...", "status-thinking");
}

function captureCameraFrame() {
  if (!cameraVideo.videoWidth) return null;
  const canvas = document.createElement("canvas");
  canvas.width = cameraVideo.videoWidth;
  canvas.height = cameraVideo.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.7);
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
// 7. Voice Input (Speech Recognition)
// ==========================================
let recognition = null;
let isRecording = false;

function initSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) {
    micBtn.style.display = "none";
    console.warn("Web Speech API not supported in this browser.");
    return;
  }

  recognition = new SpeechRec();
  recognition.lang = "id-ID"; // Default Indonesian
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
      console.warn("Recognition start failed:", e);
    }
  }
}

function stopRecording() {
  isRecording = false;
  micBtn.classList.remove("recording");
  if (isWsConnected) updateStatus("Online", "status-online");
}

// ==========================================
// 8. Event Listeners
// ==========================================
function initEventListeners() {
  modelSelect.addEventListener("change", (e) => switchModel(e.target.value));
  cameraToggleBtn.addEventListener("click", toggleCamera);
  cameraCloseBtn.addEventListener("click", stopCamera);
  micBtn.addEventListener("click", toggleRecording);
  sendBtn.addEventListener("click", sendMessage);

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
}

// Start application on DOM ready
document.addEventListener("DOMContentLoaded", init);
