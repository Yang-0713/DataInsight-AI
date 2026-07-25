# API 文档

DataInsight AI 后端基于 FastAPI。默认 API 根地址为：

```text
http://127.0.0.1:8000/api
```

运行后端后，可通过以下地址查看自动生成的规范：

- Swagger UI：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>
- OpenAPI JSON：<http://127.0.0.1:8000/openapi.json>

本文档描述第七阶段公开接口。接口的 Pydantic 校验规则和 OpenAPI 规范是最终依据。

## 1. 通用约定

### 内容类型

- JSON 请求：`Content-Type: application/json`
- 文件上传：`multipart/form-data`
- HTML 报告下载：`text/html`

### 身份认证

除健康检查、注册和登录外，所有接口都需要 JWT Bearer 令牌：

```http
Authorization: Bearer <access_token>
```

访问令牌由 `/api/auth/login` 返回，默认有效期为 60 分钟。

### 时间格式

响应中的时间使用 ISO 8601，例如：

```text
2026-07-25T14:30:00
```

### 错误格式

业务错误统一使用 FastAPI 的 `detail` 字段：

```json
{
  "detail": "数据集不存在"
}
```

请求字段校验失败时返回 `422`，并包含字段位置和校验原因。

### 常见状态码

| 状态码 | 含义 |
| --- | --- |
| `200` | 查询或操作成功 |
| `201` | 资源创建成功 |
| `204` | 删除成功，无响应体 |
| `401` | 未登录、令牌无效或已过期 |
| `404` | 资源不存在或不属于当前用户 |
| `409` | 用户名或邮箱冲突 |
| `413` | 上传文件超过限制 |
| `422` | 请求或数据不满足分析要求 |
| `502` | 上游 AI 服务失败或报告格式无效 |
| `503` | AI 服务尚未配置 |

为避免泄露资源是否属于其他用户，访问其他用户的数据集、分析结果或报告时同样返回 `404`。

## 2. 健康检查

### `GET /api/health`

不需要身份认证。

响应：

```json
{
  "status": "ok",
  "service": "DataInsight AI API"
}
```

## 3. 身份认证

### `POST /api/auth/register`

创建普通用户。

请求：

```json
{
  "username": "analyst_01",
  "email": "analyst@example.com",
  "password": "DataInsight123!"
}
```

规则：

- `username`：3–50 个字符，只允许字母、数字和下划线
- `email`：合法邮箱地址
- `password`：8–128 个字符

成功状态：`201`

响应：

```json
{
  "id": 1,
  "username": "analyst_01",
  "email": "analyst@example.com",
  "role": "USER",
  "created_at": "2026-07-25T14:30:00"
}
```

### `POST /api/auth/login`

使用用户名或邮箱登录。

请求：

```json
{
  "identity": "analyst@example.com",
  "password": "DataInsight123!"
}
```

响应：

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### `GET /api/auth/me`

返回当前用户信息。需要 Bearer 令牌。

## 4. 数据集

### `POST /api/datasets/upload`

上传 CSV 并提取元数据。表单字段名必须为 `file`。

```bash
curl -X POST http://127.0.0.1:8000/api/datasets/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@examples/datasets/retail_sales.csv"
```

成功状态：`201`

响应：

```json
{
  "id": 1,
  "filename": "retail_sales.csv",
  "rows": 40,
  "columns": 11,
  "created_at": "2026-07-25T14:35:00"
}
```

限制：

- 仅支持 `.csv`
- 默认最大 50 MB
- 支持 UTF-8、UTF-8 BOM 和 GB18030
- 文件存储路径不会通过 API 返回

### `GET /api/datasets`

返回当前用户的数据集，按上传时间倒序排列。

### `GET /api/datasets/{dataset_id}`

返回当前用户指定数据集的元数据。

### `DELETE /api/datasets/{dataset_id}`

删除数据集元数据、本地 CSV、关联分析结果和已生成报告。

成功状态：`204`

## 5. 自动化 EDA

### `POST /api/analysis/{dataset_id}`

运行数据画像、描述性统计和可视化构建。

成功状态：`201`

响应结构：

```json
{
  "id": 10,
  "dataset_id": 1,
  "analysis_type": "EDA",
  "result_json": {
    "dataset": {
      "id": 1,
      "filename": "retail_sales.csv",
      "rows": 40,
      "columns": 11
    },
    "profile": {
      "rows": 40,
      "columns": 11,
      "duplicate_rows": 0,
      "missing_cells": 2,
      "missing_percentage": 0.45,
      "column_profiles": []
    },
    "statistics": {
      "numerical": [],
      "categorical": []
    },
    "visualizations": []
  },
  "created_at": "2026-07-25T14:40:00"
}
```

`visualizations` 中每项都包含 ECharts `option`，前端可以直接渲染。

### `GET /api/results/{result_id}`

读取当前用户拥有的任意已保存分析结果，包括 `EDA`、`ML`、`AI_CHAT` 和 `AI_REPORT`。

## 6. 机器学习

### `GET /api/ml/{dataset_id}/features`

获取数值字段和推荐特征。

响应：

```json
{
  "dataset_id": 1,
  "rows": 40,
  "numeric_features": [
    "orders",
    "units",
    "revenue",
    "cost",
    "discount_rate",
    "satisfaction_score"
  ],
  "recommended_features": [
    "orders",
    "units",
    "revenue",
    "cost",
    "discount_rate",
    "satisfaction_score"
  ],
  "max_rows": 5000
}
```

### `POST /api/ml/{dataset_id}`

运行数据预处理、PCA、Isolation Forest 和 Local Outlier Factor。

请求：

```json
{
  "features": ["orders", "units", "revenue", "cost"],
  "contamination": 0.05,
  "lof_neighbors": 10
}
```

字段规则：

| 字段 | 是否必填 | 规则 |
| --- | --- | --- |
| `features` | 否 | 不传时自动选择；字段不能重复 |
| `contamination` | 否 | 大于 `0` 且不超过 `0.5`，默认 `0.05` |
| `lof_neighbors` | 否 | `2`–`200`，默认 `20` |

成功状态：`201`

结果以 `ML` 类型保存。`result_json` 包含：

- `preprocessing`：特征、中位数补全数量和标准化方式
- `pca`：主成分载荷、解释方差和二维投影
- `isolation_forest`：异常数量、分数和标签
- `lof`：邻居数量、异常数量、分数和标签

## 7. AI 数据分析师

### `GET /api/ai/status`

返回 AI 配置状态，不会返回密钥。

```json
{
  "configured": true,
  "provider": "openai-compatible",
  "model": "gpt-5.6-terra",
  "api_mode": "responses"
}
```

### `POST /api/ai/chat`

基于指定数据集的最新聚合分析摘要进行问答。没有 EDA 结果时，系统会先自动运行 EDA。

请求：

```json
{
  "dataset_id": 1,
  "message": "这个数据集有哪些值得优先处理的数据质量问题？",
  "history": [
    {
      "role": "user",
      "content": "先概括数据集。"
    },
    {
      "role": "assistant",
      "content": "数据包含销售、成本和满意度等指标。"
    }
  ]
}
```

规则：

- `message`：1–4,000 个字符
- `history`：最多接受 30 条；后端默认只使用最近 12 条
- 历史消息角色只能是 `user` 或 `assistant`

响应：

```json
{
  "result_id": 12,
  "dataset_id": 1,
  "answer": "结论：应先处理缺失值并复核高异常分数样本。",
  "provider": "openai-compatible",
  "model": "gpt-5.6-terra",
  "created_at": "2026-07-25T14:45:00"
}
```

AI 服务接收聚合统计、分类高频值、图表说明以及可选的异常样本编号，不接收完整原始 CSV 或服务器文件路径。

## 8. AI 报告

### `POST /api/reports/{dataset_id}`

生成 HTML 综合报告并保存至本地 `reports/用户ID/`。

成功状态：`201`

响应：

```json
{
  "id": 13,
  "dataset_id": 1,
  "title": "retail_sales.csv 综合分析报告",
  "summary": "该数据集记录了多个地区和渠道的零售经营指标。",
  "findings": ["收入主要集中在常规区间"],
  "possible_problems": ["部分字段存在缺失值"],
  "recommendations": ["复核缺失记录和高分异常样本"],
  "download_url": "/api/reports/13/download",
  "provider": "openai-compatible",
  "model": "gpt-5.6-terra",
  "created_at": "2026-07-25T14:50:00"
}
```

### `GET /api/reports`

列出当前用户生成的全部报告。

### `GET /api/reports/{result_id}/download`

下载 HTML 报告。浏览器直接打开 URL 时也必须携带 Bearer 令牌；前端通过 Axios Blob 下载处理认证。

## 9. 完整调用流程

1. `POST /api/auth/register`
2. `POST /api/auth/login` 并保存 `access_token`
3. `POST /api/datasets/upload`
4. `POST /api/analysis/{dataset_id}`
5. 可选：`POST /api/ml/{dataset_id}`
6. 可选：`POST /api/ai/chat`
7. 可选：`POST /api/reports/{dataset_id}`

PowerShell 登录并保存令牌示例：

```powershell
$login = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/auth/login `
  -ContentType application/json `
  -Body '{"identity":"analyst@example.com","password":"DataInsight123!"}'

$headers = @{ Authorization = "Bearer $($login.access_token)" }
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/datasets -Headers $headers
```

请勿把真实访问令牌、数据库密码或 AI 密钥提交到仓库。
