# 安装与运行指南

本文档介绍如何在本地安装并运行 DataInsight AI。项目采用 Vue 3、FastAPI 和 MySQL，不依赖 Docker。

## 1. 环境要求

| 组件 | 推荐版本 | 用途 |
| --- | --- | --- |
| Python | 3.10.x | 后端、数据分析和机器学习 |
| Conda | Miniconda 或 Anaconda | 管理 `pythonProject` 虚拟环境 |
| MySQL | 8.0+ | 保存用户、数据集元数据和分析结果 |
| Node.js | 20+ | 构建前端 |
| npm | 10+ | 安装前端依赖 |
| Git | 2.40+ | 获取代码和参与开发 |

Windows 是当前主要开发环境，macOS 和 Linux 也可以按照相同目录结构运行。

## 2. 获取代码

```powershell
git clone https://github.com/Yang-0713/DataInsight-AI.git
cd DataInsight-AI
```

如果你正在检出尚未合并的开发分支，请把分支名替换成对应名称：

```powershell
git switch main
```

## 3. 创建 Python 3.10 环境

项目统一使用名为 `pythonProject` 的 Conda 环境：

```powershell
conda create -n pythonProject python=3.10 -y
conda activate pythonProject
python --version
```

预期输出为 Python 3.10.x。

安装后端依赖：

```powershell
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m pip check
```

如果不想激活 Conda 环境，也可以通过 Conda 直接在指定环境中运行：

```powershell
conda run -n pythonProject python -m pip install -r backend/requirements.txt
```

## 4. 初始化 MySQL

确认 MySQL 服务已经启动，然后从项目根目录执行：

```powershell
mysql -u root -p --execute="source database/init_db.sql"
```

命令会提示输入密码。不要把数据库密码写入命令、脚本或 Git 提交。

完整初始化脚本会创建：

- `datainsight_ai` 数据库
- `users` 表
- `datasets` 表
- `analysis_results` 表

如果从旧阶段升级，可按顺序执行缺失的迁移：

```powershell
mysql -u root -p --execute="source database/migrations/003_create_datasets.sql"
mysql -u root -p --execute="source database/migrations/004_create_analysis_results.sql"
```

第五至第七阶段不需要新的数据库迁移。

## 5. 配置后端

复制环境变量模板：

```powershell
Copy-Item backend/.env.example backend/.env
```

macOS 或 Linux：

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，至少填写 MySQL 密码和 JWT 密钥：

```env
DATAINSIGHT_ENVIRONMENT=development
DATAINSIGHT_DEBUG=true

DATAINSIGHT_MYSQL_HOST=127.0.0.1
DATAINSIGHT_MYSQL_PORT=3306
DATAINSIGHT_MYSQL_USER=root
DATAINSIGHT_MYSQL_PASSWORD=your-password
DATAINSIGHT_MYSQL_DATABASE=datainsight_ai

DATAINSIGHT_JWT_SECRET_KEY=replace-with-a-random-secret-of-at-least-32-characters
```

PowerShell 可以生成随机 JWT 密钥：

```powershell
[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

### 可选：配置 AI 服务

不配置 AI 密钥时，认证、数据集、EDA 和机器学习功能仍然可用。

```env
DATAINSIGHT_OPENAI_API_KEY=your-api-key
DATAINSIGHT_OPENAI_BASE_URL=https://api.openai.com/v1
DATAINSIGHT_OPENAI_MODEL=gpt-5.6-terra
DATAINSIGHT_OPENAI_API_MODE=responses
DATAINSIGHT_OPENAI_REASONING_EFFORT=medium
```

接入本地或第三方 OpenAI 兼容服务时，可修改 `DATAINSIGHT_OPENAI_BASE_URL`。如果服务不支持 Responses API，可将 `DATAINSIGHT_OPENAI_API_MODE` 改为 `chat_completions`。

## 6. 启动后端

环境变量文件位于 `backend/`，因此从该目录启动：

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

验证服务：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

预期响应：

```json
{
  "status": "ok",
  "service": "DataInsight AI API"
}
```

常用地址：

- API 根地址：<http://127.0.0.1:8000/api>
- Swagger UI：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>
- OpenAPI JSON：<http://127.0.0.1:8000/openapi.json>

## 7. 启动前端

新开一个终端窗口：

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

浏览器访问 <http://127.0.0.1:5173>。开发服务器会把 `/api` 请求代理到 `http://127.0.0.1:8000`。

如果前后端部署在不同地址，请修改 `frontend/.env`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## 8. 使用示例数据

注册并登录后，在“数据集”页面上传：

```text
examples/datasets/retail_sales.csv
```

该数据集为合成数据，包含日期、地区、渠道、数值指标、缺失值和少量异常记录，可用于体验 EDA、PCA、Isolation Forest、LOF、AI 问答和报告生成。

## 9. 运行验证

后端：

```powershell
cd DataInsight-AI
conda run -n pythonProject python -m pytest -q
```

前端：

```powershell
cd frontend
npm run type-check
npm run build
```

## 10. 常见问题

### 后端启动时提示缺少 `jwt_secret_key`

确认 `backend/.env` 存在，并且从 `backend/` 目录启动 Uvicorn。JWT 密钥必须至少包含 32 个字符。

### 无法连接 MySQL

检查 MySQL 服务、端口、用户名、密码和数据库名称。也可以先执行：

```powershell
mysql -u root -p -e "SELECT VERSION();"
```

### 上传 CSV 后提示格式错误

系统支持 UTF-8、UTF-8 BOM 和 GB18030。确认文件扩展名为 `.csv`、表头非空且各行列数一致。

### AI 接口返回 503

这表示未设置有效的 `DATAINSIGHT_OPENAI_API_KEY`。补充配置并重启后端。

### AI 接口返回 502

检查 API 密钥、服务地址、模型名称、网络连接和 API 模式。OpenAI 兼容服务如果不支持 Responses API，应切换为 `chat_completions`。

### 机器学习分析内存占用过高

默认最多分析 5,000 行。可以先抽样数据，或降低 `DATAINSIGHT_MAX_ML_ROWS`，避免 LOF 计算消耗过多内存。

### 端口被占用

调整 Uvicorn 或 Vite 端口，并同步更新前端 API 地址或代理配置。
