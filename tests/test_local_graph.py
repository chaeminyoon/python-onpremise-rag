import unittest
import requests
from src.features.graph.extractor import GraphExtractor
from src.config import Config

class TestLocalGraph(unittest.TestCase):
    def setUp(self):
        self.extractor = GraphExtractor()
        # Check if Ollama is running
        try:
            response = requests.get(Config.OLLAMA_BASE_URL)
            self.ollama_available = (response.status_code == 200)
        except:
            self.ollama_available = False
            print("Warning: Ollama is not reachable. Skipping LLM tests.")

    def test_ollama_extraction(self):
        if not self.ollama_available:
            self.skipTest("Ollama server not running")
        
        text = "Samsung Electronics announced a 15% increase in annual revenue for 2024."
        concepts = self.extractor.extract_concepts(text)
        
        print(f"Extracted Concepts: {concepts}")
        self.assertTrue(len(concepts) > 0)
        self.assertTrue(any("Samsung" in c for c in concepts))

if __name__ == '__main__':
    unittest.main()
