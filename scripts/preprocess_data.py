import os
import sys
import re
import json
import traceback
from pathlib import Path
from docx import Document
from typing import Dict, List, Any

# Add project root to sys.path to import sandbox components
sys.path.append(str(Path(__file__).parent.parent))
from sop_deeplang.sandbox.excel_parser import ExcelParser_Sandbox

class DocxParser:
    """
    Parses .docx files and extracts sections using TOC indices as ground truth.
    """
    def __init__(self, file_path: str, report_id: str = "Unknown"):
        self.file_path = Path(file_path)
        self.report_id = report_id
        if self.file_path.suffix == '.doc':
            # Note: doc to docx conversion is expected to be handled externally or via local tools
            self.file_path = self._convert_doc_to_docx(self.file_path)
        
        self.doc = Document(str(self.file_path))
        self.toc_list = self._extract_toc()
        self.sections = self._parse_sections()

    def _convert_doc_to_docx(self, doc_path: Path) -> Path:
        docx_path = doc_path.with_suffix('.docx')
        if docx_path.exists():
            return docx_path
        return doc_path 

    def _extract_toc(self) -> List[str]:
        """Extracts and cleans the Table of Contents from the document."""
        toc = []
        for p in self.doc.paragraphs:
            style_name = p.style.name.lower()
            if style_name.startswith('toc') and not style_name.startswith('toc heading'):
                text = p.text.strip()
                if text:
                    # Remove ending page numbers and dots/tabs
                    clean_text = re.sub(r'[\t\.\s]+\d+$', '', text).strip()
                    # Remove leading sequence numbers (e.g. "1.1 ", "1\t", "一、")
                    clean_text = re.sub(r'^(\d+(\.\d+)*|[\u2460-\u2473]|[一二三四五六七八九十百]+[、.])[\t\s]*', '', clean_text).strip()
                    if clean_text:
                        toc.append(clean_text)
        return toc

    def _parse_sections(self) -> Dict[str, str]:
        """Parses the document body sections based on the TOC and fixed headers."""
        sections = {}
        fixed_headers = [
            "验证报告", "GLP遵从性声明和签字页", "签字页", "质量保证声明", 
            "目录", "附表目录", "附图目录", "缩略语表", "摘要"
        ]
        
        # Combine fixed headers with TOC to form a complete list of targets
        all_targets = fixed_headers + self.toc_list
        # Use normalized (no spaces) keys for robust matching
        normalized_targets = {re.sub(r'\s+', '', t): t for t in all_targets if t}
        
        current_heading = "Header/Title"
        current_content = []

        def flush():
            nonlocal current_heading, current_content
            if current_content:
                sections[current_heading] = "\n".join(current_content).strip()
            current_content = []

        for child in self.doc.element.body.iterchildren():
            if child.tag.endswith('p'):
                paras = [p for p in self.doc.paragraphs if p._element == child]
                if not paras: continue
                para = paras[0]
                text = para.text.strip()
                if not text: continue
                
                # Skip the paragraphs that ARE the TOC entries
                if para.style.name.lower().startswith('toc'):
                    continue
                
                # Clean the body text for matching (remove leading numbers)
                body_clean = re.sub(r'^(\d+(\.\d+)*|[\u2460-\u2473]|[一二三四五六七八九十百]+[、.])[\t\s]*', '', text).strip()
                norm_text = re.sub(r'\s+', '', body_clean)
                
                is_new_section = False
                matched_heading = None
                
                if norm_text in normalized_targets:
                    is_new_section = True
                    matched_heading = normalized_targets[norm_text]
                else:
                    # Try partial match for fixed headers if they are long or contain extra text
                    for fh in fixed_headers:
                        if fh in text and len(text) < 50:
                            is_new_section = True
                            matched_heading = fh
                            break
                
                if is_new_section:
                    flush()
                    current_heading = matched_heading
                else:
                    current_content.append(text)
                    
            elif child.tag.endswith('tbl'):
                tables = [t for t in self.doc.tables if t._element == child]
                if tables:
                    md_table = self._table_to_markdown(tables[0])
                    current_content.append(md_table)

        flush()
        return sections

    def _table_to_markdown(self, table) -> str:
        rows = []
        for row in table.rows:
            rows.append([cell.text.replace('\n', '<br>').replace('|', '\\|').strip() for cell in row.cells])
        if not rows: return ""
        
        headers = rows[0]
        md = f"| {' | '.join(headers)} |\n"
        md += f"| {' | '.join(['---'] * len(headers))} |\n"
        for row in rows[1:]:
            md += f"| {' | '.join(row)} |\n"
        return md

def merge_sources(protocol_sections: Dict[str, str], report_sections: Dict[str, str], toc_order: List[str]) -> List[Dict]:
    """
    Merges Protocol and Report sections into a JSON-friendly list of dictionaries.
    toc_order comes from the report's DocxParser.toc_list.
    """
    fixed_headers = [
        "验证报告", "GLP遵从性声明和签字页", "质量保证声明", 
        "目录", "附表目录", "附图目录", "缩略语表", "摘要"
    ]
    
    # We use a mapping to align Protocol names to Report names where they differ
    HEADER_MAPPING = {
        "验证方案": "验证报告",
        "签字页": "GLP遵从性声明和签字页"
    }
    
    # Pre-process protocol sections with mapping
    mapped_protocol = {}
    for h, content in protocol_sections.items():
        standardized_h = HEADER_MAPPING.get(h, h)
        if standardized_h in mapped_protocol:
            mapped_protocol[standardized_h] += "\n\n" + content
        else:
            mapped_protocol[standardized_h] = content
            
    # Combine fixed headers and report's TOC for the final sequence
    ordered_sequence = []
    # 1. Fixed headers
    for h in fixed_headers:
        ordered_sequence.append(h)
    # 2. Add TOC items from report (avoiding duplicates with fixed headers)
    for h in toc_order:
        if h not in ordered_sequence:
            ordered_sequence.append(h)
            
    output_data = []
    for heading in ordered_sequence:
        p_content = mapped_protocol.get(heading, "")
        r_content = report_sections.get(heading, "")
        
        # If both are empty, we still keep the title but content is empty
        output_data.append({
            "section_title": heading,
            "original_content": p_content,
            "generate_content": r_content,
            "sop": ""
        })
        
        # Stop at "归档" as requested
        if heading == "归档" or heading == "9 归档" or "归档" in heading and len(heading) < 10:
             # Further ensure it is the '归档' section
             if heading.strip().endswith("归档") or heading.strip() == "归档":
                 break

    return output_data

def process_directory(dir_path: Path, output_root: Path):
    """Processes a single project directory."""
    print(f"--- Processing: {dir_path.name} ---")
    
    # Doc discovery
    protocol_files = [f for f in dir_path.glob("*方案*.docx") if not f.name.startswith((".", ".~"))]
    if not protocol_files:
        protocol_files = [f for f in dir_path.glob("*方案*.doc") if not f.name.startswith((".", ".~"))]
        
    report_files = [f for f in (list(dir_path.glob("*REPORT*.docx")) + list(dir_path.glob("*报告*.docx"))) if not f.name.startswith((".", ".~"))]
    if not report_files:
        report_files = [f for f in (list(dir_path.glob("*REPORT*.doc")) + list(dir_path.glob("*报告*.doc"))) if not f.name.startswith((".", ".~"))]
    
    protocol_path = protocol_files[0] if protocol_files else None
    report_path = report_files[0] if report_files else None
    
    if not report_path:
        print(f"Skipping {dir_path.name}: No report file found.")
        return

    report_id = dir_path.name
    report_out_dir = output_root / report_id
    report_out_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Report parser is primary as it provides the TOC order
        report_parser = DocxParser(str(report_path), report_id)
        protocol_parser = DocxParser(str(protocol_path), report_id) if protocol_path else None
        
        protocol_sections = protocol_parser.sections if protocol_parser else {}
        report_sections = report_parser.sections
        
        # Merge using the report's TOC sequence
        merged_json = merge_sources(protocol_sections, report_sections, report_parser.toc_list)
        
        out_file = report_out_dir / "filtered_data.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(merged_json, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved to {out_file}")
            
    except Exception as e:
        print(f"Error processing {dir_path.name}: {e}")
        traceback.print_exc()

def main():
    base_dir = Path(r"D:\益诺思\sop生成\original_docx\BV报告")
    output_root = Path(r"D:\益诺思\sop生成\data_parsed")
    
    if not base_dir.exists():
        print(f"Source directory {base_dir} not found.")
        return

    # Process all project directories
    for project_dir in base_dir.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith("."):
            process_directory(project_dir, output_root)

if __name__ == "__main__":
    main()
