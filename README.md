# Knowledge Driven IoT Fault Diagnosis Assistant (P_311)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![MQTT](https://img.shields.io/badge/MQTT-paho--mqtt-red.svg)](https://mqtt.org/)
[![RAG](https://img.shields.io/badge/RAG-Hybrid%20Vector%20Store-purple.svg)](https://github.com)
[![LLM](https://img.shields.io/badge/LLM-Gemini%20%7C%20OpenAI%20%7C%20Ollama-orange.svg)](https://ai.google.dev)
[![Status](https://img.shields.io/badge/Access-24%2F7%20Any%20Device-success.svg)](https://trycloudflare.com)

A production-grade, knowledge-driven industrial IoT condition monitoring and automated fault diagnosis system designed for continuous 24/7 remote operation from any device (smartphones, tablets, PCs) across cellular, Wi-Fi, and corporate networks.

---

## 📋 Project Identity
- **Project Name**: Knowledge driven IoT fault diagnosis assistant
- **Project ID**: `P_311`
- **Core Technologies**: Python, MQTT, Retrieval-Augmented Generation (RAG), Large Language Models (LLM), FastAPI, WebSockets.

---

## 🏛️ System Architecture

```
                          ┌───────────────────────────┐
                          │   Physical / Simulated    │
                          │     IoT Equipment         │
                          │ (Motors, Pumps, Compress) │
                          └─────────────┬─────────────┘
                                        │ Telemetry (RMS, Peak, Temp, Current)
                                        ▼
                          ┌───────────────────────────┐
                          │   MQTT Broker (Pub/Sub)   │
                          │   (broker.emqx.io / Mosq) │
                          └─────────────┬─────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
┌─────────────────────────┐                             ┌─────────────────────────┐
│ Automated Anomaly &     │                             │  RAG Knowledge Store    │
│ ISO 10816 Classifier    │                             │  - ISO 10816 Severity   │
│ - Zone A / B / C / D    │                             │  - Motor Bearing FMEA   │
└────────────┬────────────┘                             │  - Pump Cavitation      │
             │                                          │  - Safety LOTO Rules    │
             │ Anomaly Signature                        └────────────┬────────────┘
             │                                                       │ Top-K Chunks
             └──────────────────────────┬────────────────────────────┘
                                        ▼
                         ┌─────────────────────────────┐
                         │   LLM Diagnostic Engine     │
                         │ (Gemini / OpenAI / Fallback)│
                         └──────────────┬──────────────┘
                                        │ Structured Diagnosis & Root Cause
                                        ▼
                         ┌─────────────────────────────┐
                         │   FastAPI WebSocket Hub     │
                         └──────────────┬──────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
┌─────────────────────────┐                             ┌─────────────────────────┐
│ Local LAN Dashboard     │                             │ 24/7 Universal Remote   │
│ (http://localhost:8000) │                             │ Cloudflare Quick Tunnel │
│ (http://192.168.x.x)    │                             │ (https://*.trycloudflare)
└─────────────────────────┘                             └─────────────────────────┘
```

---

## ✨ Key Features

1. **Real-Time MQTT Telemetry Processing**:
   - Pub/Sub ingestion across `iot/p311/telemetry/#` and `iot/p311/alerts/#`.
   - Continuous streaming of Vibration RMS ($mm/s$), Peak Acceleration ($g$), Casing Temperature ($^\circ C$), Phase Current ($A$), and Hydraulic Pressure ($Bar$).
   - Built-in multi-device industrial simulator (`MTR-101`, `PUMP-204`, `CMP-301`, `FAN-402`).

2. **Knowledge-Driven RAG Engine**:
   - Curated industrial engineering knowledge base:
     - ISO 10816-3 Vibration Severity classification.
     - Induction motor bearing defect catalog (BPFO, BPFI, BSF, FTF).
     - Centrifugal pump cavitation and seal failure modes.
     - Rotary screw compressor overheating guidelines.
     - Plant safety, OSHA Lockout/Tagout (LOTO), and FMEA troubleshooting trees.
   - Hybrid N-Gram TF-IDF & Cosine Similarity vector store backed by SQLite for ultra-fast, zero-overhead retrieval on any device.

3. **Multi-Provider LLM Diagnostic Engine**:
   - Primary support for **Google Gemini** (`gemini-1.5-flash`, `gemini-2.0-flash`).
   - Support for **OpenAI** (`gpt-4o-mini`, `gpt-4o`), **Groq**, and **Local Ollama** (`llama3.2`).
   - Built-in **Deterministic Expert Synthesizer**: runs 100% offline out-of-the-box without requiring any API key or internet access for initial testing.

4. **24/7 Access from ANY Device on ANY Network**:
   - **Zero-Config Cloudflare Tunnel**: Generates a public HTTPS link (`https://xxxx.trycloudflare.com`) on startup.
   - **QR Code on Dashboard**: Point your smartphone camera at the screen to immediately open the live dashboard over 4G/5G mobile data!
   - **Docker & Docker Compose**: 1-command containerized deployment for VPS, AWS EC2, or DigitalOcean.
   - **Cloud PaaS**: Pre-configured `render.yaml` and `Procfile` for 1-click cloud hosting on Render or Railway.

---

## 🚀 Quick Start Guide

### Option 1: Native Windows / Linux Setup

1. **Navigate to the project directory**:
   ```bash
   cd P_311_IoT_Fault_Diagnosis_Assistant
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment (Optional)**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Add your `GEMINI_API_KEY` (optional; if left blank, the assistant automatically uses the built-in Expert Knowledge Engine).

4. **Start the Assistant**:
   - **Windows**: Double-click `start_assistant.bat` or run:
     ```bash
     python main.py
     ```
   - **Linux / macOS**:
     ```bash
     python3 main.py
     ```

5. **Open Dashboard**:
   - Local: [http://localhost:8000](http://localhost:8000)
   - On the same Wi-Fi: `http://<your-local-ip>:8000`
   - From any phone/cellular device: Check the terminal output or click **24/7 Global Access** on the dashboard for your public HTTPS link and QR code!

---

### Option 2: Docker & Docker Compose

Run full stack (Assistant + optional Mosquitto MQTT broker):
```bash
docker-compose up -d
```
Stop services:
```bash
docker-compose down
```

---

## 🧪 Running Automated Tests

Run the complete 15-test unit & integration test suite:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📡 MQTT Topic Specification

| Topic | Purpose | Payload Example |
| :--- | :--- | :--- |
| `iot/p311/telemetry/{device_id}` | Real-time sensor metrics | `{"device_id":"MTR-101", "vibration_rms":1.2, "temperature":52.0, "current_draw":18.5}` |
| `iot/p311/alerts/{device_id}` | Automatic threshold alerts | `{"device_id":"PUMP-204", "severity":"CRITICAL", "fault_code":"E305_PUMP_CAVITATION"}` |
| `iot/p311/commands/{device_id}` | Remote actuation & reset | `{"command":"RESET_FAULT"}` |

---

## 🔌 REST API Endpoints

- `GET /`: Interactive SCADA Web Dashboard.
- `GET /api/info`: Project identity and system status.
- `GET /api/devices`: Status of all monitored IoT devices.
- `GET /api/telemetry/history`: Time-series sensor logs from SQLite database.
- `POST /api/diagnose`: Perform RAG + LLM fault diagnosis on a machine.
- `POST /api/chat`: AI Diagnostics Copilot conversation endpoint.
- `POST /api/simulator/inject`: Inject synthetic faults (`E101_BEARING_DEGRADATION`, `E305_PUMP_CAVITATION`, etc.).
- `POST /api/knowledge/upload`: Ingest new manuals and maintenance documents dynamically into vector memory.
- `GET /api/tunnel/status`: Cloudflare public HTTPS URL and QR code link.
- `WebSocket /ws/live`: Real-time duplex event streaming for telemetry and alerts.

---

## 🔒 Plant Safety & Standards Compliance
- **ISO 10816-3**: Mechanical vibration evaluation of industrial machines.
- **OSHA 29 CFR 1910.147**: Mandatory Lockout / Tagout (LOTO) protocols for electrical and mechanical isolation.
- **API 682**: Mechanical seal piping flush plan recommendations.
