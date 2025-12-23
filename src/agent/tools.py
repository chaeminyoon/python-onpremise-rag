from typing import List
from langchain_core.tools import tool
from langchain_community.vectorstores import Neo4jVector
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import Config

# Initialize Embeddings (Local BGE-M3)
embeddings = HuggingFaceEmbeddings(
    model_name=Config.EMBEDDING_MODEL_NAME,
    model_kwargs={'device': 'cpu'}, # Force CPU for safety, or check availability
    encode_kwargs={'normalize_embeddings': True}
)

# Initialize Neo4jVector from existing graph (Chunk nodes)
# This will create a vector index if it doesn't exist.
try:
    vector_store = Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=Config.NEO4J_URI,
        username=Config.NEO4J_USERNAME,
        password=Config.NEO4J_PASSWORD,
        index_name="vector_index",      # Name of the vector index in Neo4j
        node_label="Chunk",             # Nodes to search over
        text_node_properties=["text"],  # Property containing the text
        embedding_node_property="embedding", # Property to store/retrieve embedding
    )
    print("✅ Neo4jVector initialized successfully.")
except Exception as e:
    print(f"⚠️ Failed to initialize Neo4jVector: {e}")
    vector_store = None

@tool
def retrieval_tool(query: str) -> str:
    """
    Search the Knowledge Graph using Vector Search to find relevant context.
    Args:
        query: The search query string (e.g., "What is the vacation policy?").
    """
    if not vector_store:
        return "Search is unavailable (Vector Store not initialized)."
        
    print(f"DEBUG: Vector Search for query: '{query}'")
    
    try:
        # Perform Similarity Search
        results = vector_store.similarity_search(query, k=3)
        
        if not results:
            return "No relevant documents found."
            
        # Format results
        context_str = ""
        for i, doc in enumerate(results, 1):
            context_str += f"Source {i}:\n{doc.page_content}\n\n"
            
        return context_str
    except Exception as e:
        return f"Error during vector search: {e}"
