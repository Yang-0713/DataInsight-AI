# DataInsight AI

DataInsight AI 是一个开源的 AI 自动化数据分析平台，旨在帮助用户上传数据集、检查数据质量、完成统计分析与数据可视化、检测异常样本，并生成由 AI 辅助的分析结论和报告。

> 当前进度：**第三阶段——数据集管理**

项目目前已经具备用户注册与登录、JWT 身份认证，以及用户私有的 CSV 数据集上传、存储、列表、详情和删除功能。

## 当前功能

### 身份认证

- 用户名、邮箱和密码注册
- 用户名或邮箱登录
- Argon2 密码单向哈希
- JWT Bearer 访问令牌
- `USER`、`ADMIN` 用户角色
- 前端登录状态恢复和受保护路由

### 数据集管理

- 拖拽或选择上传 CSV
- 上传文件大小限制
- UTF-8、UTF-8 BOM 和 GB18030 编码支持
- 使用 pandas 验证 CSV 并提取行数、字段数
- 文件存入本地 `datasets/用户ID/` 目录
- 数据集元数据保存至 MySQL
- 用户只能查看和删除自己的数据集
- 删除记录时同步移除本地文件

数据画像、字段统计和可视化将在第四阶段实现。

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Element Plus、Pinia、Axios、ECharts、Tailwind CSS
- 后端：Python 3.10、FastAPI、SQLAlchemy、PyMySQL、Pydantic Settings
- 数据处理：pandas
- 身份认证：Argon2、PyJWT
- 数据库：本地 MySQL 8+

## 环境要求

- Node.js 20+
- npm 10+
- `pythonProject` Conda 虚拟环境（Python 3.10.12）
- MySQL 8+

本项目无需 Docker。

## 1. 初始化数据库

首次安装时，在项目根目录执行：

```powershell
mysql -u root -p < database/init_db.sql
```

如果已经完成第二阶段，只需执行第三阶段迁移：

```powershell
mysql -u root -p < database/migrations/003_create_datasets.sql
```

完整初始化脚本会创建：

- `datainsight_ai` 数据库
- `users` 用户表
- `datasets` 数据集元数据表

## 2. 配置并启动后端

激活指定的开发环境：

```powershell
conda activate pythonProject
cd D:\new__platform\backend
python -m pip install -r requirements.txt
```

复制环境变量示例：

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，填写 MySQL 配置，并设置至少 32 个字符的 JWT 密钥：

```env
DATAINSIGHT_MYSQL_HOST=127.0.0.1
DATAINSIGHT_MYSQL_PORT=3306
DATAINSIGHT_MYSQL_USER=root
DATAINSIGHT_MYSQL_PASSWORD=your-password
DATAINSIGHT_MYSQL_DATABASE=datainsight_ai

DATAINSIGHT_JWT_SECRET_KEY=replace-with-a-long-random-secret-key
DATAINSIGHT_DATASET_STORAGE_DIR=../datasets
DATAINSIGHT_MAX_UPLOAD_SIZE_MB=50
```

可以使用 PowerShell 生成随机 JWT 密钥：

```powershell
[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
```

启动 FastAPI：

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

浏览器访问 <http://127.0.0.1:5173>。Vite 会将 `/api` 请求代理到本地 FastAPI 服务。

## API

### 身份认证

| 方法 | 地址 | 是否需要令牌 | 说明 |
| --- | --- | --- | --- |
| `POST` | `/api/auth/register` | 否 | 注册普通用户 |
| `POST` | `/api/auth/login` | 否 | 使用用户名或邮箱登录 |
| `GET` | `/api/auth/me` | 是 | 获取当前登录用户 |

### 数据集

| 方法 | 地址 | 说明 |
| --- | --- | --- |
| `POST` | `/api/datasets/upload` | 上传并检查 CSV |
| `GET` | `/api/datasets` | 获取当前用户的数据集列表 |
| `GET` | `/api/datasets/{id}` | 获取当前用户的数据集详情 |
| `DELETE` | `/api/datasets/{id}` | 删除数据集记录及本地文件 |

所有数据集接口均需要：

```http
Authorization: Bearer <access_token>
```

上传示例：

```bash
curl -X POST http://127.0.0.1:8000/api/datasets/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@sales.csv"
```

## 数据存储

CSV 文件默认存储在：

```text
datasets/
└── 用户ID/
    └── 随机文件名.csv
```

数据库只保存用户归属、原始文件名、相对存储路径、行数、字段数和上传时间。API 不会向前端返回服务器文件路径。

`datasets/` 中的上传内容已被 `.gitignore` 排除，不会提交到 GitHub。

## 项目结构

```text
DataInsight-AI/
├── frontend/
│   └── src/
│       ├── api/              身份认证与数据集接口
│       ├── router/           路由与访问守卫
│       ├── store/            Pinia 认证与数据集状态
│       ├── style/            共享页面样式
│       ├── utils/            令牌和错误处理
│       └── views/            登录、注册、工作台和数据集页面
├── backend/
│   └── app/
│       ├── api/              FastAPI 路由与依赖
│       ├── core/             配置、密码和 JWT
│       ├── database/         SQLAlchemy 连接
│       ├── models/           用户和数据集模型
│       ├── schemas/          请求与响应模型
│       └── services/         认证、文件存储和 CSV 检查
├── database/
│   ├── init_db.sql           完整初始化脚本
│   └── migrations/           分阶段数据库迁移
├── datasets/                 本地上传文件
├── algorithms/               机器学习算法（后续阶段）
├── reports/                  分析报告（后续阶段）
└── tests/                    后端自动化测试
```

## 关键环境变量

| 环境变量 | 说明 |
| --- | --- |
| `DATAINSIGHT_MYSQL_*` | MySQL 连接配置 |
| `DATAINSIGHT_JWT_SECRET_KEY` | JWT 签名密钥，至少 32 个字符 |
| `DATAINSIGHT_ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌有效时间 |
| `DATAINSIGHT_DATASET_STORAGE_DIR` | CSV 本地存储目录 |
| `DATAINSIGHT_MAX_UPLOAD_SIZE_MB` | 单个上传文件大小上限 |
| `DATAINSIGHT_AUTO_CREATE_TABLES` | 启动时是否创建已实现的数据表 |

请勿提交包含真实数据库密码、JWT 密钥或其他敏感信息的 `.env` 文件。

## 运行测试

后端：

```powershell
cd D:\new__platform
D:\anaconda\envs\pythonProject\python.exe -m pytest
```

前端：

```powershell
cd D:\new__platform\frontend
npm run type-check
npm run build
```

## 开发路线

1. 项目初始化——已完成
2. 注册、登录、JWT 身份认证与用户持久化——已完成
3. CSV 数据集上传、存储和管理——已完成
4. 自动化数据画像、统计分析与可视化
5. PCA、Isolation Forest 和 Local Outlier Factor
6. AI 数据分析师与 HTML 报告生成
7. 示例数据、完整文档和贡献指南

下一步建议进入第四阶段，为已上传的数据集生成数据画像、统计结果和 ECharts 图表数据。

## 开源协议

本项目使用 [MIT License](LICENSE)。
