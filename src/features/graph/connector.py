from neo4j import GraphDatabase
from typing import List, Dict, Any
from src.config import Config
from src.features.schemas import IngestedDoc, ContentType, Table, Row

class GraphConnector:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USERNAME, Config.NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def ingest_document(self, doc: IngestedDoc, concepts: List[str]):
        """
        Ingest a document/chunk and its related concepts into Neo4j.
        Handles both TEXT and TABLE content types.
        """
        with self.driver.session() as session:
            # 1. Merge Document Node (Parent)
            # We assume metadata has 'filename' or 'source' to identify the parent document.
            doc_source = doc.metadata.get("source", "Unknown_Source")
            session.run(
                """
                MERGE (d:Document {id: $source})
                ON CREATE SET d.created_at = timestamp(), d.title = $source
                """,
                source=doc_source
            )

            # 2. Merge Chunk/Table Node
            if doc.content_type == ContentType.TABLE and doc.table_data:
                self._ingest_table(session, doc, doc_source, concepts)
            else:
                self._ingest_text_chunk(session, doc, doc_source, concepts)

    def _ingest_text_chunk(self, session, doc: IngestedDoc, doc_source: str, concepts: List[str]):
        """
        Ingest a standard text chunk.
        """
        query = """
        MATCH (d:Document {id: $doc_source})
        MERGE (c:Chunk {id: $chunk_id})
        ON CREATE SET c.text = $text, c.vector_id = $vector_id, c.page = $page
        MERGE (d)-[:CONTAINS]->(c)
        
        WITH c
        UNWIND $concepts as concept_name
        MERGE (con:Concept {name: concept_name})
        MERGE (c)-[:MENTIONS]->(con)
        """
        session.run(
            query,
            doc_source=doc_source,
            chunk_id=doc.id,
            text=doc.content,
            vector_id=doc.vector_id or "", # Should be populated if VectorDB is ready, else empty
            page=doc.metadata.get("page", 1),
            concepts=concepts
        )

    def _ingest_table(self, session, doc: IngestedDoc, doc_source: str, concepts: List[str]):
        """
        Ingest a Table and its Rows.
        """
        table = doc.table_data
        
        # 1. Create Table Node and Link to Doc
        query_table = """
        MATCH (d:Document {id: $doc_source})
        MERGE (t:Table {id: $table_id})
        ON CREATE SET t.caption = $caption, t.markdown = $markdown
        MERGE (d)-[:CONTAINS]->(t)
        """
        session.run(
            query_table,
            doc_source=doc_source,
            table_id=table.id,
            caption=table.caption,
            markdown=table.markdown
        )

        # 2. Create Rows (Batch Processing)
        # We assume rows might have individual concepts extracted? 
        # For now, we link the main *Table* concepts to the Table node, 
        # but the spec says (:Row)-[:MENTIONS]->(:Concept) acts on Row serialized data.
        # If we passed 'concepts' here, it's for the whole table doc.
        
        # NOTE: To strictly follow spec, we need concepts PER ROW.
        # But 'ingest_document' receives a list of concepts for the whole doc.
        # In 'build_graph.py', we should probably iterate rows and extract concepts per row 
        # if we want row-level granularity.
        # For this implementation, let's assume 'concepts' passed here are for the *Table Context* (Summary).
        # AND we will assume the caller might call a separate method for Row concept linking, 
        # OR we just link these concepts to the Table.
        
        # Let's link Table-level concepts first.
        query_table_concepts = """
        MATCH (t:Table {id: $table_id})
        UNWIND $concepts as concept_name
        MERGE (con:Concept {name: concept_name})
        MERGE (t)-[:MENTIONS]->(con)
        """
        session.run(query_table_concepts, table_id=table.id, concepts=concepts)
        
        # 3. Ingest Rows (without concepts for now, unless extracted separately)
        # We prepare a list of dicts for UNWIND
        rows_data = [
            {
                "id": r.id, 
                "index": r.index, 
                "data": str(r.data), # Neo4j doesn't store raw JSON maps easily without APOC, stringify for now
                "serialized_text": r.serialized_text
            }
            for r in table.rows
        ]
        
        query_rows = """
        MATCH (t:Table {id: $table_id})
        UNWIND $rows as row_data
        MERGE (r:Row {id: row_data.id})
        ON CREATE SET r.index = row_data.index, r.data_json = row_data.data, r.serialized_text = row_data.serialized_text
        MERGE (t)-[:HAS_ROW]->(r)
        """
        session.run(query_rows, table_id=table.id, rows=rows_data)

    def ingest_row_concepts(self, row_id: str, concepts: List[str]):
        """
        Helper to link a Row to Concepts. 
        Should be called after extracting concepts from row.serialized_text.
        """
        query = """
        MATCH (r:Row {id: $row_id})
        UNWIND $concepts as concept_name
        MERGE (con:Concept {name: concept_name})
        MERGE (r)-[:MENTIONS]->(con)
        """
        session = self.driver.session()
        session.run(query, row_id=row_id, concepts=concepts)
        session.close()
