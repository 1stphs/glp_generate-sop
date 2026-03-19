import os
import pandas as pd
from typing import Dict, List, Tuple, Optional

class ExcelParser_Sandbox:
    """
    Excel 解析沙盒，负责将复杂的 Excel 汇总表转换为结构化的 Markdown 内容。
    """
    def __init__(self, excel_path: str):
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file not found: {excel_path}")
        self.excel_path = excel_path
        self.xl = pd.ExcelFile(excel_path)
        self.parsed_data = {}

    def parse_all_sheets(self) -> Dict[str, str]:
        """
        解析所有 Sheet，返回 {SheetName: MarkdownContent} 字典。
        """
        for sheet_name in self.xl.sheet_names:
            self.parsed_data[sheet_name] = self.parse_sheet(sheet_name)
        return self.parsed_data

    def parse_sheet(self, sheet_name: str) -> str:
        """
        解析单个 Sheet，识别文本块和表格块。
        """
        df = self.xl.parse(sheet_name, header=None)
        # 移除全空行
        df = df.dropna(how='all')
        
        blocks = []
        current_block_type = None
        current_block_rows = []
        
        for _, row in df.iterrows():
            non_null_count = row.notna().sum()
            if non_null_count == 0:
                continue
            
            # 判断是文本还是表格：单列有值视为文本/标题，多列有值视为表格
            row_type = 'text' if non_null_count == 1 else 'table'
            
            if current_block_type is None:
                current_block_type = row_type
                current_block_rows.append(row)
            elif current_block_type == row_type:
                current_block_rows.append(row)
            else:
                blocks.append((current_block_type, pd.DataFrame(current_block_rows)))
                current_block_type = row_type
                current_block_rows = [row]
        
        if current_block_rows:
            blocks.append((current_block_type, pd.DataFrame(current_block_rows)))
            
        return self._blocks_to_markdown(blocks)

    def _blocks_to_markdown(self, blocks: List[Tuple[str, pd.DataFrame]]) -> str:
        md_output = ""
        for b_type, b_df in blocks:
            if b_type == 'text':
                for _, r in b_df.iterrows():
                    text_val = r.dropna().iloc[0]
                    md_output += f"{text_val}\n\n"
            else:
                md_output += self._to_md_table(b_df) + "\n\n"
        return md_output.strip()

    def _to_md_table(self, df: pd.DataFrame) -> str:
        df = df.dropna(axis=1, how='all').fillna("")
        if df.empty:
            return ""
        
        headers = [str(x).replace('\n', '<br>').strip() for x in df.iloc[0].tolist()]
        # 防止空表头导致 Markdown 渲染失败
        headers = [h if h != "" else f"Col_{i}" for i, h in enumerate(headers)]
        
        data_rows = df.iloc[1:].values.tolist()
        
        md = f"| {' | '.join(headers)} |\n"
        md += f"|{'|'.join(['---'] * len(headers))}|\n"
        for row in data_rows:
            row_str = [str(x).replace('\n', '<br>') for x in row]
            md += f"| {' | '.join(row_str)} |\n"
        return md

class TableMapper:
    """
    负责将 Excel Sheet 名称映射到 SOP 的具体章节名。
    """
    def __init__(self, mapping_config: Optional[Dict[str, List[str]]] = None):
        # 默认映射配置，后续可扩展为基于 LLM 的语义映射
        self.mapping_config = mapping_config or {
            "系统适用性": ["系统适用性", "System Suitability", "表1"],
            "精密度": ["精密度", "Precision", "表2", "表3", "表4"],
            "准确度": ["准确度", "Accuracy", "表2", "表3", "表4"],
            "残留": ["残留", "Carry-over", "Carryover", "表5", "残"],
            "特异性": ["特异性", "Specificity", "表6"],
            "稳定性": ["稳定性", "Stability", "表10", "表11", "表12", "温"],
            "基质效应": ["基质效应", "Matrix Effect", "表7"],
            "提取回收率": ["回收率", "Recovery", "表8"],
            "标准曲线": ["标准曲线", "Calibration", "校准", "表9"]
        }

    def map_sections(self, sheet_names: List[str]) -> Dict[str, List[str]]:
        """
        将输入的 sheet_names 映射到规范的章节名。
        返回 {SectionTitle: [SheetNames]} 字典。
        """
        result = {}
        for sheet in sheet_names:
            matched = False
            for section, keywords in self.mapping_config.items():
                if any(kw.lower() in sheet.lower() for kw in keywords):
                    if section not in result:
                        result[section] = []
                    result[section].append(sheet)
                    matched = True
                    break
            # 如果没匹配到，暂时归类为 "其他" 或保留原样
            if not matched:
                if "其他" not in result:
                    result["其他"] = []
                result["其他"].append(sheet)
        return result
