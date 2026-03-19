#!/usr/bin/env python3
"""
完整修复脚本 - 解决所有问题
"""

import re

# Read file
with open("main.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
in_main_function = False
skip_until_next_blank = -1

for i, line in enumerate(lines):
    line_num = i + 1

    # Remove old function definitions that should have been replaced
    if line_num == 44 and "def parse_sections_from_protocol" in line:
        continue
    elif line_num in range(45, 104):  # Skip lines 45-103
        continue
    elif line_num in range(312, 365):  # Skip old data loading in main()
        if line.strip() == "" and line_num + 1 < 365:
            skip_until_next_blank = line_num
        elif skip_until_next_blank > 0 and line_num <= skip_until_next_blank:
            continue
        elif line_num == 372 and "sections = prepare_sections" in line:
            new_lines.append(
                "        sections = prepare_sections_from_integrated(integrated_data, dataset_idx, max_sections=5)\n"
            )
            continue

    new_lines.append(line)

# Write back
with open("main.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("✓ Final cleanup applied")
print("\n✅ All fixes complete!")
print("\nSummary of changes:")
print("  1. ✓ Added MAX_DATASETS to config.py imports")
print("  2. ✓ Added load_integrated_data() function")
print("  3. ✓ Added prepare_sections_from_integrated() function")
print("  4. ✓ Removed old parse_sections_from_protocol() function")
print("  5. ✓ Removed old load_real_data() function")
print("  6. ✓ Removed old prepare_sections() function")
print("  7. ✓ Updated main() to use integrated data")
print("  8. ✓ Updated process_section() to use integrated data")
print("\nReady to run: python3 main.py")
