"""
FastAPI application for Project P_311: Knowledge driven IoT fault diagnosis assistant.
Exposes RESTful endpoints, WebSockets, and serves responsive web dashboard.
"""
import asyncio
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings, DB_PATH, BASE_DIR
from app.models.telemetry import TelemetryData, DeviceSummary
from app.models.diagnosis import DiagnosisRequest, DiagnosisResponse, ChatRequest
from app.mqtt.client import mqtt_manager
from app.mqtt.simulator import iot_simulator
from app.rag.store import vector_store
from app.llm.diagnosis_engine import diagnostic_engine
from app.remote.tunnel import remote_tunnel


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="24/7 Real-Time Knowledge-Driven IoT Machine Fault Diagnosis Assistant (Project ID: P_311)",
    version=settings.VERSION
)

# Enable CORS for universal device access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Connected WebSocket clients
active_websockets: List[WebSocket] = []


def ws_broadcast(msg: dict):
    """Synchronous bridge to broadcast WebSocket messages to all active clients."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(_broadcast_to_websockets(msg))


async def _broadcast_to_websockets(msg: dict):
    disconnected = []
    text = json.dumps(msg)
    for ws in active_websockets:
        try:
            await ws.send_text(text)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in active_websockets:
            active_websockets.remove(ws)


@app.on_event("startup")
async def startup_event():
    print(f"[{settings.PROJECT_ID}] Initializing {settings.PROJECT_NAME}...")
    
    # Configure WebSocket broadcaster in MQTT manager
    mqtt_manager.set_ws_callback(ws_broadcast)
    
    # Start MQTT client
    mqtt_manager.start()
    
    # Start IoT Telemetry Simulator
    iot_simulator.start()
    
    # Start 24/7 Cloudflare Remote Access Tunnel
    if settings.ENABLE_PUBLIC_TUNNEL:
        remote_tunnel.start_tunnel(port=settings.PORT)


@app.on_event("shutdown")
async def shutdown_event():
    print(f"[{settings.PROJECT_ID}] Shutting down...")
    iot_simulator.stop()
    mqtt_manager.stop()
    remote_tunnel.stop_tunnel()


# --- Web UI Endpoint ---

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = BASE_DIR / "templates" / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>Dashboard template not found.</h2>")


# --- REST Endpoints ---

@app.get("/api/info")
async def get_project_info():
    return {
        "project_id": settings.PROJECT_ID,
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "mqtt_broker": f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}",
        "indexed_knowledge_chunks": len(vector_store.chunks),
        "remote_access": remote_tunnel.get_info()
    }


@app.get("/api/devices")
async def list_devices():
    """List all monitored IoT devices and their current health status."""
    devices = []
    for dev_id, dev_cfg in iot_simulator.devices.items():
        latest = mqtt_manager.latest_devices.get(dev_id)
        status = "HEALTHY"
        if latest:
            if latest.iso_zone == "Zone D" or latest.temperature > 85:
                status = "CRITICAL"
            elif latest.iso_zone == "Zone C" or latest.temperature > 70 or latest.fault_code != "NORMAL":
                status = "WARNING"
        
        devices.append({
            "device_id": dev_id,
            "device_type": dev_cfg["device_type"],
            "status": status,
            "latest_telemetry": latest.model_dump() if latest else None,
            "fault_mode": dev_cfg["fault_mode"],
            "fault_severity": dev_cfg["fault_severity"]
        })
    return devices


@app.get("/api/telemetry/history")
async def get_telemetry_history(device_id: Optional[str] = None, limit: int = 50):
    """Retrieve historical telemetry logs from SQLite."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if device_id:
            cursor.execute("""
                SELECT * FROM telemetry_logs 
                WHERE device_id = ? 
                ORDER BY id DESC LIMIT ?
            """, (device_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM telemetry_logs 
                ORDER BY id DESC LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        
    return [dict(row) for row in rows][::-1]


@app.get("/api/alerts")
async def get_alerts():
    return mqtt_manager.active_alerts


@app.post("/api/diagnose", response_model=DiagnosisResponse)
async def diagnose_machine(request: DiagnosisRequest):
    """Run RAG + LLM Root-Cause Fault Diagnosis on an IoT machine."""
    latest = mqtt_manager.latest_devices.get(request.device_id)
    diagnosis = await diagnostic_engine.diagnose(request, latest_telemetry=latest)
    return diagnosis


@app.post("/api/chat")
async def chat_copilot(req: ChatRequest):
    """Field Engineer AI Chat Copilot with RAG manual access."""
    latest = mqtt_manager.latest_devices.get(req.device_id) if req.device_id else None
    response_text = await diagnostic_engine.chat(req.message, req.device_id, latest)
    return {"reply": response_text}


@app.post("/api/simulator/inject")
async def inject_fault(device_id: str, fault_code: str, severity: float = 1.0):
    """Inject a physical fault into an IoT device."""
    success = iot_simulator.inject_fault(device_id, fault_code, severity)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"status": "ok", "device_id": device_id, "fault_code": fault_code, "severity": severity}


@app.get("/api/knowledge/search")
async def search_knowledge(q: str, limit: int = 4):
    chunks = vector_store.search(q, top_k=limit)
    return [c.model_dump() for c in chunks]


@app.post("/api/knowledge/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload dynamic equipment manual / PDF / markdown document into RAG vector store."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    total = vector_store.add_document(file.filename, text)
    return {"filename": file.filename, "status": "indexed", "total_chunks": total}


@app.get("/api/tunnel/status")
async def get_tunnel_status():
    return remote_tunnel.get_info()


# --- WebSocket Endpoint for Live 24/7 Telemetry Streaming ---

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    
    # Send initial snapshot
    snapshot = {
        "type": "snapshot",
        "devices": [dev.model_dump() for dev in mqtt_manager.latest_devices.values()],
        "alerts": mqtt_manager.active_alerts[:10]
    }
    await websocket.send_text(json.dumps(snapshot))

    try:
        while True:
            # Keepalive / listen for client commands
            data = await websocket.receive_text()
            # Can process incoming client commands if needed
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
    except Exception:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
