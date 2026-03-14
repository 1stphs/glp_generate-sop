# 审计日志 (Audit Log)

记录 DeepAgent 系统每日的执行流水与进化轨迹。

## 目录结构
- `audit_log.md`: 本引导说明书。
- `audit_log_{YYYY-MM-DD}.json`: 按天生成的执行流水记录。

## JSON 架构示例
```json
[
  {
    "timestamp": "2026-03-14T15:10:00",
    "experiment_type": "LC-MS_MS验证项目",
    "version": "V1",
    "sop_id": "sop_20260314151000",
    "quality_assessment": {
      "is_passed": true,
      "score": 5.0
    }
  }
]
```
