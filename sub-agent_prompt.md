按chapter来写：

## 一、writer

输入：{
    protocol_content_{chapter_id}:
    report_content_{chapter_id}:
}

输出：{
    {chapter_id}_SOP_version:（每调用一次 version + 1 ）
    {chapter_id}_SOP_id:
    SOP:
}

## 二、simulator

输入：{
    {chapter_id}_SOP_version:
    SOP: (from writer)
}

输出：{
    {chapter_id}_SOP_version:
    sim_generation_report_content_{chapter_id}: 
}

## 三、reviewer

输入：{
    {chapter_id}_SOP_version:
    sim_generation_report_content_{chapter_id}: 
    report_content_{chapter_id}:
}

标准：{

    ## Skill: SOP Evaluator

    ### Goal
    Evaluate SOP quality.

    多维打分用哪些指标？？？

    ### Rubric
    1 Structure
    2 Rule compliance
    3 Operability
    4 Hallucination risk

    ### Scoring
    Each dimension 1-5.

    ### Pass Threshold
    4.5
}

指标：{
    Compliance / 合规性：
        保证 SOP 符合法规和内部标准
        防止法律或实验室规程风险

    Operability / 可操作性：
        保证实验可执行性
        步骤完整、参数合理

    Accuracy / Validity / 准确性：
        模拟结果和实际目标对比
        用于发现 Writer 或 SOP 的偏差

    Clarity / 可读性：
        帮助实验人员快速理解 SOP
        防止逻辑混乱导致错误操作

    Data Plausibility / 防幻觉：
        确保生成内容中没有虚假或不合理数据
        对 AI 生成内容非常关键

    Overall / 综合评分：
        按权重汇总各项指标
        可作为 Reviewer 最终判断参考
}

后面去更新 Rubric、Threshold

输出：{
    {chapter_id}_SOP_version:
    feedback: 反馈
    issues: 原因事件
    suggestion: 建议
}

## 四、reflector

输入：
输出：

## 五、curator

输入：
输出：
