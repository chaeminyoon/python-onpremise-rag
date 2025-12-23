import unittest
import os
import sys
import pandas as pd
from src.features.universal_parser import UniversalParser
from src.features.schemas import ContentType

class TestUniversalParser(unittest.TestCase):
    def setUp(self):
        self.parser = UniversalParser()
        # Create dummy files for testing
        self.dummy_csv = "dummy.csv"
        df = pd.DataFrame({'Product': ['Widget A'], 'Price': [100]})
        df.to_csv(self.dummy_csv, index=False)

    def tearDown(self):
        if os.path.exists(self.dummy_csv):
            os.remove(self.dummy_csv)

    def test_csv_parsing(self):
        docs = self.parser.parse(self.dummy_csv)
        self.assertTrue(len(docs) > 0)
        table_doc = docs[0]
        self.assertEqual(table_doc.content_type, ContentType.TABLE)
        self.assertTrue(table_doc.table_data is not None)
        
        # Check Serialized Text
        row = table_doc.table_data.rows[0]
        self.assertIn("Product: Widget A", row.serialized_text)
        self.assertIn("Price: 100", row.serialized_text)
        print(f"[Pass] CSV Serialized: {row.serialized_text}")

    def test_hwp_import(self):
        # We can't easily test HWP without a real file and olefile installed,
        # but we can verify classes load and methods exist.
        from src.features.converters.hwp_converter import HwpConverter
        converter = HwpConverter()
        self.assertTrue(hasattr(converter, 'convert_hwp_legacy'))

    def test_pydantic_validation(self):
        from src.features.schemas import SerializedText
        st = SerializedText(text="Test")
        self.assertEqual(st.text, "Test")

if __name__ == '__main__':
    unittest.main()
