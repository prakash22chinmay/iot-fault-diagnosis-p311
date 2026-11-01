"""
Streamlit Application for Project P_311: Knowledge driven IoT fault diagnosis assistant.
Supports 24/7 deployment on Streamlit Community Cloud (share.streamlit.io).
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.models.telemetry import TelemetryData
from app.models.diagnosis import DiagnosisRequest
from app.mqtt.simulator import iot_simulator
from app.mqtt.client import mqtt_manager
from app.rag.store import vector_store
from app.llm.diagnosis_engine import diagnostic_engine

# --- Page Config ---
st.set_page_config(
    page_title="P_311: IoT Fault Diagnosis Assistant",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Background Services Initialization (Cached) ---
@st.cache_resource
def init_backend_services():
    """Start MQTT manager, Simulator, and index RAG vector base."""
    # Ensure vector store is loaded
    if not vector_store.chunks:
        vector_store.load_and_index()
    # Start MQTT loop if not running
    mqtt_manager.start()
    # Start telemetry simulator
    iot_simulator.start()
    return True

init_backend_services()

# --- Custom CSS for Industrial Dashboard Aesthetic ---
st.markdown("""
<style>
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 0px;
    }
    .badge-p311 {
        background-color: #083344;
        color: #22d3ee;
        border: 1px solid #0891b2;
        padding: 2px 8px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .badge-rag {
        background-color: #3b0764;
        color: #d8b4fe;
        border: 1px solid #9333ea;
        padding: 2px 8px;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #121826;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .status-healthy { color: #34d399; font-weight: bold; }
    .status-warning { color: #fbbf24; font-weight: bold; }
    .status-critical { color: #f87171; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- Top Header ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 2rem;">⚙️</span>
        <div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span class="main-title">Knowledge Driven IoT Fault Diagnosis Assistant</span>
                <span class="badge-p311">P_311</span>
                <span class="badge-rag">RAG + LLM</span>
            </div>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 2px;">
                24/7 Universal Remote Condition Monitoring & Root-Cause Remediation
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_h2:
    st.markdown(f"""
    <div style="text-align: right; font-size: 0.8rem; color: #94a3b8; padding-top: 8px;">
        <div>📡 MQTT: <code style="color: #34d399;">{settings.MQTT_BROKER_HOST}</code></div>
        <div>🧠 Knowledge: <code style="color: #22d3ee;">{len(vector_store.chunks)} Chunks Indexed</code></div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# --- Sidebar Controls ---
st.sidebar.image("https://img.icons8.com/fluency/96/processor.png", width=64)
st.sidebar.title("Configuration & Controls")

# LLM Provider selection
provider_choice = st.sidebar.selectbox(
    "🤖 LLM Diagnostic Provider",
    options=["gemini", "openai", "expert_fallback"],
    format_func=lambda x: {
        "gemini": "Google Gemini (Recommended)",
        "openai": "OpenAI GPT-4o-mini",
        "expert_fallback": "Expert Knowledge RAG Synthesizer (Offline/Zero Setup)"
    }.get(x, x),
    index=0
)
settings.LLM_PROVIDER = provider_choice

# API Key input
if provider_choice == "gemini":
    gemini_key = st.sidebar.text_input(
        "Gemini API Key",
        value=settings.GEMINI_API_KEY,
        type="password",
        help="Enter your Google Gemini API Key or leave empty to use expert synthesis fallback."
    )
    if gemini_key:
        settings.GEMINI_API_KEY = gemini_key
        diagnostic_engine.gemini_key = gemini_key

elif provider_choice == "openai":
    openai_key = st.sidebar.text_input(
        "OpenAI API Key",
        value=settings.OPENAI_API_KEY,
        type="password"
    )
    if openai_key:
        settings.OPENAI_API_KEY = openai_key
        diagnostic_engine.openai_key = openai_key

st.sidebar.markdown("---")

# Refresh Control
auto_refresh = st.sidebar.checkbox("🔄 Live Telemetry Stream", value=True)
if auto_refresh:
    refresh_sec = st.sidebar.slider("Refresh interval (seconds)", min_value=2, max_value=10, value=3)
    # Streamlit rerun mechanism
    import time
    time.sleep(0.01)

# Navigation tabs
tab_dash, tab_diag, tab_chat, tab_inject, tab_kb, tab_deploy = st.tabs([
    "📊 Fleet Telemetry Dashboard",
    "🔬 Knowledge-Driven Diagnosis",
    "💬 AI Copilot Chat",
    "🧪 Fault Injection Lab",
    "📚 RAG Knowledge Base",
    "🌐 24/7 Cloud Deployment"
])

# --- Helper: Generate or Get Latest Device Telemetry ---
def get_fleet_telemetry():
    fleet = {}
    for dev_id, dev_cfg in iot_simulator.devices.items():
        # Generate tick if not in latest_devices
        if dev_id not in mqtt_manager.latest_devices:
            raw = iot_simulator._generate_telemetry(dev_cfg)
            mqtt_manager._handle_telemetry(raw)
        fleet[dev_id] = mqtt_manager.latest_devices[dev_id]
    return fleet

# ==============================================================================
# TAB 1: FLEET TELEMETRY DASHBOARD
# ==============================================================================
with tab_dash:
    fleet = get_fleet_telemetry()
    
    st.subheader("Monitored Equipment Fleet")
    cols = st.columns(len(fleet))

    for idx, (dev_id, t) in enumerate(fleet.items()):
        with cols[idx]:
            # Status badge
            if t.iso_zone == "Zone D" or t.temperature > 85:
                status_color = "status-critical"
                status_text = "CRITICAL"
                card_border = "#ef4444"
            elif t.iso_zone == "Zone C" or t.temperature > 70 or t.fault_code != "NORMAL":
                status_color = "status-warning"
                status_text = "WARNING"
                card_border = "#f59e0b"
            else:
                status_color = "status-healthy"
                status_text = "HEALTHY"
                card_border = "#10b981"

            st.markdown(f"""
            <div class="metric-card" style="border-left: 4px solid {card_border};">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <strong style="font-size: 1.1rem; color: #fff;">{t.device_id}</strong><br>
                        <span style="font-size: 0.75rem; color: #94a3b8;">{t.device_type}</span>
                    </div>
                    <span class="{status_color}">{status_text}</span>
                </div>
                <hr style="border-color: rgba(255,255,255,0.08); margin: 8px 0;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                    <span>Health Score:</span>
                    <strong style="color: {'#34d399' if t.health_index > 70 else '#f87171'};">{t.health_index}%</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                    <span>ISO 10816:</span>
                    <strong style="color: #38bdf8;">{t.iso_zone}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                    <span>Vibration RMS:</span>
                    <strong>{t.vibration_rms} mm/s</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                    <span>Peak Accel:</span>
                    <strong>{t.vibration_peak} g</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                    <span>Temperature:</span>
                    <strong>{t.temperature} °C</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem;">
                    <span>Current:</span>
                    <strong>{t.current_draw} A</strong>
                </div>
                <div style="margin-top: 6px; font-size: 0.75rem; color: #cbd5e1;">
                    Fault: <code style="color: #f59e0b;">{t.fault_code}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Diagnose {dev_id}", key=f"diag_btn_{dev_id}", use_container_width=True):
                st.session_state["target_diag_device"] = dev_id
                st.session_state["trigger_diag"] = True

    # Real-Time Telemetry Trends
    st.markdown("### 📈 Live Vibration Velocity Trend (ISO 10816-3)")
    sel_chart_dev = st.selectbox("Select Machine for Trend Graph", list(fleet.keys()), index=0)
    
    # Fetch historical readings from DB
    import sqlite3
    from app.config import DB_PATH
    history_records = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT timestamp, vibration_rms, vibration_peak, temperature, current_draw 
                FROM telemetry_logs 
                WHERE device_id = ? 
                ORDER BY id DESC LIMIT 25
            """, (sel_chart_dev,))
            history_records = [dict(r) for r in cur.fetchall()][::-1]
    except Exception as e:
        pass

    if history_records:
        df = pd.DataFrame(history_records)
        df["time"] = pd.to_datetime(df["timestamp"]).dt.strftime("%H:%M:%S")
        chart_df = df.set_index("time")[["vibration_rms", "vibration_peak"]]
        st.line_chart(chart_df, color=["#06b6d4", "#f59e0b"])
        st.caption("ISO 10816 Thresholds: Zone A (<1.4 mm/s) | Zone B (1.4 - 2.8 mm/s) | Zone C (2.8 - 4.5 mm/s) | Zone D (>4.5 mm/s)")
    else:
        st.info("Generating telemetry history... Readings will appear after a few seconds.")

# ==============================================================================
# TAB 2: KNOWLEDGE-DRIVEN DIAGNOSIS
# ==============================================================================
with tab_diag:
    st.subheader("🔬 Automated Root-Cause Fault Diagnosis")
    st.write("Combines live IoT sensor readings with the indexed RAG industrial engineering knowledge base.")

    diag_col1, diag_col2 = st.columns([1, 2])
    
    with diag_col1:
        target_device = st.selectbox(
            "Select IoT Equipment to Diagnose",
            options=list(fleet.keys()),
            index=list(fleet.keys()).index(st.session_state.get("target_diag_device", "MTR-101"))
        )
        symptom_notes = st.text_area(
            "Field Engineer Notes / Observed Symptoms (Optional)",
            placeholder="e.g. Unusual metallic rattling, high casing heat, cavitation sound..."
        )
        run_btn = st.button("Run AI Diagnosis", type="primary", use_container_width=True)

    with diag_col2:
        if run_btn or st.session_state.get("trigger_diag", False):
            st.session_state["trigger_diag"] = False
            active_t = fleet.get(target_device)

            with st.spinner(f"Querying RAG Vector Base and invoking {settings.LLM_PROVIDER.upper()}..."):
                req = DiagnosisRequest(device_id=target_device, symptom_description=symptom_notes)
                diag_res = asyncio.run(diagnostic_engine.diagnose(req, latest_telemetry=active_t))

            # Display Diagnosis Card
            sev_color = "#10b981" if diag_res.severity == "HEALTHY" else ("#f59e0b" if diag_res.severity == "WARNING" else "#ef4444")
            st.markdown(f"""
            <div style="background-color: #121826; border-left: 5px solid {sev_color}; padding: 16px; border-radius: 12px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #fff;">{diag_res.device_id}: {diag_res.fault_identified}</h3>
                    <span style="background-color: {sev_color}33; color: {sev_color}; border: 1px solid {sev_color}; padding: 3px 10px; border-radius: 6px; font-weight: bold; font-size: 0.85rem;">
                        {diag_res.severity}
                    </span>
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">
                    ID: <code>{diag_res.diagnosis_id}</code> | ISO Compliance: <strong style="color: #38bdf8;">{diag_res.iso_compliance}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 🔍 Root-Cause Analysis")
            st.write(diag_res.root_cause_analysis)

            st.markdown("#### 🛠️ Prescribed Remediation Actions")
            for action in diag_res.prescribed_actions:
                st.markdown(f"""
                - **Step {action.step}:** {action.action}  
                  *(Urgency: `{action.urgency}` | Assigned to: `{action.technician_role}`)*
                """)

            st.markdown("#### 📚 Retrieved RAG Technical Manual References")
            for ref in diag_res.retrieved_references:
                with st.expander(f"📄 {ref.title} — {ref.section} (Similarity: {ref.similarity_score * 100:.1f}%)"):
                    st.markdown(ref.content)

            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #94a3b8; margin-top: 16px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px;">
                <span>⏳ Estimated Remaining Useful Life (RUL): <strong style="color: #fbbf24;">{diag_res.estimated_rul}</strong></span>
                <span>🤖 Diagnostics Engine: <strong style="color: #22d3ee;">{diag_res.llm_model_used}</strong></span>
            </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# TAB 3: AI COPILOT CHAT
# ==============================================================================
with tab_chat:
    st.subheader("💬 Industrial AI Diagnostics Copilot")
    st.caption("Ask natural language questions about machines, ISO 10816 limits, bearing vibration, or troubleshooting protocols.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I am your Knowledge-Driven IoT Diagnostics Copilot (Project P_311). How can I assist you with machinery health, vibration standards, or fault resolution today?"}
        ]

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Ask a question (e.g. 'What causes cavitation in centrifugal pumps?')...")
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Searching RAG manuals & synthesizing response..."):
                reply = asyncio.run(diagnostic_engine.chat(user_query))
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ==============================================================================
# TAB 4: FAULT INJECTION LAB
# ==============================================================================
with tab_inject:
    st.subheader("🧪 Interactive IoT Fault Injection Lab")
    st.write("Simulate real-world industrial failure modes on fleet machines to observe real-time MQTT telemetry shifts, threshold alarms, and RAG diagnosis responses.")

    inj_c1, inj_c2, inj_c3 = st.columns(3)

    with inj_c1:
        st.markdown("### 🛞 Motor Bearing Failure")
        st.caption("Triggers high-frequency peak acceleration spikes (BPFO/BPFI) and bearing temperature rise.")
        if st.button("Inject Bearing Degradation (MTR-101)", use_container_width=True):
            iot_simulator.inject_fault("MTR-101", "E101_BEARING_DEGRADATION", severity=1.0)
            st.success("Injected E101_BEARING_DEGRADATION into MTR-101!")

        st.markdown("### 🌪️ Centrifugal Cavitation")
        st.caption("Simulates low NPSH causing vapor bubble collapse, high-frequency vibration, and severe pressure drop.")
        if st.button("Inject Cavitation (PUMP-204)", use_container_width=True):
            iot_simulator.inject_fault("PUMP-204", "E305_PUMP_CAVITATION", severity=1.0)
            st.success("Injected E305_PUMP_CAVITATION into PUMP-204!")

    with inj_c2:
        st.markdown("### 🔥 Stator Thermal Overheat")
        st.caption("Simulates clogged fan cowl shroud with temperature >95°C and current rise above FLA.")
        if st.button("Inject Stator Overheat (MTR-101)", use_container_width=True):
            iot_simulator.inject_fault("MTR-101", "E204_MOTOR_OVERHEAT", severity=1.0)
            st.success("Injected E204_MOTOR_OVERHEAT into MTR-101!")

        st.markdown("### ⚖️ Rotor Unbalance")
        st.caption("1X harmonic mass imbalance pushing vibration velocity into ISO Zone D.")
        if st.button("Inject Rotor Unbalance (FAN-402)", use_container_width=True):
            iot_simulator.inject_fault("FAN-402", "E401_ROTOR_UNBALANCE", severity=1.0)
            st.success("Injected E401_ROTOR_UNBALANCE into FAN-402!")

    with inj_c3:
        st.markdown("### ⚡ 3-Phase Current Imbalance")
        st.caption("Simulates high-resistance terminal lug causing phase imbalance >5%.")
        if st.button("Inject Phase Imbalance (CMP-301)", use_container_width=True):
            iot_simulator.inject_fault("CMP-301", "E502_PHASE_IMBALANCE", severity=1.0)
            st.success("Injected E502_PHASE_IMBALANCE into CMP-301!")

        st.markdown("### 🔄 Normal Restoration")
        st.caption("Resets all fleet machines to healthy baseline operation.")
        if st.button("Restore All to Normal", type="primary", use_container_width=True):
            for d in ["MTR-101", "PUMP-204", "CMP-301", "FAN-402"]:
                iot_simulator.inject_fault(d, "NORMAL", severity=0.0)
            st.success("All machines restored to healthy operating baseline!")

# ==============================================================================
# TAB 5: RAG KNOWLEDGE BASE
# ==============================================================================
with tab_kb:
    st.subheader("📚 Industrial Equipment Knowledge Base")
    st.caption("Explore technical manuals, ISO standards, and troubleshooting procedures indexed in the vector store.")

    kb_query = st.text_input("Search knowledge documents...", value="ISO 10816 vibration limits")
    if kb_query:
        matches = vector_store.search(kb_query, top_k=5)
        for m in matches:
            with st.expander(f"{m.title} — {m.section} (Category: {m.category} | Score: {m.similarity_score * 100:.1f}%)"):
                st.markdown(m.content)

    st.markdown("---")
    st.subheader("📤 Ingest New Manual / Document")
    uploaded_file = st.file_uploader("Upload technical manual (.md or .txt)", type=["md", "txt"])
    if uploaded_file is not None:
        content_str = uploaded_file.read().decode("utf-8", errors="ignore")
        if st.button("Index into Vector Store"):
            total_chunks = vector_store.add_document(uploaded_file.name, content_str)
            st.success(f"Indexed {uploaded_file.name} successfully! Total chunks in memory: {total_chunks}")

# ==============================================================================
# TAB 6: 24/7 CLOUD DEPLOYMENT
# ==============================================================================
with tab_deploy:
    st.subheader("🌐 Deploying 24/7 on Streamlit Community Cloud")
    st.markdown("""
    You can host this assistant for **FREE 24/7 with zero server costs** on **Streamlit Community Cloud** ([share.streamlit.io](https://share.streamlit.io)):

    ### 3-Step 24/7 Deployment:

    1. **Push this code to GitHub**:
       ```bash
       git init
       git add .
       git commit -m "Initial commit for P_311 IoT Fault Diagnosis Assistant"
       git branch -M main
       git remote add origin https://github.com/<your-username>/<your-repo-name>.git
       git push -u origin main
       ```

    2. **Connect to Streamlit Cloud**:
       - Go to [share.streamlit.io](https://share.streamlit.io) and log in with GitHub.
       - Click **"New app"**.
       - Select your repository and branch (`main`).
       - Set **Main file path** to: `streamlit_app.py`.

    3. **Set Secrets (Optional)**:
       Under **Advanced Settings > Secrets**, you can add your API keys:
       ```toml
       GEMINI_API_KEY = "your-gemini-api-key"
       MQTT_BROKER_HOST = "broker.emqx.io"
       MQTT_BROKER_PORT = 1883
       ```
       Click **Deploy!**

    Your app will be live 24/7 at a permanent URL like:
    `https://iot-fault-diagnosis-p311.streamlit.app` accessible from any smartphone, tablet, or PC worldwide!
    """)
