第一部分：核心准则
- 定义必须反映的“静态文本”与“动态数据”：
  - 静态文本（直接可复用，不需计算）：遵从性/合规性声明段落的原文、签字页原文。
  - 动态数据（必须从原始记录或协议中提取并以占位符表示）：{{Validation_Study_Number}}、{{Validation_Study_Title}}、{{Regulation_List}}、{{CoA_Source}}（含机构名与GLP状态）、{{Signatory_List}}（姓名、职务、签名日期）。
- 合规性表述必须与原始报告优先一致；不得擅自添加或删除“是否在本机构完成”“是否影响质量完整性”等结论性断言，若原始材料缺失则出具明显的偏差/说明段。
- 第三方 CoA 必须明确来源与是否在 GLP 条件下完成；若为非 GLP，应在报告中明示，不得以模糊措辞替代（若协议/报告已声明，则直接复用）。
- 签字页必须列出签署人姓名与职务；签名/签字日期应来自原始签字页扫描件或签名记录；若仅有打印姓名或电子声明，须标注“签名/日期记录不可用”并引用原始证据位置。
- 一致性校验规则：报告中列示的试验编号/标题/遵从性列表/CoA 信息/签署人，必须逐项与方案（Protocol）或原始签字页核对；若不一致，生成不一致项表并在报告中加入“差异说明”段。
- 变通与禁止项：严禁自行声明第三方 CoA 为 GLP，严禁伪造签名或补填未有依据的签名日期；必要时引用原始附件编号与位置，保全可追溯性。

第二部分：通用模板
- 输入（必备文档/字段）：
  1. Protocol 文档（用于核对预期签署人列表与机构信息）
  2. Report 主文档（优先使用其已有的合规段落与签字页）
  3. 原始签字页扫描件或签名记录（用于验证签名与日期）
  4. CoA 附件或供应商证书（用于提取 CoA_Source 与 GLP 状态）
- 提取指令（顺序化、可自动执行）：
  1. 从 Report 提取：{{Validation_Study_Number}}；若缺失则从 Protocol 提取并标注来源。
  2. 从 Report 提取：{{Validation_Study_Title}}（全称）；若存在中/英双语，保留并并列。
  3. 从 Report 提取：合规性段落原文并解析为{{Regulation_List}}（数组形式，每项为一个法规条目）；若 Report 无此段，则从 Protocol 提取并标注“来源：Protocol”。
  4. 从 Report 与附件提取：{{CoA_Source}}（字段：机构名称、是否GLP条件下完成（True/False/未知）、附件编号）；若 Report 指明“非 GLP”，设置 GLP_flag=False。
  5. 从 Protocol 与签字页扫描件提取并生成{{Signatory_List}}数组：每项包含 {Name, Role, Signature_Present (Y/N), Signature_Date (if present), Source_Doc}。
- 校验规则（自动判定逻辑）：
  1. 若 Report 中的 {{Validation_Study_Number}} 与 Protocol 不一致，记录不一致项：{字段, Protocol_value, Report_value} 并在报告中插入差异说明段。
  2. 若某 CoA 在附件中标注为“非 GLP”，则应在合规段落后附加明确句式（见输出模板）；若 CoA 状态未知，插入“CoA 状态未明，请见附件 X”并标注待补充。
  3. 若签字页中签署人名单与 Protocol 中不符，生成签署人差异表并要求确认/更正来源文档。
- 组装输出段落模板（占位符形式，可直接替换）：
  1. 标题与编号：
     {{Validation_Study_Number}}  
     {{Validation_Study_Title}}
  2. 合规性声明（若 Report 中已有原文，优先引用原文；若无，使用下述占位模板）：
     「本验证研究在本试验单位按验证方案{{Protocol_ID_or_Version}}、本机构相关 SOP 及下列规范开展：{{Regulation_List}}。试验期间未出现影响试验质量和完整性的因素。」
  3. CoA 说明（必须明确机构与 GLP 状态）：
     - 若 CoA 为非 GLP：「待测物 {{Analyte_Name}} 的 CoA 由 {{CoA_Source.Institution}} 在非‑GLP 条件下完成；内标 {{Internal_Std_Name}} 的 CoA 由 {{CoA_Source_2.Institution}} 在非‑GLP 条件下完成（见附件 {{CoA_Attachments}}）。」
     - 若 CoA 为 GLP：相应替换为“在 GLP 条件下完成”并引用证据。
     - 若 CoA 状态未知：使用占位「CoA 状态未明确」并引用附件位置。
  4. 签字页模板（每个签署人为一行，占位）：
     __________________________________________________  
     {{Signatory_List[0].Name}}  {{Signatory_List[0].Role}}  （签名：{{Y/N}}，签字日期：{{Signature_Date_or_NA}}）  
     {{Signatory_List[1].Name}}  {{Signatory_List[1].Role}}  （签名：{{Y/N}}，签字日期：{{Signature_Date_or_NA}}）  
     （按需继续）
- 输出后校验（需生成的核对清单）：
  1. 是否包含试验编号与全称？（Y/N）
  2. 是否包含并列出法规清单？（Y/N）
  3. 是否明确 CoA 来源并标注 GLP 状态？（Y/N）
  4. 签署人名单是否与原始签字页一致？（Y/N）
  5. 若有任一为 N，生成“差异说明”并附原始证据路径。
- 分支逻辑要点：
  - 若 Report 已含合规段且与 Protocol 对应字段一致，直接复用；否则在报告中添加“差异说明”段并引用证据。
  - 若签字页仅列名无签名或日期，输出时必须标注“签名/日期记录不可用”，并指示追溯动作（例如请求原始签字页或电子签名证据）。

第三部分：报告示例
- 验证试验编号与名称（直接取自报告）：
  Validation Study Number：NS25315BV01  
  Validation Study Title：LC-MS/MS方法测定SD大鼠EDTA-K2血浆样品中BPR-30160639（游离型）反义链和正义链浓度的生物分析方法学验证
- 合规性段落（报告原文示例）：
  本验证所有阶段均在本机构完成，遵从本验证方案及变更、本机构相关 SOP 及下列管理规范。试验期间未出现影响试验质量和完整性的因素。

  ■ NMPA (2017), 药物非临床研究质量管理规范。  
  ■ US FDA (1978). 21CFR Part 58, Good Laboratory Practice for Nonclinical Laboratory Studies.  
  ■ OECD (1998). OECD Series on Principles of Good Laboratory Practice and Compliance Monitoring Number 1: OECD Principles of Good Laboratory Practice.
- CoA 说明示例（报告原文）：
  待测物 BPR-30160639 标准品的 CoA 由 上海兆维生物工程有限公司 在 非 GLP 条件下完成；内标 Vutrisiran 标准品 CoA 由 成都倍特药业股份有限公司 在 非 GLP 条件下完成。
- 签字页示例（报告摘录）：
  __________________________________________________  
  钱哲元 (Qian Zhe Yuan) 验证负责人 (Validation Study Director)

（使用说明：将以上示例段落作为最终报告中该章节的参考排版与用语风格；自动化生成时以通用模板中的占位符替换对应提取值，并按“输出后校验”清单逐项确认。）