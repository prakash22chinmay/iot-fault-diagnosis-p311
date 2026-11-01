"""
Configuration module for Project P_311: Knowledge driven IoT fault diagnosis assistant.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge_docs"
DB_PATH = DATA_DIR / "iot_diagnostics.db"

# Ensure data directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    # Project Identity
    PROJECT_ID: str = "P_311"
    PROJECT_NAME: str = "Knowledge driven IoT fault diagnosis assistant"
    VERSION: str = "1.0.0"

    # Server Settings (0.0.0.0 allows LAN access)
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # MQTT Broker Configuration
    # Uses public reliable broker for immediate plug-and-play, or override with private broker
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "broker.emqx.io")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_KEEPALIVE: int = 60
    MQTT_USERNAME: str = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD: str = os.getenv("MQTT_PASSWORD", "")
    MQTT_CLIENT_ID: str = f"p311_iot_assistant_{os.getpid()}"
    
    # MQTT Topics
    TOPIC_TELEMETRY: str = "iot/p311/telemetry/#"
    TOPIC_TELEMETRY_PUB_PREFIX: str = "iot/p311/telemetry"
    TOPIC_ALERTS: str = "iot/p311/alerts/#"
    TOPIC_ALERTS_PUB_PREFIX: str = "iot/p311/alerts"
    TOPIC_COMMANDS: str = "iot/p311/commands/#"

    # LLM Settings
    # Providers supported: "gemini", "openai", "groq", "ollama", "expert_fallback"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    # RAG Settings
    RAG_TOP_K: int = 4
    RAG_SIMILARITY_THRESHOLD: float = 0.25

    # 24/7 Remote Access / Tunnel Settings
    ENABLE_PUBLIC_TUNNEL: bool = os.getenv("ENABLE_PUBLIC_TUNNEL", "true").lower() in ("true", "1", "yes")
    TUNNEL_PROVIDER: str = os.getenv("TUNNEL_PROVIDER", "cloudflare")  # "cloudflare" or "ngrok"
    NGROK_AUTHTOKEN: str = os.getenv("NGROK_AUTHTOKEN", "")

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
