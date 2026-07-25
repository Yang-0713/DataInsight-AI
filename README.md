# DataInsight AI

DataInsight AI 是一个开源的 AI 自动化数据分析平台，旨在帮助用户上传数据集、检查数据质量、完成统计分析与数据可视化、检测异常样本，并生成由 AI 辅助的分析结论和报告。

> 当前进度：**第一阶段——项目初始化**

第一阶段已经完成 Vue 3 前端、FastAPI 后端、MySQL 连接配置和基础项目结构。用户认证、数据集上传、自动化分析、机器学习和 AI 分析等功能将在后续阶段逐步实现。

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Element Plus、Pinia、Axios、ECharts、Tailwind CSS
- 后端：Python、FastAPI、SQLAlchemy、PyMySQL、Pydantic Settings
- 数据库：本地 MySQL 8+

## 环境要求

- Node.js 20+
- npm 10+
- `pythonProject` Conda 虚拟环境（当前为 Python 3.10.12）
- MySQL 8+

本项目无需安装 Docker。

## 1. 初始化 MySQL 数据库

登录本地 MySQL 服务后，在项目根目录执行：

```sql
SOURCE database/init_db.sql;
```

也可以在终端中执行：

```bash
mysql -u root -p < database/init_db.sql
```

该脚本会创建名为 `datainsight_ai` 的数据库。用户表及其他业务表将在对应的后续开发阶段通过数据库迁移添加。

## 2. 启动后端

后续开发统一使用以下 Conda 环境：

```text
D:\anaconda\envs\pythonProject
```

打开 PowerShell，激活环境并进入后端目录：

```powershell
conda activate pythonProject
cd D:\new__platform\backend
```

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

复制环境变量示例文件：

```powershell
Copy-Item .env.example .env
```

打开 `.env`，根据本机 MySQL 配置修改用户名、密码、端口和数据库名称，然后启动服务：

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

常用地址：

- API 根地址：<http://127.0.0.1:8000/api>
- 健康检查：<http://127.0.0.1:8000/api/health>
- API 文档：<http://127.0.0.1:8000/docs>

如果当前终端无法使用 `conda activate`，也可以直接通过该环境的 Python 运行：

```powershell
D:\anaconda\envs\pythonProject\python.exe -m pip install -r requirements.txt
D:\anaconda\envs\pythonProject\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 3. 启动前端

打开另一个 PowerShell 窗口：

```powershell
cd D:\new__platform\frontend
npm install
```

复制前端环境变量示例文件：

```powershell
Copy-Item .env.example .env
```

启动 Vite 开发服务器：

```powershell
npm run dev
```

浏览器访问 <http://127.0.0.1:5173>。开发环境下，Vite 会将 `/api` 请求代理到运行在 `http://127.0.0.1:8000` 的 FastAPI 服务。

## 项目结构

```text
DataInsight-AI/
├── frontend/                 Vue 3 前端项目
│   └── src/
│       ├── api/              HTTP 请求封装
│       ├── components/       可复用组件
│       ├── router/           前端路由
│       ├── store/            Pinia 状态管理
│       └── views/            页面级组件
├── backend/
│   └── app/
│       ├── ai/               AI 分析模块（后续阶段）
│       ├── api/              FastAPI 接口路由
│       ├── core/             应用配置
│       ├── database/         SQLAlchemy 数据库连接
│       ├── models/           数据库模型
│       ├── schemas/          API 请求与响应模型
│       └── services/         业务与数据分析服务
├── algorithms/               可复用机器学习算法（后续阶段）
├── database/                 MySQL 初始化脚本
├── datasets/                 本地数据集目录（内容不提交到 Git）
├── docs/                     项目文档
├── reports/                  分析报告目录（内容不提交到 Git）
└── tests/                    自动化测试
```

## 配置说明

后端环境变量统一使用 `DATAINSIGHT_` 前缀。第一阶段的完整配置项可参考 `backend/.env.example`。

请勿将填写了真实数据库密码的 `.env` 文件、API 密钥或其他敏感信息提交到 Git。

## 开发路线

1. 项目初始化——已完成
2. 用户注册、登录、JWT 身份认证与用户数据持久化
3. 数据集上传与管理
4. 自动化数据画像、统计分析与可视化
5. PCA、Isolation Forest 和 Local Outlier Factor
6. AI 数据分析师与 HTML 报告生成
7. 示例数据、完整文档、贡献指南等开源准备

## 当前已提供的接口

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| `GET` | `/api` | 获取 API 基本信息 |
| `GET` | `/api/health` | 检查后端服务运行状态 |
| `GET` | `/docs` | 打开 Swagger API 文档 |

## 运行测试

激活 `pythonProject` 环境并安装后端依赖后，在项目根目录执行：

```powershell
cd D:\new__platform
D:\anaconda\envs\pythonProject\python.exe -m pytest
```

前端生产构建：

```powershell
cd D:\new__platform\frontend
npm run build
```

## 开源协议

本项目使用 [MIT License](LICENSE)。
