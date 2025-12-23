import unittest
import os
import requests
from src.config import Config
from src.pipeline.evaluate import run_evaluation

class TestEvaluation(unittest.TestCase):
    def setUp(self):
        # Check Local Services
        try:
            r1 = requests.get(Config.OLLAMA_BASE_URL)
            self.services_up = (r1.status_code == 200)
        except:
            self.services_up = False
            
    def test_run_evaluation_pipeline(self):
        if not self.services_up:
            self.skipTest("Local services (Ollama) not running")
            
        # Run the evaluation script logic
        # We might want to mock the dataset size or run a smaller subset for testing
        # But run_evaluation uses a small hardcoded dataset, so it's fine.
        
        try:
            run_evaluation()
        except Exception as e:
            self.fail(f"Evaluation pipeline failed: {e}")
            
        # Check artifact
        self.assertTrue(os.path.exists("data/evaluation_results.csv"))
        
        # Cleanup (Optional)
        # os.remove("data/evaluation_results.csv")

if __name__ == "__main__":
    unittest.main()
