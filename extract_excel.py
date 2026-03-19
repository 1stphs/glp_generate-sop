import os
import pandas as pd

excel_path = "/Users/pangshasha/Documents/github/glp_generate-sop/original_docx/BV报告/NS25318BV01/Qced NS25318BV01二次数据汇总@20250916（1-6）.xlsx"
out_dir = "/Users/pangshasha/Documents/github/glp_generate-sop/original_docx/BV报告/NS25318BV01/parsed_excel_markdowns"

os.makedirs(out_dir, exist_ok=True)

print(f"Loading '{excel_path}'...")
xl = pd.ExcelFile(excel_path)

def to_md_table(df):
    df = df.dropna(axis=1, how='all')
    if df.empty:
        return ""
    df = df.fillna("")
    
    headers = [str(x).replace('\n', '<br>') for x in df.iloc[0].tolist()]
    
    # Ensure header isn't completely empty, which breaks Markdown
    headers = [h if str(h).strip() != "" else f"Col_{i}" for i, h in enumerate(headers)]
    
    data_rows = df.iloc[1:].values.tolist()
    
    md = f"| {' | '.join(headers)} |\n"
    md += f"|{'|'.join(['---'] * len(headers))}|\n"
    for row in data_rows:
        row_str = [str(x).replace('\n', '<br>') for x in row]
        md += f"| {' | '.join(row_str)} |\n"
    return md

for sheet_name in xl.sheet_names:
    print(f"Processing sheet: {sheet_name}")
    df = xl.parse(sheet_name, header=None)
    
    # Drop rows that are completely NaN
    df = df.dropna(how='all')
    
    blocks = []
    current_block_type = None
    current_block_rows = []
    
    for idx, row in df.iterrows():
        non_null_count = row.notna().sum()
        
        if non_null_count == 0:
            continue
            
        elif non_null_count == 1:
            row_type = 'text'
        else:
            row_type = 'table'
            
        if current_block_type is None:
            current_block_type = row_type
            current_block_rows.append(row)
        elif current_block_type == row_type:
            current_block_rows.append(row)
        else:
            # Type changed, save current block
            blocks.append((current_block_type, pd.DataFrame(current_block_rows)))
            # Start new block
            current_block_type = row_type
            current_block_rows = [row]
            
    # Add the last block
    if current_block_rows:
        blocks.append((current_block_type, pd.DataFrame(current_block_rows)))
        
    # Write to Markdown file
    safe_sheet_name = sheet_name.replace("/", "_").replace("\\", "_")
    md_file_path = os.path.join(out_dir, f"{safe_sheet_name}.md")
    
    with open(md_file_path, "w", encoding="utf-8") as f:
        f.write(f"# {sheet_name}\n\n")
        
        for b_type, b_df in blocks:
            if b_type == 'text':
                for _, r in b_df.iterrows():
                    # Find the single non-null value
                    text_val = r.dropna().iloc[0]
                    f.write(f"{text_val}\n\n")
            else:
                md_table = to_md_table(b_df)
                f.write(md_table)
                f.write("\n\n")
                
print(f"Extraction complete! Files saved in: {out_dir}")
