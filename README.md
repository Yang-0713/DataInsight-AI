# DataInsight AI

DataInsight AI 是一个开源的 AI 自动化数据分析平台，旨在帮助用户上传数据集、检查数据质量、完成统计分析与数据可视化、检测异常样本，并生成由 AI 辅助的分析结论和报告。

> 当前进度：**第二阶段——身份认证系统**

项目目前已经具备 Vue 3 前端、FastAPI 后端、MySQL 数据库连接，以及完整的用户注册、登录、JWT 身份认证和受保护用户接口。数据集管理、自动化分析、机器学习和 AI 分析等功能将在后续阶段逐步实现。

## 当前功能

- 用户名、邮箱和密码注册
- 用户名或邮箱登录
- Argon2 密码单向哈希
- JWT Bearer 访问令牌
- 受保护的当前用户接口
- `USER`、`ADMIN` 用户角色
- 前端登录、注册和受保护工作台
- 页面刷新后的登录状态恢复
- MySQL 用户数据持久化

公开注册接口只能创建 `USER` 普通用户，不能自行注册为管理员。

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Element Plus、Pinia、Axios、ECharts、Tailwind CSS
- 后端：Python 3.10、FastAPI、SQLAlchemy、PyMySQL、Pydantic Settings
- 身份认证：Argon2、PyJWT
- 数据库：本地 MySQL 8+

## 环境要求

- Node.js 20+
- npm 10+
- `pythonProject` Conda 虚拟环境（Python 3.10.12）
- MySQL 8+

本项目无需安装 Docker。

## 1. 初始化 MySQL 数据库

登录本地 MySQL 服务后，在项目根目录执行：

```sql
SOURCE database/init_db.sql;
```

也可以在 PowerShell 中执行：

```powershell
mysql -u root -p < database/init_db.sql
```

初始化脚本会创建 `datainsight_ai` 数据库和 `users` 用户表。FastAPI 启动时也会检查并创建当前阶段已实现但尚不存在的数据表。

## 2. 配置并启动后端

后端开发统一使用：

```text
D:\anaconda\envs\pythonProject
```

激活环境并进入后端目录：

```powershell
conda activate pythonProject
cd D:\new__platform\backend
```

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

复制环境变量示例：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，填写本机 MySQL 配置，并将 `DATAINSIGHT_JWT_SECRET_KEY` 修改为至少 32 个字符的随机密钥。可在 PowerShell 中生成随机值：

```powershell
[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

启动后端：

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

如果无法激活 Conda 环境，可以直接运行：

```powershell
D:\anaconda\envs\pythonProject\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

常用地址：

- API 根地址：<http://127.0.0.1:8000/api>
- 健康检查：<http://127.0.0.1:8000/api/health>
- Swagger 文档：<http://127.0.0.1:8000/docs>

## 3. 启动前端

打开另一个 PowerShell 窗口：

```powershell
cd D:\new__platform\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

浏览器访问 <http://127.0.0.1:5173>。开发环境下，Vite 会将 `/api` 请求代理到 `http://127.0.0.1:8000`。

## 身份认证 API

| 方法 | 地址 | 是否需要令牌 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register` | 否 | 注册普通用户 |
| `POST` | `/api/auth/login` | 否 | 使用用户名或邮箱登录 |
| `GET` | `/api/auth/me` | 是 | 获取当前登录用户 |
| `GET` | `/api/health` | 否 | 检查后端状态 |

访问受保护接口时需添加请求头：

```http
Authorization: Bearer <access_token>
```

注册请求示例：

```json
{
  "username": "analyst",
  "email": "analyst@example.com",
  "password": "DataInsight123!"
}
```

登录请求示例：

```json
{
  "identity": "analyst@example.com",
  "password": "DataInsight123!"
}
```

## 项目结构

```text
DataInsight-AI/
├── frontend/                 Vue 3 前端
│   └── src/
│       ├── api/              HTTP 与认证接口
│       ├── components/       可复用组件
│       ├── router/           路由与访问守卫
│       ├── store/            Pinia 应用与认证状态
│       ├── style/            页面级共享样式
│       ├── utils/            令牌和错误处理工具
│       └── views/            登录、注册和工作台页面
├── backend/
│   └── app/
│       ├── ai/               AI 分析模块（后续阶段）
│       ├── api/              路由和认证依赖
│       ├── core/             配置、密码与 JWT
│       ├── database/         SQLAlchemy 连接
│       ├── models/           用户数据库模型
│       ├── schemas/          请求与响应模型
│       └── services/         用户认证服务
├── algorithms/               机器学习算法（后续阶段）
├── database/                 MySQL 初始化脚本
├── datasets/                 本地数据集目录
├── docs/                     项目文档
├── reports/                  分析报告目录
└── tests/                    后端自动化测试
```

## 环境变量

后端环境变量统一使用 `DATAINSIGHT_` 前缀，完整配置参考 `backend/.env.example`。

关键配置：

| 环境变量 | 说明 |
| --- | --- |
| `DATAINSIGHT_MYSQL_*` | MySQL 地址、端口、用户名、密码和数据库 |
| `DATAINSIGHT_JWT_SECRET_KEY` | JWT 签名密钥，至少 32 个字符 |
| `DATAINSIGHT_JWT_ALGORITHM` | JWT 算法，默认 `HS256` |
| `DATAINSIGHT_ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌有效时间 |
| `DATAINSIGHT_AUTO_CREATE_TABLES` | 启动时是否自动创建已实现的数据表 |

请勿提交包含真实数据库密码、JWT 密钥或其他敏感信息的 `.env` 文件。

## 运行测试

后端：

```powershell
cd D:\new__platform
D:\anaconda\envs\pythonProject\python.exe -m pytest
```

前端类型检查和生产构建：

```powershell
cd D:\new__platform\frontend
npm run type-check
npm run build
```

## 开发路线

1. 项目初始化——已完成
2. 注册、登录、JWT 身份认证与用户持久化——已完成
3. CSV 数据集上传、存储和管理
4. 自动化数据画像、统计分析与可视化
5. PCA、Isolation Forest 和 Local Outlier Factor
6. AI 数据分析师与 HTML 报告生成
7. 示例数据、完整文档和贡献指南

下一步建议进入第三阶段，实现用户私有的 CSV 数据集上传和管理。

## 开源协议

本项目使用 [MIT License](LICENSE)。
