import os
import argparse
from tqdm import tqdm
from src.features.universal_parser import UniversalParser
from src.features.schemas import ContentType
from src.features.graph.extractor import GraphExtractor
from src.features.graph.connector import GraphConnector

def main(input_dir: str):
    parser = UniversalParser()
    extractor = GraphExtractor()
    connector = GraphConnector()
    
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
    
    print(f"Found {len(files)} files in {input_dir}")
    
    for file_path in tqdm(files, desc="Processing Files"):
        try:
            # 1. Parse File
            docs = parser.parse(file_path)
            
            for doc in docs:
                # 2. Extract Concepts from Main Content (Text or Table Summary)
                # For Tables, doc.content is usually the markdown representation
                main_concepts = extractor.extract_concepts(doc.content)
                
                # 3. Ingest Document/Table Node
                connector.ingest_document(doc, main_concepts)
                
                # 4. If Table, Process Rows Individually
                if doc.content_type == ContentType.TABLE and doc.table_data:
                    for row in doc.table_data.rows:
                        # Extract concepts from "Header: Value" sentence
                        row_concepts = extractor.extract_concepts(row.serialized_text)
                        if row_concepts:
                            connector.ingest_row_concepts(row.id, row_concepts)

        except Exception as e:
            print(f"Failed to process {file_path}: {e}")
    
    connector.close()
    print("Graph Build Completed.")

if __name__ == "__main__":
    # Example usage: python src/pipeline/build_graph.py --input_dir data_raw
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--input_dir", type=str, default="data_raw")
    args = arg_parser.parse_args()
    
    if not os.path.exists(args.input_dir):
        print(f"Input directory {args.input_dir} not found.")
    else:
        main(args.input_dir)
