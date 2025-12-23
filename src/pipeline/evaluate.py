import os
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from langchain_community.graphs import Neo4jGraph

from src.config import Config
from src.agent.graph import graph_app
from src.pipeline.trace import setup_tracing
from src.evaluation.metrics import get_ragas_llm_embeddings, METRICS

# Define Golden Dataset
GOLDEN_DATASET = [
    {
        "question": "What is the revenue performance of Samsung Electronics in 2024?",
        "ground_truth": "Samsung Electronics announced a 15% increase in annual revenue for 2024."
    },
    {
        "question": "Which company announced revenue growth?",
        "ground_truth": "Samsung Electronics announced the revenue growth."
    }
]

def seed_database():
    """
    Seeds the Neo4j database with the knowledge required for the Golden Dataset.
    This ensures the Agent actually finds context.
    """
    print("🌱 Seeding Database with Test Data...")
    graph = Neo4jGraph(
        url=Config.NEO4J_URI, 
        username=Config.NEO4J_USERNAME, 
        password=Config.NEO4J_PASSWORD
    )
    
    # Simple Cypher to create a Concept node and a mock Chunk relation
    # Ideally we use the Pipeline, but for Eval speed we inject directly.
    query = """
    MERGE (c:Concept {name: "Samsung Electronics"})
    MERGE (t:Chunk {text: "Samsung Electronics announced a 15% increase in annual revenue for 2024.", chunk_id: "eval_chunk_1"})
    MERGE (c)-[:MENTIONS]->(t)
    """
    graph.query(query)
    print("✅ Database Seeded.")

def run_evaluation():
    # 1. Setup Tracing
    setup_tracing()
    
    # 2. Seed Data
    seed_database()
    
    # 3. Initialize RAGAS Config
    llm, embeddings = get_ragas_llm_embeddings()
    
    # 4. Collection Output from Agent
    data_samples = {
        "question": [],
        "answer": [],
        "contexts": [],
        "ground_truth": []
    }
    
    print("🤖 Running Agent on Golden Dataset...")
    for item in GOLDEN_DATASET:
        question = item["question"]
        ground_truth = item["ground_truth"]
        
        # Input Fix: StateGraph expects 'chat_history' often, or use 'input' if defined in State
        # Based on graph.py, it uses state['input'] primarily but checks chat_history.
        # Let's populate both to be safe.
        from langchain_core.messages import HumanMessage
        inputs = {
            "input": question, 
            "chat_history": [HumanMessage(content=question)]
        }
        
        # Run with recursion limit
        try:
            # We need to capture tool outputs for "contexts"
            # stream(inputs, stream_mode="updates") returns dicts of {node_name: {updated_keys}}
            result_stream = graph_app.stream(inputs, config={"recursion_limit": 10}, stream_mode="updates")
            
            final_answer = ""
            retrieved_contexts = []
            
            for update in result_stream:
                # Check for Tool Node updates (context)
                if "tool_executor" in update:
                    tool_output = update["tool_executor"]
                    if "context" in tool_output:
                        # Extend our context list
                        retrieved_contexts.extend(tool_output["context"])
                
                # Check for Oracle Node updates (answer)
                if "oracle" in update:
                    oracle_output = update["oracle"]
                    if "answer" in oracle_output:
                        final_answer = oracle_output["answer"]
            
            # If answer is empty, maybe it's in the last state
            if not final_answer:
                # It might have been set in an earlier step or failed
                final_answer = "No answer produced."

            print(f"  Q: {question}")
            print(f"  A: {final_answer[:50]}...")
            
            data_samples["question"].append(question)
            data_samples["answer"].append(final_answer)
            data_samples["contexts"].append(retrieved_contexts)
            data_samples["ground_truth"].append(ground_truth)
            
        except Exception as e:
            print(f"Error processing question '{question}': {e}")

    # 5. Build Dataset
    hf_dataset = Dataset.from_dict(data_samples)
    
    # 6. Run Evaluation
    print("📊 Starting RAGAS Evaluation (This may take time using Local LLM)...")
    results = evaluate(
        dataset=hf_dataset,
        metrics=METRICS,
        llm=llm,
        embeddings=embeddings
    )
    
    # 7. Save Results
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "evaluation_results.csv")
    
    df = results.to_pandas()
    df.to_csv(output_path, index=False)
    print(f"✅ Evaluation Complete. Results saved to: {output_path}")
    print(results)

if __name__ == "__main__":
    run_evaluation()
