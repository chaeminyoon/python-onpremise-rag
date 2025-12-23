import pandas as pd
from typing import List, Dict, Any, Optional
import json
from src.features.schemas import IngestedDoc, ContentType, Table, Row, SerializedText

class TableConverter:
    def __init__(self):
        pass

    def convert_csv(self, file_path: str, metadata: Dict[str, Any] = {}) -> List[IngestedDoc]:
        """
        Convert CSV to IngestedDoc with Table structure and SerializedText.
        """
        try:
            df = pd.read_csv(file_path)
            # Replace NaN with empty string or None to avoid JSON serialization issues
            df = df.where(pd.notnull(df), None)
            return self._process_dataframe(df, file_path, "csv", metadata)
        except Exception as e:
            print(f"Error parsing CSV {file_path}: {e}")
            return []

    def convert_excel(self, file_path: str, metadata: Dict[str, Any] = {}) -> List[IngestedDoc]:
        """
        Convert Excel to IngestedDoc. Support multiple sheets.
        """
        try:
            xls = pd.ExcelFile(file_path)
            docs = []
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                df = df.where(pd.notnull(df), None)
                sheet_metadata = metadata.copy()
                sheet_metadata["sheet_name"] = sheet_name
                docs.extend(self._process_dataframe(df, file_path, "excel", sheet_metadata))
            return docs
        except Exception as e:
            print(f"Error parsing Excel {file_path}: {e}")
            return []

    def _process_dataframe(self, df: pd.DataFrame, file_path: str, source_type: str, metadata: Dict[str, Any]) -> List[IngestedDoc]:
        """
        Common logic to transform DataFrame into IngestedDoc with Table schema.
        """
        table_rows = []
        full_text_parts = []
        columns = df.columns.tolist()
        
        # Markdown representation for the whole table (for context)
        markdown_table = df.to_markdown(index=False)
        
        for idx, row_series in df.iterrows():
            row_data = row_series.to_dict()
            
            # Serialize: "Header is Value."
            sentences = []
            for col in columns:
                val = row_data.get(col)
                if val:
                    sentences.append(f"{col}: {val}")
            
            serialized_text = ", ".join(sentences) + "."
            full_text_parts.append(serialized_text)
            
            table_row = Row(
                index=idx,
                data=row_data,
                serialized_text=serialized_text
            )
            table_rows.append(table_row)

        table = Table(
            caption=f"Table extracted from {file_path}",
            markdown=markdown_table or "",
            rows=table_rows,
            metadata=metadata
        )

        # We create one IngestedDoc representing the Table
        # The content is the Markdown representation + some summary
        doc = IngestedDoc(
            content=f"Table from {file_path}.\n\n{markdown_table}",
            content_type=ContentType.TABLE,
            metadata={
                **metadata,
                "source": file_path,
                "type": source_type
            },
            table_data=table
        )
        
        return [doc]
