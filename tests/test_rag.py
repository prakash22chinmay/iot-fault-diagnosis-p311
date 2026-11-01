"""
Unit tests for RAG Vector Store and Knowledge Retrieval.
"""
import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.store import vector_store


class TestRAGStore(unittest.TestCase):
    def test_knowledge_base_indexing(self):
        self.assertGreater(len(vector_store.chunks), 0, "Knowledge base should have indexed chunks")

    def test_bearing_fault_retrieval(self):
        results = vector_store.search("bearing raceway degradation peak acceleration", top_k=3)
        self.assertGreater(len(results), 0, "Should return matching chunks for bearing search")
        contents = " ".join([r.content.lower() + " " + r.title.lower() for r in results])
        self.assertIn("bearing", contents)

    def test_pump_cavitation_retrieval(self):
        results = vector_store.search("centrifugal pump cavitation NPSH suction pressure drop", top_k=3)
        self.assertGreater(len(results), 0)
        contents = " ".join([r.content.lower() for r in results])
        self.assertIn("cavitation", contents)

    def test_iso_10816_retrieval(self):
        results = vector_store.search("ISO 10816-3 vibration severity Zone D Zone C limits", top_k=3)
        self.assertGreater(len(results), 0)
        contents = " ".join([r.content.lower() for r in results])
        self.assertTrue("iso 10816" in contents or "zone" in contents)


if __name__ == "__main__":
    unittest.main()
