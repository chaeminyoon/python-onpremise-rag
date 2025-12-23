import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    NEO4J_URI = os.getenv("NEO4J_URI", "")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    
    # Local Stack Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL_NAME = "llama3.1"
    
    # HuggingFace Embedding (Local)
    EMBEDDING_MODEL_NAME = "BAAI/bge-m3"
    EMBEDDING_DEVICE = "cuda" if os.getenv("USE_CUDA", "false").lower() == "true" else "cpu"
