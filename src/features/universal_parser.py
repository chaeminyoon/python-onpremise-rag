import os
from typing import List, Dict, Any
from src.features.schemas import IngestedDoc
from src.features.converters.hwp_converter import HwpConverter
from src.features.converters.table_converter import TableConverter
from src.features.converters.pdf_converter import PdfConverter

class UniversalParser:
    def __init__(self):
        self.hwp_converter = HwpConverter()
        self.table_converter = TableConverter()
        self.pdf_converter = PdfConverter()

    def parse(self, file_path: str, metadata: Dict[str, Any] = {}) -> List[IngestedDoc]:
        """
        Parses a file and returns a list of IngestedDoc objects.
        Dispatches to the appropriate converter based on file extension.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower().strip()

        # Update metadata with basic file info
        file_meta = {
            **metadata,
            "filename": os.path.basename(file_path),
            "extension": ext
        }

        if ext in ['.hwp']:
            return self.hwp_converter.convert_hwp_legacy(file_path, file_meta)
        
        elif ext in ['.hwpx', '.zip']: # Identifying .zip as HWPX if needed, but strictly .hwpx is better
            return self.hwp_converter.convert_hwpx(file_path, file_meta)
        
        elif ext in ['.csv']:
            return self.table_converter.convert_csv(file_path, file_meta)
        
        elif ext in ['.xlsx', '.xls']:
            return self.table_converter.convert_excel(file_path, file_meta)

        elif ext in ['.pdf']:
            return self.pdf_converter.convert(file_path, file_meta)

        else:
            # Fallback for other text files or unsupported
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                from src.features.schemas import ContentType
                return [IngestedDoc(
                    content=text, 
                    content_type=ContentType.TEXT, 
                    metadata={**file_meta, "type": "fallback_text"}
                )]
            except Exception as e:
                print(f"Error parsing fallback {file_path}: {e}")
                return []
