from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class ContentType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"

class SerializedText(BaseModel):
    """
    Represents a natural language serialization of structured data.
    e.g., "Revenue for 2023 is 500 Million USD."
    """
    text: str
    original_key: Optional[str] = None
    original_value: Optional[str] = None

class Row(BaseModel):
    """
    Represents a single row in a table.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    index: int
    data: Dict[str, Any]  # Raw JSON data: {"col1": "val1", ...}
    serialized_text: str  # Sentence representation for embedding
    # We might want to store list of SerializedText objects for granular mapping if needed later

class Table(BaseModel):
    """
    Represents a table extracted from a document.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caption: str = ""
    markdown: str = ""  # Full markdown representation for LLM context
    rows: List[Row] = []
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestedDoc(BaseModel):
    """
    Standardized document unit for the pipeline.
    Processing result of the Universal Parser.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str  # Main text content or markdown representation of table
    content_type: ContentType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Bi-directional ID Links
    graph_node_id: Optional[str] = None
    vector_id: Optional[str] = None
    
    table_data: Optional[Table] = None # Populated if content_type is TABLE

class ExtractionResult(BaseModel):
    """
    Wrapper for the result of a file parsing operation.
    """
    file_path: str
    documents: List[IngestedDoc]
    errors: List[str] = []
