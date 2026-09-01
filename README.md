# QualiSync

> 测试协作与质量管理开源平台

QualiSync 是一个面向测试团队的协作与质量管理平台，提供缺陷管理、测试计划、用例管理、接口测试、性能测试、Mock 服务、数据工厂等完整的测试工具链。

---

## ✨ 功能特性

### 核心功能
- **缺陷管理** — 完整的 Bug 生命周期管理，支持自定义工作流、状态流转、优先级分类
- **测试计划** — 创建和管理测试计划，跟踪执行进度和覆盖率
- **用例管理** — 结构化的测试用例管理，支持目录树、标签、批量操作
- **接口测试** — Swagger 导入、接口自动化测试、响应断言
- **性能测试** — 压测场景管理、Jenkins 集成、性能报告生成
- **Mock 服务** — 快速创建 API Mock 接口，支持动态响应规则
- **数据工厂** — 测试数据生成和管理工具

### 协作与管理
- **RBAC 权限控制** — 基于角色的细粒度权限管理
- **产品/项目管理** — 多层级产品和项目结构
- **自动化集成** — Jenkins 流水线对接，支持自动化测试触发
- **AI 辅助** — 接入大语言模型，支持 AI 生成测试用例、AI 辅助缺陷分析

### 其他
- **数据监控** — 关键质量指标可视化看板
- **精准测试** — 基于代码变更的精准测试推荐
- **需求质量** — 需求阶段的质量风险评估

---

## 🛠 技术栈

### 前端
- Vue.js 2.x + Element UI 2.x
- Webpack 3.x
- Axios, ECharts, WangEditor

### 后端
- Python 3.10+
- FastAPI + Flask (legacy)
- PostgreSQL + SQLAlchemy
- Redis (Token 存储 / 缓存)

### 部署
- Docker + Docker Compose
- Nginx (前端静态资源 + 反向代理)
- Gunicorn + Uvicorn (后端)

---

## 📋 环境要求

| 组件 | 版本要求 |
|------|---------|
| Python | >= 3.10 |
| Node.js | >= 16 |
| PostgreSQL | >= 12 |
| Redis | >= 6 |
| Docker (可选) | >= 20 |

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/your-org/qualisync.git
cd qualisync
```

### 2. 后端部署

```bash
cd backend

# 创建 Python 虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写数据库、Redis 等配置

# 启动服务
gunicorn --config=gunicorn.conf.py app.main:app
```

后端默认监听 `0.0.0.0:5010`。

### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

前端开发服务器默认监听 `localhost:8081`。

### 4. Docker 部署

```bash
# 构建后端镜像
cd backend
docker build -t qualisync-backend .

# 构建前端镜像
cd frontend
docker build -t qualisync-frontend .

# 启动（确保 nginx.conf 中 proxy_pass 地址与实际后端地址一致）
docker run -d --name qualisync-backend --env-file .env -p 5010:5010 qualisync-backend
docker run -d --name qualisync-frontend -p 80:80 qualisync-frontend
```

---

## ⚙️ 配置说明

所有敏感配置通过环境变量管理，参考 `backend/.env.example` 获取完整列表。

### 必填配置

| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `SPARKATP_SQL_URI` | PostgreSQL 连接字符串 | `postgresql+psycopg2://user:pass@host:5432/dbname` |
| `REDIS_URL` | Redis 连接地址 | `redis://127.0.0.1:6379/0` |

### 可选配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `BE_URL` | 后端服务地址 | `0.0.0.0:5010` |
| `PLATFORM_BASE_URL` | 平台对外访问地址 | `http://127.0.0.1:5010/it/api` |
| `JENKINS_BASE_URL` | Jenkins 服务地址 | 空 |
| `FEISHU_WEBHOOK_URL` | 飞书机器人 Webhook | 空 |
| `CUSTOM_API_KEY` | AI 大模型 API Key | 空 |
| `CUSTOM_API_BASE` | AI 大模型 API 地址 | 空 |
| `CUSTOM_MODEL` | AI 模型名称 | 空 |

---

## 📁 项目结构

```
qualisync/
├── backend/                  # 后端服务
│   ├── app/                  # FastAPI 应用
│   │   ├── api/              # 控制器、服务、数据访问、模型
│   │   ├── core/             # 配置中心、数据库、安全模块
│   │   ├── routers/          # FastAPI 路由
│   │   └── schemas/          # Pydantic 数据模型
│   ├── common/               # 公共工具
│   ├── config/               # AI 配置
│   ├── resources/            # SQL 迁移脚本
│   ├── const.py              # 基础配置
│   ├── requirements.txt      # Python 依赖
│   ├── Dockerfile
│   └── .env.example          # 环境变量模板
├── frontend/                 # 前端应用
│   ├── src/
│   │   ├── api/              # API 接口封装
│   │   ├── components/       # Vue 组件
│   │   ├── assets/           # 静态资源
│   │   ├── router/           # 路由配置
│   │   └── vuex/             # 状态管理
│   ├── build/                # Webpack 配置
│   ├── nginx.conf            # Nginx 配置
│   ├── Dockerfile
│   └── package.json
├── picture/                  # 项目截图
└── README.md
```

---

## 🔌 API 文档

启动后端后，访问以下地址查看 API 文档：
- Swagger UI: `http://localhost:5010/docs`
- ReDoc: `http://localhost:5010/redoc`

---

## 📜 License

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
