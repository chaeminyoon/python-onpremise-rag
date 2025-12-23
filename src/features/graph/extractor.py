from typing import List, Optional
import json
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
# from langchain_huggingface import HuggingFaceEmbeddings # Reserved for VectorDB phase
from src.config import Config

class GraphExtractor:
    def __init__(self):
        # Initialize Llama 3.1 via Ollama
        self.llm = ChatOllama(
            base_url=Config.OLLAMA_BASE_URL,
            model=Config.LLM_MODEL_NAME,
            temperature=0,
            format="json"  # Force JSON mode for Llama 3.1
        )
        
    def extract_concepts(self, text: str) -> List[str]:
        """
        Extracts key concepts from the given text using Local LLM.
        """
        if not text or len(text.strip()) < 10:
             return []
        
        prompt = f"""
        You are an expert Data Scientist. Extract key business concepts and named entities (companies, people, locations) from the text below.
        Return ONLY a JSON object with a single key 'concepts' containing a list of strings.
        Do not add any explanation.
        
        Example:
        {{
            "concepts": ["Samsung Electronics", "Revenue", "2024", "Growth"]
        }}
        
        Text:
        {text[:4000]}
        """
        
        try:
            response_msg = self.llm.invoke(prompt)
            content = response_msg.content.strip()
            
            # Parsing Llama 3.1 JSON output
            data = json.loads(content)
            if "concepts" in data and isinstance(data["concepts"], list):
                return [str(c) for c in data["concepts"]]
            return []
            
        except json.JSONDecodeError:
            print(f"JSON Parse Error. Output was: {content}")
            return []
        except Exception as e:
            print(f"Error extracting concepts with Llama: {e}")
            return []
