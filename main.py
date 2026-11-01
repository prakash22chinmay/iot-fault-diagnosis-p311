"""
Main Entrypoint for Project P_311: Knowledge driven IoT fault diagnosis assistant.
"""
import sys
import uvicorn
from app.config import settings
from app.rag.store import vector_store


def main():
    print("=" * 75)
    print(f"🚀 Project Name: {settings.PROJECT_NAME}")
    print(f"🆔 Project ID:   {settings.PROJECT_ID}")
    print(f"📡 MQTT Broker:  {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
    print(f"🧠 RAG Engine:   Hybrid TF-IDF & Cosine Similarity ({len(vector_store.chunks)} chunks indexed)")
    print(f"🤖 LLM Provider: {settings.LLM_PROVIDER}")
    print(f"🌐 Local Server: http://{settings.HOST}:{settings.PORT} (or http://localhost:{settings.PORT})")
    print(f"📱 24/7 Remote:  Auto Cloudflare Quick Tunnel enabled ({settings.ENABLE_PUBLIC_TUNNEL})")
    print("=" * 75)

    uvicorn.run(
        "app.api.app:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=False
    )


if __name__ == "__main__":
    main()
