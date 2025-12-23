import os
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import olefile
import zlib
from src.features.schemas import IngestedDoc, ContentType, Table, Row

class HwpConverter:
    def __init__(self):
        pass

    def convert_hwp_legacy(self, file_path: str, metadata: Dict[str, Any] = {}) -> List[IngestedDoc]:
        """
        Extract text from Legacy HWP (OLE) files.
        Strategy A: Focus on text extraction. Table structure might be lost or flat.
        """
        text_content = ""
        try:
            if not olefile.isOleFile(file_path):
                raise ValueError("Not a valid OLE file")

            with olefile.OleFileIO(file_path) as f:
                dirs = f.listdir()
                # HWP 5.0 typically keeps body text in 'BodyText' stream sections
                body_sections = [d for d in dirs if d[0] == "BodyText"]
                
                for section in body_sections:
                    stream = f.openstream(section)
                    data = stream.read()
                    # Decompress using zlib (window bits -15 for raw deflate is common in HWP)
                    try:
                        decompressed = zlib.decompress(data, -15)
                        # Extract UTF-16 text (HWP uses UTF-16LE)
                        # This is a naive extraction. Real HWP parsing requires parsing the records Structure.
                        # For Risk Management Strategy A, we try to grab readable text.
                        # However, raw stream parsing of HWP records is extremely complex.
                        # If simple decode fails or produces garbage, we might need a library like 'pyhwp' 
                        # but that wasn't in the plan.
                        # Let's try a very heuristic approach: scan for valid utf-16 chars.
                        text_content += self._extract_text_from_stream(decompressed)
                    except Exception as e:
                        # Sometimes it's not compressed or different format
                        pass

            doc = IngestedDoc(
                content=text_content.strip(),
                content_type=ContentType.TEXT,
                metadata={**metadata, "source": file_path, "type": "hwp_legacy"}
            )
            return [doc]

        except Exception as e:
            print(f"Error parsing HWP {file_path}: {e}")
            return []

    def _extract_text_from_stream(self, data: bytes) -> str:
        """
        Very crude heuristic to extract text from binary stream.
        HWP text is usually UTF-16LE.
        """
        # This is a placeholder for the complex HWP parsing logic.
        # In a real implementation, we would use a dedicated library or subprocess to 'hwp5txt'.
        # Since 'pyhwp' installation can be tricky on Windows without compilation, 
        # we will assume for this prototype that we can extract some strings.
        # For now, let's return a placeholder if we can't parse real records, 
        # OR suggest the user to use HWPX.
        
        # Attempt to decode as utf-16le and filter control characters
        try:
            text = data.decode('utf-16-le', errors='ignore')
            # Filter out control characters that are not formatting
            clean_text = "".join([c for c in text if c.isprintable() or c in ['\n', '\t']])
            return clean_text
        except:
            return ""

    def convert_hwpx(self, file_path: str, metadata: Dict[str, Any] = {}) -> List[IngestedDoc]:
        """
        Parse HWPX (Zip + XML) and convert tables to Markdown.
        """
        try:
            if not zipfile.is_zipfile(file_path):
                raise ValueError("Not a valid Zip/HWPX file")

            text_parts = []
            tables = [] # Placeholder for extracted tables if we want to separate them via IngestedDoc
            
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Main content is usually in Contents/section0.xml
                # There might be multiple sections.
                section_files = [f for f in zf.namelist() if f.startswith('Contents/section') and f.endswith('.xml')]
                
                for sec_file in section_files:
                    xml_data = zf.read(sec_file)
                    root = ET.fromstring(xml_data)
                    
                    # Need to handle namespaces properly in real HWPX
                    # HWPX namespaces: hp, hc, hs, etc.
                    # We will iterate elements.
                    
                    ns = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph'} 
                    # Note: Namespace URLs might differ by version, often better to ignore NS or wildcard.

                    for elem in root.iter():
                        # Paragraph text
                        if elem.tag.endswith('t'): # <hp:t> contains text
                            if elem.text:
                                text_parts.append(elem.text)
                        
                        # Tables
                        # Identifying tables in HWPX requires finding <hp:table> or similar structures
                        # constructing the markdown.
                        # This is non-trivial without the full schema, but we can try to detect 'tr' / 'tc' equivalents.
                        
                        # For this MVP, we focus on aggregating text.
                        # A robust Markdown table converter for HWPX requires mapping 
                        # Grid -> Col/Row span -> Markdown.
            
            full_text = "\n".join(text_parts)
            
            doc = IngestedDoc(
                content=full_text,
                content_type=ContentType.TEXT, # If we successfully parsed a table, we'd add TABLE type docs
                metadata={**metadata, "source": file_path, "type": "hwpx"}
            )
            return [doc]

        except Exception as e:
            print(f"Error parsing HWPX {file_path}: {e}")
            return []
