import unittest
from unittest.mock import MagicMock, patch
from src.features.schemas import IngestedDoc, ContentType, Table, Row
from src.features.graph.connector import GraphConnector

class TestGraphIntegration(unittest.TestCase):
    def setUp(self):
        # Mock the Neo4j driver in the connector
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__.return_value = self.mock_session
        
        with patch('neo4j.GraphDatabase.driver', return_value=self.mock_driver):
            self.connector = GraphConnector()

    def test_ingest_text_chunk(self):
        doc = IngestedDoc(
            content="Samsung Electronics revenue is huge.",
            content_type=ContentType.TEXT,
            metadata={"source": "report.pdf", "page": 1}
        )
        concepts = ["Samsung Electronics", "Revenue"]
        
        self.connector.ingest_document(doc, concepts)
        
        # Verify Cypher execution for Document and Chunk
        queries = [call[0][0] for call in self.mock_session.run.call_args_list]
        self.assertTrue(any("MERGE (d:Document" in q for q in queries))
        self.assertTrue(any("MERGE (c:Chunk" in q for q in queries))
        self.assertTrue(any("(c)-[:MENTIONS]->(con)" in q for q in queries))
        print("[Pass] Text Chunk Cypher Queries Verified")

    def test_ingest_table(self):
        row = Row(index=0, data={"col": "val"}, serialized_text="Col is Val.")
        table = Table(caption="Test Table", markdown="| col | val |", rows=[row])
        doc = IngestedDoc(
            content="Markdown Table",
            content_type=ContentType.TABLE,
            metadata={"source": "data.xlsx"},
            table_data=table
        )
        concepts = ["Test Table Concept"]
        
        self.connector.ingest_document(doc, concepts)
        
        queries = [call[0][0] for call in self.mock_session.run.call_args_list]
        self.assertTrue(any("MERGE (t:Table" in q for q in queries))
        self.assertTrue(any("UNWIND $rows as row_data" in q for q in queries))
        print("[Pass] Table & Row Cypher Queries Verified")

if __name__ == '__main__':
    unittest.main()
