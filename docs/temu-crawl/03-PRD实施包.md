# Temu 一键刷新爬取 — PRD 实施包

## 里程碑

| 阶段 | 内容 | 状态 |
|------|------|------|
| P0 | Java 任务表 + CrawlService + API + Python `--json` | 完成 |
| P1 | Vue 刷新按钮 + 轮询 | 完成 |
| P2 | V4 唯一约束修复、部署文档、测试验证 | 完成 |

## API 契约

### POST `/api/temu/crawl`

请求体（可选）：

```json
{ "report_time": "2026-07-06", "seed": true }
```

响应 202：

```json
{ "code": 0, "data": { "job_id": "uuid", "status": "pending" } }
```

响应 409：同租户已有任务进行中。

### GET `/api/temu/crawl/{jobId}`

```json
{
  "code": 0,
  "data": {
    "job_id": "uuid",
    "status": "success",
    "rows_count": 8,
    "report_time": "2026-07-06"
  }
}
```

## 验收标准

- [x] Boss 点刷新，seed 模式 <10s 成功
- [x] 员工 `liting@yituo-outdoor.com` 可触发
- [x] 任务状态 pending → running → success
- [x] 爬取后 operational 数据可读取

## 运维

1. 每租户首次：`py login.py --tenant-id N`
2. 线上 Java 需能执行宿主机 Python，挂载 `backend/python`、`.temu-browser-profile/`、`crosshub.db`
3. 生产 `CROSSHUB_PYTHON=python3`，`allow-seed: false`
