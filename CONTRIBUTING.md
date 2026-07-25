# 贡献指南

感谢你帮助改进 DataInsight AI。项目欢迎问题报告、文档修正、测试、功能建议和代码贡献。

参与贡献即表示你同意遵守 [社区行为准则](CODE_OF_CONDUCT.md)，并同意以项目的 [MIT License](LICENSE) 发布你的贡献。

## 开始之前

- 普通缺陷和功能建议请先搜索现有 Issue，避免重复。
- 安全漏洞不要创建公开 Issue，请按照 [安全策略](SECURITY.md) 私下报告。
- 大型功能或架构调整建议先创建讨论 Issue，说明使用场景、数据边界和兼容性影响。
- 不要在 Issue、日志、测试数据或提交中包含真实密码、令牌、API 密钥或敏感业务数据。

## 本地开发环境

完整步骤见 [安装与运行指南](docs/installation.md)。项目统一使用：

- Python 3.10
- `pythonProject` Conda 环境
- Node.js 20+
- MySQL 8+

后端依赖：

```powershell
conda activate pythonProject
python -m pip install -r backend/requirements.txt
```

前端依赖：

```powershell
cd frontend
npm ci
```

自动化测试默认使用 SQLite，不要求测试机连接 MySQL，也不会调用真实 AI 服务。

## 创建分支

从最新目标分支创建语义清晰的分支：

```powershell
git switch main
git pull --ff-only
git switch -c feat/short-description
```

推荐前缀：

- `feat/`：新功能
- `fix/`：缺陷修复
- `docs/`：文档
- `test/`：测试
- `refactor/`：不改变外部行为的重构
- `chore/`：工具、依赖或维护任务

## 代码规范

### Python

- 目标版本为 Python 3.10。
- 新增公共函数和复杂数据结构时补充类型注解。
- 业务规则放在 `services/`，路由层负责认证、输入和 HTTP 错误映射。
- 所有数据集、分析结果和报告查询必须验证当前用户所有权。
- 路径操作必须先解析并确认位于配置的存储根目录内。
- AI 提供方不得记录 API 密钥、完整提示词或上游敏感响应。

### Vue 与 TypeScript

- 使用 Vue 3 Composition API 和 `<script setup lang="ts">`。
- API 类型集中在 `frontend/src/api/`。
- 跨页面状态使用 Pinia；仅组件内部使用的状态保留在组件中。
- 用户可见文案使用简体中文，代码标识符使用英文。
- 新页面必须兼顾窄屏布局和键盘可操作性。

### 数据库

- 数据库结构变化必须同时提供幂等迁移和完整初始化脚本更新。
- 外键删除行为、索引和 MySQL/SQLite 测试兼容性需要明确说明。
- 不要把运行时数据库、CSV 或报告文件提交到仓库。

## 添加测试

每次行为变更都应包含相应测试。

后端：

```powershell
conda run -n pythonProject python -m pytest -q
```

前端：

```powershell
cd frontend
npm run type-check
npm run build
```

AI 相关测试必须使用假的提供方或 HTTP Mock，不得消耗真实额度或依赖外部网络。

如果修改示例数据，请确保 `tests/test_example_dataset.py` 仍通过，并同步更新 `examples/README.md`。

## 提交信息

提交信息使用简洁的祈使语气，描述一个完整改动，例如：

```text
Add dataset export endpoint
Fix report ownership validation
Document MySQL installation
```

避免把无关改动塞入同一个提交，也不要提交生成目录、缓存或本地 `.env`。

## Pull Request

提交 PR 前确认：

- 工作区只包含本次任务相关改动
- 后端测试通过
- 前端类型检查和生产构建通过
- README、API 文档和环境变量模板已同步
- 没有密钥、用户数据或本地绝对路径
- 数据库改动包含迁移说明
- PR 描述说明变更原因、用户影响和验证结果

PR 默认可以先创建为草稿。准备好审核后再转为 Ready for review。

维护者可能要求补充测试、拆分提交或调整接口兼容性。请在同一 PR 中继续推送修正，不要为同一变更重复创建 PR。

## 文档贡献

文档使用 GitHub Flavored Markdown。内部链接使用相对路径，命令示例应注明运行目录，并避免把某台开发机的密码或个人路径写成通用要求。

公开 API 发生变化时，至少同步：

- `docs/api.md`
- FastAPI 路由与 Pydantic Schema
- `README.md` 的接口概览
- 必要的安装或迁移说明

## 获得帮助

普通使用问题可以创建 GitHub Issue，并提供：

- 操作系统与版本
- Python、Node.js、MySQL 版本
- 最小复现步骤
- 已脱敏的错误信息
- 预期行为和实际行为
