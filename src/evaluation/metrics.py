from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from src.config import Config

def get_ragas_llm_embeddings():
    """
    Returns the Local LLM and Embeddings configured for RAGAS.
    """
    llm = ChatOllama(
        base_url=Config.OLLAMA_BASE_URL,
        model=Config.LLM_MODEL_NAME,  # e.g., "llama3.1"
        temperature=0
    )
    
    embeddings = HuggingFaceEmbeddings(
        model_name=Config.EMBEDDING_MODEL_NAME,  # e.g., "BAAI/bge-m3"
        model_kwargs={'device': 'cpu'}, # Use CPU or 'cuda' if available
        encode_kwargs={'normalize_embeddings': True}
    )
    
    return llm, embeddings

# Standard Metrics to use
METRICS = [
    faithfulness,
    answer_relevancy,
    context_precision
]
