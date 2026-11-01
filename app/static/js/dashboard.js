/**
 * Project P_311: IoT Fault Diagnosis Assistant - Dashboard Controller
 */

let devices = {};
let vibrationChart = null;
let currentChartDevice = "MTR-101";
let socket = null;
let chartHistory = {
  labels: [],
  data: []
};
let publicAccessUrl = "";

document.addEventListener("DOMContentLoaded", () => {
  initChart();
  initWebSocket();
  fetchInitialData();
  fetchRemoteStatus();

  document.getElementById("chart-device-select").addEventListener("change", (e) => {
    currentChartDevice = e.target.value;
    chartHistory = { labels: [], data: [] };
    if (vibrationChart) {
      vibrationChart.data.labels = [];
      vibrationChart.data.datasets[0].data = [];
      vibrationChart.update();
    }
  });
});

function initChart() {
  const ctx = document.getElementById("vibrationChart").getContext("2d");
  
  // ISO 10816-3 Threshold Guide Lines
  vibrationChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Vibration RMS (mm/s)",
          data: [],
          borderColor: "#06b6d4",
          backgroundColor: "rgba(6, 182, 212, 0.1)",
          borderWidth: 2.5,
          tension: 0.35,
          fill: true,
          pointRadius: 3,
          pointBackgroundColor: "#06b6d4"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 300 },
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.05)" },
          ticks: { color: "#94a3b8", font: { family: "JetBrains Mono", size: 10 } }
        },
        y: {
          min: 0,
          max: 10,
          grid: { color: "rgba(255, 255, 255, 0.07)" },
          ticks: { color: "#94a3b8", font: { family: "JetBrains Mono", size: 10 } }
        }
      },
      plugins: {
        legend: { labels: { color: "#cbd5e1", font: { size: 11 } } },
        tooltip: {
          backgroundColor: "#0f172a",
          titleFont: { family: "JetBrains Mono" },
          bodyFont: { family: "JetBrains Mono" }
        }
      }
    }
  });
}

function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/live`;
  const wsDot = document.getElementById("ws-dot");
  const wsStatus = document.getElementById("ws-status");

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    wsDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 pulse-dot";
    wsStatus.textContent = "Live WS Connected";
  };

  socket.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "telemetry") {
        handleIncomingTelemetry(msg.data);
      } else if (msg.type === "alert") {
        handleIncomingAlert(msg.data);
      } else if (msg.type === "snapshot") {
        msg.devices.forEach(handleIncomingTelemetry);
      }
    } catch (e) {
      console.error("WS error:", e);
    }
  };

  socket.onclose = () => {
    wsDot.className = "w-2.5 h-2.5 rounded-full bg-amber-500";
    wsStatus.textContent = "Reconnecting...";
    setTimeout(initWebSocket, 3000);
  };
}

async function fetchInitialData() {
  try {
    const res = await fetch("/api/devices");
    const data = await res.json();
    data.forEach(d => {
      if (d.latest_telemetry) {
        handleIncomingTelemetry(d.latest_telemetry);
      }
    });
  } catch (e) {
    console.error("Error fetching devices:", e);
  }
}

async function fetchRemoteStatus() {
  try {
    const res = await fetch("/api/tunnel/status");
    const info = await res.json();
    document.getElementById("lan-url-display").textContent = info.local_network_url || "http://localhost:8000";
    
    if (info.public_url) {
      publicAccessUrl = info.public_url;
      document.getElementById("public-url-input").value = info.public_url;
      renderQrCode(info.public_url);
    } else {
      document.getElementById("public-url-input").value = info.local_network_url || "Waiting for tunnel...";
      renderQrCode(info.local_network_url || window.location.href);
    }
  } catch (e) {
    console.warn("Could not fetch remote tunnel info:", e);
  }
}

function handleIncomingTelemetry(t) {
  devices[t.device_id] = t;
  renderDeviceCards();

  // If this device is active in the chart, push data point
  if (t.device_id === currentChartDevice && vibrationChart) {
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    if (vibrationChart.data.labels.length > 20) {
      vibrationChart.data.labels.shift();
      vibrationChart.data.datasets[0].data.shift();
    }
    
    vibrationChart.data.labels.push(now);
    vibrationChart.data.datasets[0].data.push(t.vibration_rms);

    // Color indicator based on severity
    if (t.iso_zone === "Zone D") {
      vibrationChart.data.datasets[0].borderColor = "#ef4444";
      vibrationChart.data.datasets[0].pointBackgroundColor = "#ef4444";
    } else if (t.iso_zone === "Zone C") {
      vibrationChart.data.datasets[0].borderColor = "#f59e0b";
      vibrationChart.data.datasets[0].pointBackgroundColor = "#f59e0b";
    } else {
      vibrationChart.data.datasets[0].borderColor = "#06b6d4";
      vibrationChart.data.datasets[0].pointBackgroundColor = "#06b6d4";
    }

    vibrationChart.update();
  }
}

function renderDeviceCards() {
  const container = document.getElementById("device-cards");
  const deviceList = Object.values(devices);

  if (deviceList.length === 0) return;

  container.innerHTML = deviceList.map(t => {
    let statusBg = "border-emerald-600/40 hover:border-emerald-500";
    let badgeClass = "bg-emerald-950 text-emerald-400 border-emerald-800";
    let statusText = "HEALTHY";
    let iconClass = "fa-circle-check text-emerald-400";

    if (t.iso_zone === "Zone D" || t.temperature > 85) {
      statusBg = "border-red-600/60 bg-red-950/20 hover:border-red-500";
      badgeClass = "bg-red-950 text-red-400 border-red-800";
      statusText = "CRITICAL";
      iconClass = "fa-triangle-exclamation text-red-400";
    } else if (t.iso_zone === "Zone C" || t.temperature > 70 || t.fault_code !== "NORMAL") {
      statusBg = "border-amber-600/60 bg-amber-950/20 hover:border-amber-500";
      badgeClass = "bg-amber-950 text-amber-400 border-amber-800";
      statusText = "WARNING";
      iconClass = "fa-circle-exclamation text-amber-400";
    }

    return `
      <div class="glass-card rounded-2xl p-4 border transition ${statusBg} flex flex-col justify-between space-y-3">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center space-x-1.5">
              <span class="font-bold text-white text-base tracking-tight">${t.device_id}</span>
              <i class="fa-solid ${iconClass} text-xs"></i>
            </div>
            <span class="text-[11px] text-slate-400 block">${t.device_type}</span>
          </div>
          <span class="px-2 py-0.5 text-[10px] font-bold border rounded font-mono ${badgeClass}">${statusText}</span>
        </div>

        <!-- HEALTH & ISO -->
        <div class="flex items-center justify-between text-xs pt-1 border-t border-slate-800/80">
          <div>
            <span class="text-[10px] text-slate-400 uppercase font-semibold">Health Score</span>
            <div class="text-sm font-bold font-mono ${t.health_index > 70 ? 'text-emerald-400' : t.health_index > 40 ? 'text-amber-400' : 'text-red-400'}">
              ${t.health_index}%
            </div>
          </div>
          <div class="text-right">
            <span class="text-[10px] text-slate-400 uppercase font-semibold">ISO 10816</span>
            <div class="text-xs font-mono font-bold text-cyan-300">${t.iso_zone}</div>
          </div>
        </div>

        <!-- SENSOR METRICS -->
        <div class="grid grid-cols-2 gap-2 text-[11px] bg-slate-950/50 p-2 rounded-xl font-mono">
          <div>
            <span class="text-slate-500 text-[10px] block">Vib RMS:</span>
            <span class="text-white font-bold">${t.vibration_rms} mm/s</span>
          </div>
          <div>
            <span class="text-slate-500 text-[10px] block">Peak Accel:</span>
            <span class="text-white font-bold">${t.vibration_peak} g</span>
          </div>
          <div>
            <span class="text-slate-500 text-[10px] block">Temp:</span>
            <span class="text-white font-bold">${t.temperature} °C</span>
          </div>
          <div>
            <span class="text-slate-500 text-[10px] block">Current:</span>
            <span class="text-white font-bold">${t.current_draw} A</span>
          </div>
        </div>

        <!-- ACTION BUTTON -->
        <button onclick="requestDiagnosis('${t.device_id}')" class="w-full py-2 bg-gradient-to-r from-cyan-600/80 to-indigo-600/80 hover:from-cyan-500 hover:to-indigo-500 rounded-xl text-xs font-bold text-white transition flex items-center justify-center space-x-1.5 shadow">
          <i class="fa-solid fa-stethoscope text-[11px]"></i>
          <span>Run AI Diagnosis</span>
        </button>
      </div>
    `;
  }).join("");
}

function handleIncomingAlert(alert) {
  const container = document.getElementById("alert-banner-container");
  const banner = document.getElementById("alert-banner");
  const title = document.getElementById("alert-title");
  const msg = document.getElementById("alert-msg");
  const icon = document.getElementById("alert-icon");
  const btn = document.getElementById("alert-diag-btn");

  container.classList.remove("hidden");
  title.textContent = `ALERT [${alert.device_id}]: ${alert.fault_code}`;
  msg.textContent = alert.message;

  if (alert.severity === "CRITICAL") {
    banner.className = "rounded-xl border border-red-500 bg-red-950/80 p-4 flex items-start justify-between gap-4 text-red-200 shadow-xl shadow-red-950/40";
    icon.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-red-400"></i>`;
  } else {
    banner.className = "rounded-xl border border-amber-500 bg-amber-950/80 p-4 flex items-start justify-between gap-4 text-amber-200 shadow-xl shadow-amber-950/40";
    icon.innerHTML = `<i class="fa-solid fa-circle-exclamation text-amber-400"></i>`;
  }

  btn.onclick = () => requestDiagnosis(alert.device_id);
}

async function requestDiagnosis(deviceId) {
  const modal = document.getElementById("diagnosis-modal");
  modal.classList.remove("hidden");

  document.getElementById("modal-device-id").textContent = `Diagnosing ${deviceId}...`;
  document.getElementById("modal-diag-id").textContent = "Consulting RAG Vector Base & LLM...";
  document.getElementById("modal-fault-title").textContent = "Analyzing telemetry...";
  document.getElementById("modal-iso-eval").textContent = "Evaluating ISO 10816...";
  document.getElementById("modal-root-cause").innerHTML = "<div class='flex items-center space-x-2 text-cyan-400'><i class='fa-solid fa-spinner fa-spin'></i><span>Synthesizing root cause analysis from technical manuals...</span></div>";
  document.getElementById("modal-actions").innerHTML = "";
  document.getElementById("modal-references").innerHTML = "";

  try {
    const res = await fetch("/api/diagnose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_id: deviceId })
    });
    const diag = await res.json();
    renderDiagnosisResult(diag);
  } catch (e) {
    document.getElementById("modal-root-cause").innerHTML = `<span class='text-red-400'>Diagnosis error: ${e.message}</span>`;
  }
}

function renderDiagnosisResult(diag) {
  document.getElementById("modal-device-id").textContent = `${diag.device_id} (${diag.device_type})`;
  document.getElementById("modal-diag-id").textContent = `ID: ${diag.diagnosis_id} | ${new Date(diag.timestamp).toLocaleString()}`;
  document.getElementById("modal-fault-title").textContent = diag.fault_identified;
  document.getElementById("modal-iso-eval").textContent = diag.iso_compliance;
  document.getElementById("modal-root-cause").textContent = diag.root_cause_analysis;
  document.getElementById("modal-rul").textContent = diag.estimated_rul;
  document.getElementById("modal-model-used").textContent = diag.llm_model_used;

  // Severity styling
  const sevBadge = document.getElementById("modal-severity-badge");
  const sevIcon = document.getElementById("modal-severity-icon");
  sevBadge.textContent = diag.severity;

  if (diag.severity === "CRITICAL") {
    sevBadge.className = "px-2 py-0.5 text-xs rounded font-bold bg-red-950 text-red-300 border border-red-700";
    sevIcon.className = "w-10 h-10 rounded-xl bg-red-950/80 border border-red-700 flex items-center justify-center text-red-400";
    sevIcon.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i>`;
  } else if (diag.severity === "WARNING") {
    sevBadge.className = "px-2 py-0.5 text-xs rounded font-bold bg-amber-950 text-amber-300 border border-amber-700";
    sevIcon.className = "w-10 h-10 rounded-xl bg-amber-950/80 border border-amber-700 flex items-center justify-center text-amber-400";
    sevIcon.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i>`;
  } else {
    sevBadge.className = "px-2 py-0.5 text-xs rounded font-bold bg-emerald-950 text-emerald-300 border border-emerald-700";
    sevIcon.className = "w-10 h-10 rounded-xl bg-emerald-950/80 border border-emerald-700 flex items-center justify-center text-emerald-400";
    sevIcon.innerHTML = `<i class="fa-solid fa-check"></i>`;
  }

  // Prescribed Actions
  const actionsContainer = document.getElementById("modal-actions");
  actionsContainer.innerHTML = diag.prescribed_actions.map(a => `
    <div class="bg-slate-800/80 p-3 rounded-xl border border-slate-700/60 flex items-start space-x-3">
      <div class="w-6 h-6 rounded-full bg-cyan-950 border border-cyan-700 text-cyan-300 flex items-center justify-center font-mono font-bold text-xs shrink-0 mt-0.5">
        ${a.step}
      </div>
      <div class="flex-1">
        <div class="flex items-center justify-between mb-0.5">
          <span class="font-bold text-white">${a.action}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded font-mono ${a.urgency === 'IMMEDIATE' ? 'bg-red-950 text-red-400' : 'bg-slate-700 text-slate-300'}">${a.urgency}</span>
        </div>
        <span class="text-[11px] text-slate-400 block"><i class="fa-solid fa-user-gear mr-1"></i>Assigned: ${a.technician_role}</span>
      </div>
    </div>
  `).join("");

  // RAG Document References
  const refContainer = document.getElementById("modal-references");
  refContainer.innerHTML = diag.retrieved_references.map(r => `
    <div class="bg-slate-950/60 p-3 rounded-xl border border-slate-800 space-y-1">
      <div class="flex items-center justify-between">
        <span class="font-bold text-indigo-300 text-xs">${r.title}</span>
        <span class="text-[10px] font-mono text-cyan-400">Match: ${(r.similarity_score * 100).toFixed(1)}%</span>
      </div>
      <span class="text-[10px] text-slate-400 block font-semibold">Section: ${r.section}</span>
      <p class="text-[11px] text-slate-300 leading-snug line-clamp-3">${r.content}</p>
    </div>
  `).join("");
}

function closeDiagnosisModal() {
  document.getElementById("diagnosis-modal").classList.add("hidden");
}

// Chat Copilot
async function sendChatMessage(e) {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const msg = input.value.trim();
  if (!msg) return;

  const chatContainer = document.getElementById("chat-messages");
  
  // User bubble
  chatContainer.innerHTML += `
    <div class="flex items-start justify-end space-x-2">
      <div class="bg-cyan-600/90 text-white rounded-xl p-3 max-w-[85%]">
        <p>${escapeHtml(msg)}</p>
      </div>
    </div>
  `;
  input.value = "";
  chatContainer.scrollTop = chatContainer.scrollHeight;

  // Typing indicator
  const typingId = `typing-${Date.now()}`;
  chatContainer.innerHTML += `
    <div id="${typingId}" class="flex items-start space-x-2">
      <div class="w-6 h-6 rounded-full bg-cyan-700/50 text-cyan-300 flex items-center justify-center text-[10px] shrink-0 mt-0.5">AI</div>
      <div class="bg-slate-800/90 rounded-xl p-3 border border-slate-700 text-slate-400">
        <i class="fa-solid fa-spinner fa-spin mr-1"></i> Consulting knowledge base...
      </div>
    </div>
  `;
  chatContainer.scrollTop = chatContainer.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, device_id: currentChartDevice })
    });
    const data = await res.json();
    document.getElementById(typingId).remove();

    chatContainer.innerHTML += `
      <div class="flex items-start space-x-2">
        <div class="w-6 h-6 rounded-full bg-cyan-700/50 text-cyan-300 flex items-center justify-center text-[10px] shrink-0 mt-0.5">AI</div>
        <div class="bg-slate-800/90 rounded-xl p-3 border border-slate-700/60 text-slate-200 space-y-1.5 max-w-[90%] whitespace-pre-wrap leading-relaxed">
          ${formatMarkdown(data.reply)}
        </div>
      </div>
    `;
    chatContainer.scrollTop = chatContainer.scrollHeight;
  } catch (err) {
    document.getElementById(typingId).remove();
    chatContainer.innerHTML += `
      <div class="text-red-400 text-xs p-2">Failed to get response: ${err.message}</div>
    `;
  }
}

// Fault Injection
async function injectFault(deviceId, faultCode) {
  try {
    await fetch(`/api/simulator/inject?device_id=${deviceId}&fault_code=${faultCode}&severity=1.0`, {
      method: "POST"
    });
  } catch (e) {
    console.error("Injection error:", e);
  }
}

async function resetAllDevices() {
  const devs = ["MTR-101", "PUMP-204", "CMP-301", "FAN-402"];
  for (const d of devs) {
    await injectFault(d, "NORMAL");
  }
  document.getElementById("alert-banner-container").classList.add("hidden");
}

// Remote Modal & QR
function openRemoteModal() {
  document.getElementById("remote-modal").classList.remove("hidden");
  fetchRemoteStatus();
}

function closeRemoteModal() {
  document.getElementById("remote-modal").classList.add("hidden");
}

function renderQrCode(url) {
  const qrElem = document.getElementById("qrcode");
  qrElem.innerHTML = "";
  if (window.QRCode) {
    new QRCode(qrElem, {
      text: url,
      width: 160,
      height: 160,
      colorDark: "#0b0f17",
      colorLight: "#ffffff",
      correctLevel: QRCode.CorrectLevel.M
    });
  }
}

function copyPublicUrl() {
  const input = document.getElementById("public-url-input");
  input.select();
  navigator.clipboard.writeText(input.value);
  alert("Public URL copied to clipboard! Open it from any phone or computer.");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatMarkdown(text) {
  // Simple markdown bold and bullet formatter for chat
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code class="bg-slate-900 px-1 py-0.5 rounded text-cyan-300 font-mono text-[11px]">$1</code>');
}
