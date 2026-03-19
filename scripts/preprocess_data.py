import os
import sys
import subprocess
import shutil
from pathlib import Path
from docx import Document
import pandas as pd
from typing import Dict, List, Any

# Add project root to sys.path to import sandbox components
sys.path.append(str(Path(__file__).parent.parent))
from sop_deeplang.sandbox.excel_parser import ExcelParser_Sandbox

class DocxParser:
    """
    Parses .docx files and extracts sections with headings, text, and tables.
    """
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if self.file_path.suffix == '.doc':
            self.file_path = self._convert_doc_to_docx(self.file_path)
        
        self.doc = Document(str(self.file_path))
        self.sections = self._parse_sections()

    def _convert_doc_to_docx(self, doc_path: Path) -> Path:
        """Converts .doc to .docx using textutil on Mac."""
        docx_path = doc_path.with_suffix('.docx')
        # If docx already exists (e.g. from previous run), use it
        if docx_path.exists():
            return docx_path
            
        print(f"Converting {doc_path} to {docx_path}...")
        try:
            subprocess.run(['textutil', '-convert', 'docx', str(doc_path)], check=True)
            return docx_path
        except Exception as e:
            print(f"Error converting {doc_path}: {e}")
            return doc_path # Fallback, though likely to fail docx.Document()

    SPECIAL_HEADERS = [
        "验证报告", "验证方案", "GLP遵从性声明和签字页", "签字页",
        "质量保证声明", "目录", "附表目录", "附图目录", "缩略语表", "摘要"
    ]

    def _parse_sections(self) -> Dict[str, str]:
        """
        Parses the document into a dictionary of {Heading: MarkdownText}.
        """
        sections = {}
        current_heading = "Header/Title"
        current_content = []

        def flush():
            nonlocal current_heading, current_content
            if current_content:
                sections[current_heading] = "\n".join(current_content).strip()
            current_content = []

        # Iterate through paragraphs and tables
        for child in self.doc.element.body.iterchildren():
            # Check if it's a paragraph
            if child.tag.endswith('p'):
                para = [p for p in self.doc.paragraphs if p._element == child][0]
                text = para.text.strip()
                if not text:
                    continue
                
                # Check if it's a heading (Level 1-3) or a special keyword
                is_heading = para.style.name.startswith('Heading') or para.style.name == 'Title'
                # Special check for user-requested keywords that might not be styled as headings
                if not is_heading:
                    for sh in self.SPECIAL_HEADERS:
                        if text == sh or (len(text) < 20 and sh in text):
                            is_heading = True
                            break

                if is_heading:
                    flush()
                    current_heading = text
                else:
                    current_content.append(text)
            
            # Check if it's a table
            elif child.tag.endswith('tbl'):
                table = [t for t in self.doc.tables if t._element == child][0]
                md_table = self._table_to_markdown(table)
                current_content.append(md_table)

        flush()
        return sections

    def _table_to_markdown(self, table) -> str:
        """Converts a docx table to a Markdown table."""
        rows = []
        for row in table.rows:
            # Handle empty cells or merged cells gracefully
            rows.append([cell.text.replace('\n', '<br>').strip() for cell in row.cells])
        
        if not rows:
            return ""
        
        headers = rows[0]
        md = f"| {' | '.join(headers)} |\n"
        md += f"| {' | '.join(['---'] * len(headers))} |\n"
        for row in rows[1:]:
            md += f"| {' | '.join(row)} |\n"
        return md

def merge_sources(protocol_sections: Dict[str, str], report_sections: Dict[str, str]) -> str:
    """
    Merges Protocol and Report sections into a single Markdown string.
    Aligns specific terms between protocol and report.
    """
    # Mapping to standardize headings
    HEADER_MAPPING = {
        "验证方案": "验证报告",
        "签字页": "GLP遵从性声明和签字页"
    }
    
    # Apply mapping to protocol sections
    mapped_protocol = {}
    for h, content in protocol_sections.items():
        new_h = HEADER_MAPPING.get(h, h)
        if new_h in mapped_protocol:
            mapped_protocol[new_h] += "\n\n" + content
        else:
            mapped_protocol[new_h] = content
            
    # Apply mapping to report sections (just in case they use protocol terms)
    mapped_report = {}
    for h, content in report_sections.items():
        new_h = HEADER_MAPPING.get(h, h)
        if new_h in mapped_report:
            mapped_report[new_h] += "\n\n" + content
        else:
            mapped_report[new_h] = content

    all_headings = list(mapped_protocol.keys())
    # Add missing headings from report
    for h in mapped_report.keys():
        if h not in all_headings:
            all_headings.append(h)
    
    # Sort headings to keep special ones at top if they exist
    special_order = ["验证报告", "GLP遵从性声明和签字页", "质量保证声明", "目录", "附表目录", "附图目录", "缩略语表", "摘要"]
    
    ordered_headings = []
    for sh in special_order:
        if sh in all_headings:
            ordered_headings.append(sh)
            all_headings.remove(sh)
    
    # Keep "Header/Title" at the very top if it's still there
    if "Header/Title" in all_headings:
        ordered_headings.insert(0, "Header/Title")
        all_headings.remove("Header/Title")
        
    ordered_headings.extend(all_headings)

    md_output = "# Merged Protocol & Report Data\n\n"
    
    for heading in ordered_headings:
        md_output += f"## {heading}\n\n"
        
        # Protocol Content
        md_output += "### Protocol (方案)\n"
        md_output += mapped_protocol.get(heading, "无数据") + "\n\n"
        
        # Report Content
        md_output += "### Report (报告)\n"
        md_output += mapped_report.get(heading, "无数据") + "\n\n"
        
        md_output += "---\n\n"
        
    return md_output

def process_directory(dir_path: Path, output_root: Path):
    """Processes a single report directory."""
    print(f"Processing directory: {dir_path.name}")
    
    # Identify files and filter out temporary/hidden files
    protocol_files = [f for f in dir_path.glob("*方案*") if not f.name.startswith((".", ".~"))]
    report_files = [f for f in (list(dir_path.glob("*REPORT*")) + list(dir_path.glob("*报告*"))) if not f.name.startswith((".", ".~"))]
    excel_files = [f for f in dir_path.glob("*.xlsx") if not f.name.startswith((".", ".~"))]
    
    # Use the main files (avoid hidden files or variants if possible)
    protocol_path = protocol_files[0] if protocol_files else None
    report_path = report_files[0] if report_files else None
    excel_path = excel_files[0] if excel_files else None
    
    report_id = dir_path.name
    report_out_dir = output_root / report_id
    report_out_dir.mkdir(parents=True, exist_ok=True)
    
    # Process Word Docs
    protocol_sections = DocxParser(str(protocol_path)).sections if protocol_path else {}
    report_sections = DocxParser(str(report_path)).sections if report_path else {}
    
    merged_md = merge_sources(protocol_sections, report_sections)
    with open(report_out_dir / "merged_docs.md", "w", encoding="utf-8") as f:
        f.write(merged_md)
    
    # Process Excel
    if excel_path:
        excel_out_dir = report_out_dir / "excel_data"
        excel_out_dir.mkdir(exist_ok=True)
        try:
            parser = ExcelParser_Sandbox(str(excel_path))
            sheets_data = parser.parse_all_sheets()
            for sheet_name, content in sheets_data.items():
                safe_name = "".join([c if c.isalnum() else "_" for c in sheet_name])
                with open(excel_out_dir / f"{safe_name}.md", "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception as e:
            print(f"Error parsing Excel {excel_path}: {e}")

def main():
    base_dir = Path("original_docx/BV报告")
    output_root = Path("data_parsed")
    
    if not base_dir.exists():
        print(f"Source directory {base_dir} not found.")
        return

    for report_dir in base_dir.iterdir():
        if report_dir.is_dir() and not report_dir.name.startswith("."):
            process_directory(report_dir, output_root)

if __name__ == "__main__":
    main()
