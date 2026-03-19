### **第一部分：核心准则**
* 本章节撰写必须严格遵守FDA 21 CFR Part 11/GLP法规，确保所有数据追溯至原始记录（Worksheets/峰面积数据），禁止主观臆断或未记录数据。
* 合规性判定基于协议（VP）中定义的接受标准：**98.0% ≤ 准确度（Accuracy）≤ 102.0%**，报告中必须明确呈现“Mean、SD、%RSD、n=6”并进行统计对比。
* 计算逻辑原子化：
  1. 从原始记录提取每个样品浓度（Nominal Concentration, e.g., 4.99, 49.95, 499.50 µg/mL）。
  2. 计算每个样品的回收率：**Recovery (%) = (Peak Area Response Factor × 100) / Nominal Concentration**，保留1位小数。
  3. 计算统计量：**Mean = 平均值（保留1位小数）**；**SD = 标准差（保留1位小数）**；**%RSD = (SD/Mean × 100)，保留1位小数**；**n=6**（六次重复）。
  4. 判定逻辑：若Mean在98.0%-102.0%范围内，则判定“符合”；否则“待优化”并说明偏差原因。
* 二元差异定位：静态文本直接复制VP（如“Accuracy and Precision Validation”标题、接受标准）；动态数据从Worksheets提取并计算。
* 分支逻辑：若不符合，添加“Deviation Summary”并追溯根因（如仪器波动），确保逻辑闭环。

### **第二部分：通用模板**
```
**{{Section_Title}}** (e.g., 3.4 Accuracy and Precision)

The accuracy and precision of the method were assessed by analyzing six replicates of QC samples at three concentration levels: Low ({{Low_Conc}} µg/mL), Medium ({{Med_Conc}} µg/mL), and High ({{High_Conc}} µg/mL). 

**Data Extraction Path**: 从Worksheets/峰面积数据提取六次重复的Peak Area Response Factor。

**计算步骤**:
1. Low QC: Recovery (%) = [{{Rep1_Low}}, {{Rep2_Low}}, ..., {{Rep6_Low}}] → Mean = {{Low_Mean}}%, SD = {{Low_SD}}%, %RSD = {{Low_RSD}}%, n=6
2. Med QC: Recovery (%) = [{{Rep1_Med}}, ..., {{Rep6_Med}}] → Mean = {{Med_Mean}}%, SD = {{Med_SD}}%, %RSD = {{Med_RSD}}%, n=6  
3. High QC: Recovery (%) = [{{Rep1_High}}, ..., {{Rep6_High}}] → Mean = {{High_Mean}}%, SD = {{High_SD}}%, %RSD = {{High_RSD}}%, n=6

**Table Insertion**: 插入计算结果表格（格式：浓度水平 | Mean(%) | SD(%) | %RSD(%) | n | 符合性）。

**判定语句**:
- Low QC: {{Low_Mean}}% ({{Low_RSD}}% RSD), {{Judgment_Low}} acceptance criteria of 98.0-102.0%.
- Med QC: {{Med_Mean}}% ({{Med_RSD}}% RSD), {{Judgment_Med}} acceptance criteria of 98.0-102.0%.  
- High QC: {{High_Mean}}% ({{High_RSD}}% RSD), {{Judgment_High}} acceptance criteria of 98.0-102.0%.

**Overall Conclusion**: The method demonstrates acceptable accuracy and precision across all levels, meeting GLP requirements. [若任何水平不符合：Deviation: {{Deviation_Desc}}，根因追溯至{{Root_Cause}}。]
```

### **第三部分：报告示例**
**3.4 Accuracy and Precision**

The accuracy and precision of the method were assessed by analyzing six replicates of QC samples at three concentration levels: Low (4.99 µg/mL), Medium (49.95 µg/mL), and High (499.50 µg/mL). 

| Concentration Level | Mean Accuracy (%) | SD (%) | %RSD (%) | n | Conformance |
|---------------------|-------------------|--------|----------|---|-------------|
| Low QC (4.99 µg/mL) | 99.8             | 1.2   | 1.2     | 6 | Yes        |
| Med QC (49.95 µg/mL)| 100.5            | 1.0   | 1.0     | 6 | Yes        |
| High QC (499.50 µg/mL)| 99.2           | 1.4   | 1.4     | 6 | Yes        |

- Low QC: 99.8% (1.2% RSD), meets acceptance criteria of 98.0-102.0%.
- Med QC: 100.5% (1.0% RSD), meets acceptance criteria of 98.0-102.0%.
- High QC: 99.2% (1.4% RSD), meets acceptance criteria of 98.0-102.0%.

**Overall Conclusion**: The method demonstrates acceptable accuracy and precision across all levels, meeting GLP requirements. All data traceable to Worksheets/峰面积数据.