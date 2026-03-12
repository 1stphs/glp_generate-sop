"""
SOP 生成工作流 LangGraph 状态定义

V3 架构升级：
GlobalState 是整个多 Agent 系统的共享主状态，采用前端预解析的 JSON 作为数据源。
ChapterState 是每个独立并发的章节子图 (Chapter Sub-graph) 的局部状态。
"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict, List, Literal
import operator
from typing import Annotated


class ChapterState(TypedDict):
    """
    单章节子图 (Chapter Sub-graph) 的独立运行状态。
    作为 LangGraph Send API 的 Payload 被派发并在并发节点中流转。
    """
    project_id: NotRequired[str]
    """项目 ID，用于 OpenViking 工作区读写。"""

    section_id: NotRequired[Any]
    """章节唯一标识（通常是模板章节 id）。"""

    child_thread_id: NotRequired[str]
    """子图独立线程 ID，用于章节级 checkpoint/回放。"""

    section_title: str
    """章节名称，例如 '2.1 标准品'"""

    original_content: str
    """方案原始内容"""

    target_generate_content: str
    """目标报告内容（来自 report.json 的 generate_content）"""

    current_sop: NotRequired[str]
    """SOP Writer 生成的当前 SOP 步骤内容"""

    sop_type: NotRequired[Literal["simple_insert", "rule_template", "complex_composite"]]
    """SOP 类型：简单插入 / 规则+模板 / 复杂组合"""

    simulated_generate_content: NotRequired[str]
    """Simulator 根据 current_sop 盲测模拟执行出的虚构结果数据"""

    feedback: NotRequired[str]
    """Reviewer (校验器) 抛出的上一轮失败的详细比对驳回原因"""

    retry_count: int
    """重试计数器（不含首次执行）；最大重试次数为 2（总尝试次数为 3）"""

    is_passed: bool
    """Reviewer 判定当前章节是否通过核验"""

    status: Literal["RUNNING", "PASSED", "Need Human Review"]
    """章节处理状态"""

    extracted_data: NotRequired[dict[str, Any]]
    """上下文加载器读取的章节源数据快照。"""

    sse_summary: NotRequired[dict[str, Any]]
    """SSE 流式推送摘要，当前章节节点执行状态，供前端实时展示。"""


class GlobalState(TypedDict):
    """
    SOP 生成主图 (Main Graph) 完整状态。
    """

    # ---- 项目基础信息 ----
    project_id: str
    """项目唯一 ID，用于构建 OpenViking 工作区路径和报告追踪"""

    report_json_path: NotRequired[str]
    """兼容字段：当前固定读取项目内 mockData/report.json，此字段已不再作为外部输入源"""

    # ---- 工作流阶段 ----
    current_phase: NotRequired[str]
    """
    当前所处阶段：
    - "initialization"   项目初始化与读 JSON
    - "fan_out"          触发并发子图
    - "merge"            汇聚检查
    - "human_review"     人工兜底审核
    - "completed"        完成生成
    """

    # ---- 章节并发流转数据 ----
    # 使用 Annotated 和 operator.add 的原因是，由于各个并发的 Sub-graph 是并行结束的，
    # 它们将归约到完成列表中，这里指定以 extend 方式聚合 List。
    mapped_chapters: NotRequired[List[ChapterState]]
    """解析 report.json 后初始化好的所有待处理章节状态字典集合"""

    chapter_list: NotRequired[List[dict[str, Any]]]
    """API 直传章节数组（字段含 section_protocol / section_report）。"""

    completed_chapters: NotRequired[Annotated[List[ChapterState], operator.add]]
    """接收并发节点完成的回流合并数据池"""

    section_update_results: NotRequired[Annotated[List[dict[str, Any]], operator.add]]
    """章节生成完成后的逐章回写结果汇总。"""

    completed_chapters_output_path: NotRequired[str]
    """completed_chapters 落盘到本地 tests/output 的 JSON 路径"""

    final_document_path: NotRequired[str]
    """兼容保留字段：当前聚合节点不再导出 Word。"""

    # ---- 其他系统输出 ----
    human_decision: NotRequired[dict[str, Any]]
    """人工审核或中断干预指令"""

    error_log: NotRequired[Annotated[List[dict[str, Any]], operator.add]]
    """运行期间捕获的全局错误记录列"""

    sse_summary: NotRequired[dict[str, Any]]
    """SSE 流式推送摘要，当前主图节点执行状态，供前端实时展示。"""
