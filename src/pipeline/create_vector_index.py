
import os
import sys

# Ensure src is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from langchain_community.vectorstores import Neo4jVector
from langchain_huggingface import HuggingFaceEmbeddings
from src.config import Config

def create_index():
    print("🚀 Starting Vector Index Creation...")
    print(f"   - Embedding Model: {Config.EMBEDDING_MODEL_NAME}")
    print(f"   - Neo4j URI: {Config.NEO4J_URI}")
    
    # 1. Initialize Embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name=Config.EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'}, # Config.EMBEDDING_DEVICE can be used if robust
        encode_kwargs={'normalize_embeddings': True}
    )

    # 2. Create/Update Index
    # from_existing_graph will:
    # - Fetch 'Chunk' nodes
    # - Calculate embeddings for 'text' property
    # - Store them in 'embedding' property
    # - Create a vector index named 'vector_index'
    try:
        vector_store = Neo4jVector.from_existing_graph(
            embedding=embeddings,
            url=Config.NEO4J_URI,
            username=Config.NEO4J_USERNAME,
            password=Config.NEO4J_PASSWORD,
            index_name="vector_index",
            node_label="Chunk",
            text_node_properties=["text"],
            embedding_node_property="embedding",
        )
        print("✅ Vector Index 'vector_index' created/updated successfully.")
        
        # Optional: Test search
        print("🔎 Testing Search...")
        results = vector_store.similarity_search("테스트", k=1)
        print(f"   - Found {len(results)} results for trigger check.")
        
    except Exception as e:
        print(f"❌ Failed to create vector index: {e}")

if __name__ == "__main__":
    create_index()
