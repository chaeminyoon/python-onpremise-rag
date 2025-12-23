import pdfplumber
from typing import List, Dict, Any
from src.features.schemas import IngestedDoc, ContentType, Table, Row

class PdfConverter:
    def __init__(self):
        pass

    def convert(self, file_path: str, metadata: Dict[str, Any] = {}) -> List[IngestedDoc]:
        """
        Extract text and tables from PDF using pdfplumber.
        """
        docs = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 1. Extract Tables
                    tables = page.extract_tables()
                    for table_data in tables:
                        # table_data is List[List[str]]
                        if not table_data:
                            continue
                            
                        # Convert to Markdown
                        # Simple logic: First row is header
                        markdown_lines = []
                        header = table_data[0]
                        # Clean newlines in cells
                        header = [str(h).replace('\n', ' ') if h else '' for h in header]
                        
                        markdown_lines.append("| " + " | ".join(header) + " |")
                        markdown_lines.append("| " + " | ".join(['---'] * len(header)) + " |")
                        
                        rows_obj = []
                        for i, row_vals in enumerate(table_data[1:]):
                            clean_row = [str(c).replace('\n', ' ') if c else '' for c in row_vals]
                            markdown_lines.append("| " + " | ".join(clean_row) + " |")
                            
                            # Create Row object
                            # Map header to value
                            row_dict = {}
                            serialized_parts = []
                            for h, v in zip(header, clean_row):
                                row_dict[h] = v
                                if v.strip():
                                    serialized_parts.append(f"{h}: {v}")
                            
                            rows_obj.append(Row(
                                index=i,
                                data=row_dict,
                                serialized_text=", ".join(serialized_parts) + "."
                            ))
                            
                        md_text = "\n".join(markdown_lines)
                        
                        table_doc = IngestedDoc(
                            content=md_text,
                            content_type=ContentType.TABLE,
                            metadata={
                                **metadata, 
                                "page": page_num + 1,
                                "source": file_path
                            },
                            table_data=Table(
                                markdown=md_text,
                                rows=rows_obj,
                                metadata={"page": page_num + 1}
                            )
                        )
                        docs.append(table_doc)

                    # 2. Extract Text (excluding tables if possible, but pdfplumber extracts all)
                    # For simplicity, we extract full text as a separate Text chunk.
                    # Overlap is acceptable for RAG context.
                    text = page.extract_text()
                    if text:
                        text_doc = IngestedDoc(
                            content=text,
                            content_type=ContentType.TEXT,
                            metadata={
                                **metadata,
                                "page": page_num + 1,
                                "source": file_path
                            }
                        )
                        docs.append(text_doc)
            return docs

        except Exception as e:
            print(f"Error parsing PDF {file_path}: {e}")
            return []
