"""
RAG Vector Store & Knowledge Base Indexer.
Provides hybrid semantic retrieval using TF-IDF + N-gram Cosine Similarity & SQLite storage.
Can also integrate with cloud embedding providers if API keys are configured.
"""
import os
import re
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import KNOWLEDGE_DIR, DB_PATH
from app.models.diagnosis import KnowledgeChunk


class KnowledgeVectorStore:
    def __init__(self, db_path: Path = DB_PATH, docs_dir: Path = KNOWLEDGE_DIR):
        self.db_path = db_path
        self.docs_dir = docs_dir
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.chunks: List[Dict[str, Any]] = []
        self._init_db()
        self.load_and_index()

    def _init_db(self):
        """Initialize SQLite database for chunks and documents."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id TEXT PRIMARY KEY,
                    doc_id TEXT,
                    title TEXT,
                    category TEXT,
                    section TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    device_type TEXT,
                    timestamp TEXT,
                    vibration_rms REAL,
                    vibration_peak REAL,
                    temperature REAL,
                    current_draw REAL,
                    pressure REAL,
                    flow_rate REAL,
                    fault_code TEXT,
                    health_index REAL,
                    iso_zone TEXT,
                    is_anomaly INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fault_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT,
                    severity TEXT,
                    fault_code TEXT,
                    message TEXT,
                    timestamp TEXT,
                    resolved INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def chunk_document(self, file_path: Path) -> List[Dict[str, Any]]:
        """Split markdown or text document into semantic section chunks."""
        text = file_path.read_text(encoding="utf-8")
        doc_id = file_path.stem
        lines = text.split("\n")
        
        doc_title = file_path.name
        if lines and lines[0].startswith("# "):
            doc_title = lines[0].replace("# ", "").strip()
            
        chunks = []
        current_section = "General Overview"
        current_buffer = []

        for line in lines:
            if line.startswith("## ") or line.startswith("### "):
                if current_buffer:
                    body = "\n".join(current_buffer).strip()
                    if len(body) > 30:
                        chunk_id = f"{doc_id}_{len(chunks)}"
                        content = f"### {current_section}\n\n{body}"
                        chunks.append({
                            "id": chunk_id,
                            "doc_id": doc_id,
                            "title": doc_title,
                            "category": self._infer_category(doc_id),
                            "section": current_section,
                            "content": content
                        })
                    current_buffer = []
                current_section = line.lstrip("#").strip()
            else:
                current_buffer.append(line)

        # Flush final chunk
        if current_buffer:
            body = "\n".join(current_buffer).strip()
            if len(body) > 30:
                chunk_id = f"{doc_id}_{len(chunks)}"
                content = f"### {current_section}\n\n{body}"
                chunks.append({
                    "id": chunk_id,
                    "doc_id": doc_id,
                    "title": doc_title,
                    "category": self._infer_category(doc_id),
                    "section": current_section,
                    "content": content
                })

        return chunks

    def _infer_category(self, doc_id: str) -> str:
        doc_lower = doc_id.lower()
        if "motor" in doc_lower:
            return "Motors"
        elif "pump" in doc_lower:
            return "Pumps"
        elif "compressor" in doc_lower:
            return "Compressors"
        elif "vibration" in doc_lower or "iso" in doc_lower:
            return "Vibration Standards"
        elif "safety" in doc_lower or "fmea" in doc_lower:
            return "Plant Safety & FMEA"
        return "Industrial Equipment"

    def load_and_index(self):
        """Load all documents from knowledge directory and build hybrid vector index."""
        all_chunks = []
        for file in self.docs_dir.glob("*.md"):
            try:
                chunks = self.chunk_document(file)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"[RAG] Error reading {file.name}: {e}")

        for file in self.docs_dir.glob("*.txt"):
            try:
                chunks = self.chunk_document(file)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"[RAG] Error reading {file.name}: {e}")

        # Update DB
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_chunks")
            for c in all_chunks:
                cursor.execute("""
                    INSERT INTO knowledge_chunks (id, doc_id, title, category, section, content)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (c["id"], c["doc_id"], c["title"], c["category"], c["section"], c["content"]))
            conn.commit()

        self.chunks = all_chunks

        if not self.chunks:
            return

        # Build TF-IDF + N-Gram Hybrid Vectorizer
        corpus = [f"{c['title']} {c['section']} {c['category']} {c['content']}" for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            stop_words="english",
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        print(f"[RAG Indexer] Indexed {len(self.chunks)} knowledge chunks from {self.docs_dir}")

    def search(self, query: str, top_k: int = 4, category_filter: Optional[str] = None) -> List[KnowledgeChunk]:
        """Perform semantic similarity search against knowledge chunks."""
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Sort indices descending
        ranked_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in ranked_indices:
            score = float(similarities[idx])
            chunk = self.chunks[idx]

            if category_filter and category_filter.lower() not in chunk["category"].lower():
                continue

            # Accept if score is positive or top matches
            if len(results) < top_k and (score > 0.05 or len(results) == 0):
                results.append(KnowledgeChunk(
                    doc_id=chunk["doc_id"],
                    title=chunk["title"],
                    category=chunk["category"],
                    section=chunk["section"],
                    content=chunk["content"],
                    similarity_score=round(score, 4)
                ))

        return results

    def add_document(self, filename: str, content: str) -> int:
        """Add a new document dynamically to the knowledge base and reindex."""
        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
        file_path = self.docs_dir / safe_name
        file_path.write_text(content, encoding="utf-8")
        self.load_and_index()
        return len(self.chunks)


# Global singleton instance
vector_store = KnowledgeVectorStore()
