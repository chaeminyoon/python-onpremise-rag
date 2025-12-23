import unittest
import requests
from src.agent.graph import graph_app
from src.config import Config

class TestAgent(unittest.TestCase):
    def setUp(self):
        try:
            response = requests.get(Config.OLLAMA_BASE_URL)
            self.ollama_available = (response.status_code == 200)
        except:
            self.ollama_available = False

    def test_agent_graph_query(self):
        if not self.ollama_available:
            self.skipTest("Ollama server not running")

        print("\n>>> Testing Agent (JSON Router) with Query: 'Tell me about Samsung Electronics revenue.'")
        
        initial_state = {
            "input": "Tell me about Samsung Electronics revenue.",
            "chat_history": [],
            "context": [],
            "answer": "",
            "current_decision": {}
        }
        
        # Run
        events = list(graph_app.stream(initial_state, config={"recursion_limit": 5}))
        
        final_answer = ""
        search_occured = False
        
        for event in events:
            for node, state_update in event.items():
                print(f"\n--- Node: {node} ---")
                # print(state_update)
                
                if node == "oracle":
                    decision = state_update.get("current_decision", {})
                    if "answer" in state_update:
                        final_answer = state_update["answer"]
                    if decision.get("action") == "search":
                        print(f"  [Router Decision]: SEARCH {decision.get('entity')}")
                        search_occured = True
                
                if node == "tool_executor":
                    print("  [Tool Executor]: Context updated.")
        
        print(f"\nFinal Answer: {final_answer}")
        
        if search_occured:
            print("SUCCESS: Agent decided to search.")
        else:
            print("WARNING: Agent did not search.")
            
        self.assertTrue(len(final_answer) > 0)

if __name__ == '__main__':
    unittest.main()
