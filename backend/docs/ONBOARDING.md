# effekt-interface 新人上手指南

> 由 `/understand --language zh` 自动生成。图谱：`.understand-anything/knowledge-graph.json`

## 项目概览

| 项 | 说明 |
|---|---|
| **名称** | effekt-interface |
| **描述** | 面向 IT 接口与测试管理的 Flask 后端：提供接口/用例/计划/报告等 REST API，使用 SQLAlchemy 持久化，经 Gunicorn 部署，并集成 Jenkins、Jira、Redis 与 OpenAI 等能力。 |
| **语言** | config、dockerfile、html、jenkinsfile、json、markdown、python、sql、txt、xlsx、xml |
| **框架** | Docker、Faker、Flask、Flask-Cors、Gunicorn、Jenkins、OpenAI、SQLAlchemy、flask_redis |
| **提交** | `e1e65632` |

```bash
pip3 install -r requirements.txt
gunicorn --config=gunicorn.conf.py manage:app
```

## 架构分层

### API层

Flask 路由注册、Controller 与鉴权中间件，对外暴露 IT 测试平台 REST 接口。

- `app/api/__init__.py` — Flask API 子包初始化模块，当前无导出符号。
- `app/api/controller/__init__.py` — API 控制器子包占位初始化文件。
- `app/api/controller/automationController.py` — Flask 自动化测试执行控制器，暴露用例/计划触发及 Jenkins 回调全生命周期的 HTTP 接口。
- `app/api/controller/baseCrudController.py` — CRUD 控制器基类，提供 SqlSession 生命周期、请求参数解析与 JSON 序列化能力。
- `app/api/controller/bugController.py` — 缺陷管理 HTTP 控制器，提供缺陷 CRUD、评论、历史、统计及附件上传等 API。
- `app/api/controller/caseController.py` — 测试用例与模块树 HTTP 控制器，覆盖用例、快照、评审、导入及模块维护。
- `app/api/controller/dataBuilderController.py` — Flask API 控制器，提供造数器 CRUD、执行与任务状态查询接口，业务逻辑委托给 DataBuilderService。
- `app/api/controller/documentSourceController.py` — 文档源 HTTP 控制器，管理需求/设计文档的上传、刷新、AI 生成用例与模块匹配导入。
- `app/api/controller/mockController.py` — Flask API 控制器，提供 Mock 文档导入、接口/场景 CRUD、调用日志、解析问题与运行时 Mock 分发端点。
- `app/api/controller/planController.py` — 测试计划控制器，处理计划、轮次与计划用例的 CRUD 及执行进度查询。
- `app/api/controller/productController.py` — 产品域 HTTP 控制器，提供产品列表、详情、创建、更新与软删除接口，负责参数校验与序列化。
- `app/api/controller/projectController.py` — 项目控制器，管理项目、环境、成员与 Webhook，并集成 RBAC 权限校验。

*（另有 10 个文件，见 Dashboard）*

### 服务层

自动化、Mock、RBAC、计划与报告等业务编排，对接 Jenkins 与外部系统。

- `app/api/service/__init__.py` — 业务服务层子包占位初始化文件。
- `app/api/service/aiService.py` — 中央 AI 集成服务，封装 LLM 对话补全、JSON 提取、测试用例生成、技能/规则内容及文档分块。
- `app/api/service/automationService.py` — 自动化测试核心业务服务：创建执行记录、触发 Jenkins、接收回调并汇总执行结果。
- `app/api/service/bugService.py` — 缺陷业务服务层，将控制器请求委托给 BugDao 并组装评论/历史逻辑。
- `app/api/service/caseService.py` — 用例业务服务薄封装，代理 CaseDao 的 CRUD 与键/快照版本生成。
- `app/api/service/dataBuilderService.py` — 服务层编排 DAO 操作，调用 DataBuilderExecutor 执行造数任务并回写任务状态。
- `app/api/service/documentSourceService.py` — 文档源核心服务：飞书/PDF 拉取、AI 批量生成用例、模块匹配与导入编排。
- `app/api/service/jenkinsPollService.py` — Jenkins 构建状态轮询服务，根据构建 API 同步 AutoExecution 与用例执行状态。
- `app/api/service/mockDataGeneratorService.py` — 基于 Faker 与可选 AI，从 API Schema 生成默认 Mock 场景、请求示例与响应模板。
- `app/api/service/mockMatchService.py` — 路径规范化、按 HTTP 方法/路径匹配接口，以及运行时通过匹配规则选择 Mock 场景。
- `app/api/service/mockParserService.py` — 解析 OpenAPI、YApi、手动 JSON 及文本/docx 源，归一化为 Mock 接口定义，并支持 AI 回退解析。
- `app/api/service/mockService.py` — Mock 核心编排：文档导入流水线、接口/场景管理、日志记录与 HTTP 运行时响应组装。

*（另有 11 个文件，见 Dashboard）*

### 数据层

SQLAlchemy ORM/DAO 与 PostgreSQL 建表脚本，持久化用例、执行与权限数据。

- `app/api/dao/__init__.py` — 数据访问层子包占位初始化文件。
- `app/api/dao/automationDao.py` — 自动化执行与执行用例的 DAO，封装 AutoExecution/AutoExecutionCase 及关联计划、用例的 SQLAlchemy 查询。
- `app/api/dao/bugDao.py` — 缺陷数据访问层，封装 SQLAlchemy 查询、软删、评论/历史及缺陷编号生成。
- `app/api/dao/caseDao.py` — 用例与模块 DAO，处理用例键生成、快照版本、评审记录及模块名称映射。
- `app/api/dao/dataBuilderDao.py` — DataBuilder 与 DataTask 实体的数据访问层，基于 SQLAlchemy 会话实现通用 CRUD、过滤分页与软删除。
- `app/api/dao/documentSourceDao.py` — 文档源 DAO，提供按来源查询、版本管理与过滤列表等持久化操作。
- `app/api/dao/mockDao.py` — Mock 实体数据访问层，支持筛选列表、场景查询及运行时匹配所需的已启用接口查找。
- `app/api/dao/planDao.py` — 测试计划域数据访问层，封装计划/用例/轮次模型的增删改查、软删除分页及计划执行进度聚合统计。
- `app/api/dao/productDao.py` — 产品数据访问层，提供通用 CRUD、软删除过滤与分页查询的静态方法。
- `app/api/dao/projectDao.py` — 项目域 DAO，复用通用 CRUD 模式，并提供产品名与项目名的批量映射查询。
- `app/api/dao/projectHookDao.py` — 项目 Webhook 数据访问层，封装 project_hook 表的增删改查与分页查询。
- `app/api/dao/rbacDao.py` — RBAC 数据访问层，封装角色、权限、菜单及其关联表的 SQLAlchemy 查询。

*（另有 51 个文件，见 Dashboard）*

### 工具层

HTTP/Jenkins/定时任务客户端、统一响应与数据库会话等跨层共享能力。

- `__sync_prod_db.py` — 占位或待实现的生产库同步脚本，当前文件为空。
- `attachment/用例导入模版.xlsx` — 测试用例批量导入的 Excel 模板，供前端或运维下载填写后导入用例库。
- `common/__init__.py` — 公共模块包初始化文件，无业务逻辑。
- `common/apiResponse.py` — 统一 JSON API 响应封装，含 CORS 头与日期/Decimal 自定义序列化。
- `common/cronRequest.py` — 定时任务平台 HTTP 客户端，封装登录、任务触发与 SQL 项目相关远程调用。
- `common/dataBuilderExecutor.py` — 独立执行器，对 JSON 造数定义进行模板占位符渲染与随机值生成，产出合成数据集。
- `common/feishuMessage.py` — 封装飞书群机器人 Webhook 消息发送与关键字链接校验的通用工具类。
- `common/getRequest.py` — 基于 requests 的通用 GET 请求封装，统一超时与错误日志。
- `common/getUserInfo.py` — 从外部用户中心拉取当前登录用户信息的轻量客户端。
- `common/jenkinsRequest.py` — Jenkins REST API 封装，负责触发构建与查询构建状态。
- `common/sqlSession.py` — 全局 SQLAlchemy 会话工厂，含 Postgres URI 构建、连接缓存与事务辅助方法。
- `logger.py` — 基于 const.LOG_DIR 的 FunctionalTestsLogger 工厂，为各层提供统一日志实例。

### 应用入口层

manage.py 与 Flask 应用工厂，负责启动与调度入口。

- `app/__init__.py` — Flask 应用工厂，注册 API 蓝图并初始化 API 文档。
- `manage.py` — 应用启动脚本，创建 Flask 实例、启用 CORS 并提供 Bug 图片静态访问。

### 配置层

环境常量、Gunicorn、AI/技能资产与 Interface Hunter 等运行配置。

- `.env` — 运行时环境变量配置，定义 Meteor/Routin 自定义 LLM API、模型提供商选择及 AI 请求超时与重试策略。
- `config/skills/test-case-generator/evals/evals.json` — 评测清单：声明 test-case-generator 技能名称及用于技能触发测试的提示词评测用例列表。
- `resources/config.xml` — Jenkins 调度任务 Job 配置导出，定义 Robot Framework 用例执行参数（环境、路径、标签过滤、重跑）及 sparkatp-scripts 构建命令。
- `resources/interface_hunter_config.xml` — Jenkins Interface Hunter Job 配置，用于按组抓取 hh/hhi 等环境的 Swagger 接口定义，支持新服务与新 group 场景。
- `config/ai_config.py` — 从项目根 .env 加载大模型 API 密钥、端点与超时等配置，供 AI 服务统一读取。
- `config/skills/skill-creator/assets/eval_review.html` — 技能评测结果审阅页的静态 HTML 片段或资源模板。
- `config/skills/skill-creator/eval-viewer/generate_review.py` — 扫描评测工作区、嵌入输出文件并启动本地 HTTP 服务，生成交互式技能评测审阅页面。
- `config/skills/skill-creator/eval-viewer/viewer.html` — 技能评测审阅前端单页，展示多轮运行输出、反馈与基准对比。
- `config/skills/skill-creator/scripts/__init__.py` — 空的 Python 包初始化文件，将 skill-creator 脚本目录标记为可导入包。
- `config/skills/skill-creator/scripts/aggregate_benchmark.py` — 命令行工具：加载技能评测运行产物，跨配置聚合通过率与时延统计，并输出 JSON 与 Markdown 基准报告。
- `config/skills/skill-creator/scripts/generate_report.py` — 将技能评估 JSON 数据渲染为可自动刷新的 HTML 报告，供 skill-creator 迭代优化流程查看训练/测试结果。
- `config/skills/skill-creator/scripts/improve_description.py` — 基于评估结果与历史记录，调用 Claude CLI 自动改写 SKILL.md 中的技能描述，以提升技能触发率。

*（另有 8 个文件，见 Dashboard）*

### 基础设施层

Docker 镜像与 Jenkinsfile，定义容器化部署与 CI 流水线。

- `Dockerfile` — 为 Flask API 定义容器镜像：基于私有仓库的 Python 3.10、通过 requirements.txt 安装依赖、复制完整应用、暴露 5010 端口，并由 Gunicorn 经 gunicorn.conf.py 启动 manage:app。
- `Dockerfile` — 基于私有仓库 39.170.26.156:8443 的 python:3.10-bookworm 运行时镜像阶段，设置 WORKDIR /app、创建 logs 目录并暴露 5010 端口。
- `Jenkinsfile` — effekt-interface 的 Jenkins 声明式流水线：拉取代码、构建并推送 Harbor 镜像，经 SSH 部署到远程主机并验证容器健康。
- `Dockerfile` — 为 Flask API 定义容器镜像：基于私有仓库的 Python 3.10、通过 requirements.txt 安装依赖、复制完整应用、暴露 5010 端口，并由 Gunicorn 经 gunicorn.conf.py 启动 manage:app。

### 文档层

README、API/SQL 说明、RBAC 设计与 AI Skill 规则文档。

- `.agents/RBAC_API.md` — RBAC、用户与菜单管理 REST API 的完整接口文档，涵盖角色/权限/菜单 CRUD、分配关系及认证联调示例。
- `.plan/1ZFcjkLpHmrHbluVoOtA4.md` — pytest 与 Jenkins 自动化执行接入的完整后端设计，涵盖 auto_execution 表结构、MVC 分层职责、触发/拉取/回调接口、状态流转、Jenkins 参数与联调示例，可直接交付 AI 编码落地。
- `.plan/3onvvJGzAx9Dhi05JkVpx.md` — 在现有 Flask + SQLAlchemy 分层架构下接入测试管理模块的分阶段实施计划，覆盖项目/用例/计划/报告/造数等 CRUD 与 /it/api 风格路由注册，不引入 FastAPI 或 Celery。
- `.plan/YCGiVLWod2rghU8nT3fEv.md` — 角色/用户/菜单 RBAC 详细设计，定义 user、role、permission、menu 及关联表 schema，并规划 userModel/rbacModel、DAO、Service、Controller 与 views 路由清单，仅输出设计不改业务代码。
- `README.md` — 项目极简入门说明，列出克隆仓库、安装依赖与通过 gunicorn 启动 Flask 应用的三步命令。
- `config/rules/智慧运营/智慧运营V2.0/采购工作台/待办规则/RULE.md` — 智慧运营采购工作台待办场景的测试规则说明，约束适用场景与用例设计要点。
- `config/skills/skill-creator/LICENSE.txt` — skill-creator 技能包附带的许可证全文。
- `config/skills/skill-creator/SKILL.md` — skill-creator 权威指南：涵盖技能编写、评测流程、基准聚合、描述优化及面向 Claude 代理的打包说明。
- `config/skills/skill-creator/agents/analyzer.md` — 定义事后分析（Post-hoc Analyzer）智能体：在盲评比较出胜负后，对照技能文件与执行 transcript，分析获胜原因并生成可操作的改进建议；另含基准测试结果聚合分析流程。
- `config/skills/skill-creator/agents/comparator.md` — 定义盲评比较（Blind Comparator）智能体：在不知晓 A/B 输出对应技能的前提下，依据任务提示与可选断言，用内容/结构双维度量表评判并选出更优输出。
- `config/skills/skill-creator/agents/grader.md` — 定义评分（Grader）智能体：对照执行 transcript 与输出目录，逐条判定期望（expectations）是否通过，并批判性审视评测断言本身的质量与覆盖缺口。
- `config/skills/skill-creator/references/schemas.md` — 定义 evals、grading、metrics、benchmark 等评测流水线 JSON 文件的结构说明。

*（另有 6 个文件，见 Dashboard）*

### 测试层

本地修复与验证脚本，用于开发期快速回归。

- `test_fix.py` — 临时脚本，用于验证或修复 const 中的配置项与数据库连接参数。

## 核心概念

- **分层模式**：Controller → Service → DAO → Model
- **BaseCrudController**：统一 Session、参数与 JSON 响应
- **认证**：authMiddleware.py（JWT、权限装饰器）
- **自动化**：automationService + Jenkins
- **Mock**：文档解析与运行时 Mock 多 Service 协作
- **RBAC**：角色/权限/菜单（rbacModel）

## 导览（Tour）

### 步骤 1：项目概览

从 README 入手，了解 effekt-interface 是面向 IT 接口管理的 Flask 后端：克隆仓库、pip 安装依赖，再通过 gunicorn 启动服务。这份文档为后续代码导览提供业务背景与本地运行路径。

**相关节点**：`document:README.md`

### 步骤 2：应用启动入口

manage.py 是运行时入口：调用应用工厂创建 Flask 实例、启用 CORS，并挂载 Bug 图片等静态资源。README 中的 gunicorn 命令最终指向这里的 app 对象，是整条依赖链 BFS 遍历的起点。

**相关节点**：`file:manage.py`

### 步骤 3：Flask 应用工厂

app/__init__.py 中的 create_app 负责组装应用：在 /it/api 前缀下注册 API 蓝图，并初始化 flask_docs 自动文档。理解这一层后，你就知道 HTTP 请求如何进入后续的 views 与各域控制器。

**相关节点**：`file:app/__init__.py`

### 步骤 4：配置与数据库会话

const.py 集中存放环境常量（数据库、JWT、外部服务等），被全项目高频引用；common/sqlSession.py 封装 SQLAlchemy 会话与事务原语，是 DAO 层访问 PostgreSQL 的统一入口。二者构成数据层之前的基础设施。

> **知识点**：Python 项目常用单一 const 模块集中配置；SQLAlchemy 通过会话（Session）管理单元工作与提交，避免在控制器中直接操作 Engine。

**相关节点**：`file:const.py`、`file:common/sqlSession.py`

### 步骤 5：API 路由总览

views.py 是蓝图的核心枢纽：fan-out 最高，将 /it/api 下的大量 REST 路径映射到用例、计划、自动化、Mock、RBAC 等各域控制器。阅读本文件可一次性把握整个 HTTP 面的模块划分与命名约定。

**相关节点**：`file:app/api/views.py`

### 步骤 6：认证与统一响应

authMiddleware.py 提供 JWT 签发、login_required 装饰器及权限校验钩子，在请求进入控制器前完成身份鉴别；common/apiResponse.py 则统一成功/失败 JSON 结构与序列化规则。二者共同保证 API 行为一致且可审计。

> **知识点**：Flask 装饰器（decorator）可在视图执行前注入认证逻辑；将 Token 校验与业务处理分离，是 Web API 的常见分层模式。

**相关节点**：`file:app/api/utils/authMiddleware.py`、`file:common/apiResponse.py`

### 步骤 7：测试用例域

用例模块遵循 Controller → Service → Model 分层：caseController 暴露模块/用例/快照/评审接口，caseService 薄封装 DAO 调用，caseModel 定义 Module、TestCase 等 ORM 实体。这是测试管理最核心的领域模型，计划与自动化均会引用用例数据。

**相关节点**：`file:app/api/controller/caseController.py`、`file:app/api/service/caseService.py`、`file:app/api/model/caseModel.py`

### 步骤 8：测试计划域

在掌握用例模型后，planController 负责测试计划、执行轮次与计划用例的 CRUD 及进度查询；planService 编排业务，planModel 映射计划相关表结构。计划层把离散用例组织成可执行的测试批次，衔接手工测试与后续自动化触发。

**相关节点**：`file:app/api/controller/planController.py`、`file:app/api/service/planService.py`、`file:app/api/model/planModel.py`

### 步骤 9：自动化执行

automationController 与 automationService 实现 Jenkins/pytest 驱动的执行生命周期：创建执行单、触发流水线、接收回调并汇总结果；automationModel 对应 ORM，而 automation_api_doc 与 automation_execution_pgsql 脚本分别描述对外 REST 契约与 auto_execution 主从表结构。

**相关节点**：`file:app/api/controller/automationController.py`、`file:app/api/service/automationService.py`、`file:app/api/model/automationModel.py`、`document:resources/automation_api_doc.md`、`table:resources/sql/automation_execution_pgsql.sql:auto_execution`

### 步骤 10：智能 Mock 服务

Mock 子系统从文档解析到运行时匹配：mockController 暴露文档导入与场景配置接口，mockService 协调解析、模板渲染与状态机，mockModel 映射文档/接口/场景实体；mock_service_pgsql.sql 则一次性定义表结构与 RBAC 种子，是理解 Mock 数据模型的权威来源。

**相关节点**：`file:app/api/controller/mockController.py`、`file:app/api/service/mockService.py`、`file:app/api/model/mockModel.py`、`table:resources/sql/mock_service_pgsql.sql:schema`

### 步骤 11：RBAC 权限体系

rbacController、rbacService 与 rbacModel 实现角色、权限码、菜单树及多对多分配；RBAC_API.md 汇总对外 REST 契约与联调示例。该模块为项目、自动化、Mock 等特性提供统一的访问控制基础，与 Step 6 的 JWT 中间件配合完成鉴权闭环。

**相关节点**：`file:app/api/controller/rbacController.py`、`file:app/api/service/rbacService.py`、`file:app/api/model/rbacModel.py`、`document:.agents/RBAC_API.md`

### 步骤 12：生产部署与 CI

本地开发用 gunicorn.conf.py 配置 worker 与绑定；Dockerfile 将应用打包为 Python 3.10 镜像并以 Gunicorn 启动 manage:app；Jenkinsfile 声明拉代码、构建推送 Harbor、SSH 部署与健康检查的完整流水线。三步串联起从 README 命令到线上容器的交付路径。

> **知识点**：Gunicorn 作为 WSGI 服务器托管 Flask 应用；Dockerfile 的 CMD 通常引用 gunicorn.conf；Jenkins 声明式流水线用 stage 串联构建与部署，实现可重复的发布流程。

**相关节点**：`file:gunicorn.conf.py`、`service:Dockerfile`、`file:Jenkinsfile`

## 复杂度热点

- **app/api/controller/updateSqlProjectController.py**（API层）— SQL 项目更新控制器，处理智能 SQL 项目的创建、查询、删除与远程执行。
- **app/api/service/automationService.py**（服务层）— 自动化测试核心业务服务：创建执行记录、触发 Jenkins、接收回调并汇总执行结果。
- **app/api/service/jenkinsPollService.py**（服务层）— Jenkins 构建状态轮询服务，根据构建 API 同步 AutoExecution 与用例执行状态。
- **app/api/controller/bugController.py**（API层）— 缺陷管理 HTTP 控制器，提供缺陷 CRUD、评论、历史、统计及附件上传等 API。
- **app/api/controller/caseController.py**（API层）— 测试用例与模块树 HTTP 控制器，覆盖用例、快照、评审、导入及模块维护。
- **app/api/controller/documentSourceController.py**（API层）— 文档源 HTTP 控制器，管理需求/设计文档的上传、刷新、AI 生成用例与模块匹配导入。
- **app/api/service/documentSourceService.py**（服务层）— 文档源核心服务：飞书/PDF 拉取、AI 批量生成用例、模块匹配与导入编排。
- **app/api/service/skillService.py**（服务层）— 技能与业务规则服务，负责文件落盘、编码生成、CRUD 及 AI 辅助标签规范化。
- **app/api/controller/projectController.py**（API层）— 项目控制器，管理项目、环境、成员与 Webhook，并集成 RBAC 权限校验。
- **app/api/controller/rbacController.py**（API层）— RBAC 控制器，提供角色、权限、菜单及角色-权限/菜单分配接口。
- **app/api/dao/rbacDao.py**（数据层）— RBAC 数据访问层，封装角色、权限、菜单及其关联表的 SQLAlchemy 查询。
- **app/api/utils/authMiddleware.py**（API层）— JWT 认证中间件，提供 Token 签发/校验装饰器与权限检查能力。
- **app/api/views.py**（API层）— Flask API 蓝图入口，集中定义全部 REST 路由并委托至各域控制器。
- **app/api/service/aiService.py**（服务层）— 中央 AI 集成服务，封装 LLM 对话补全、JSON 提取、测试用例生成、技能/规则内容及文档分块。
- **app/api/service/mockDataGeneratorService.py**（服务层）— 基于 Faker 与可选 AI，从 API Schema 生成默认 Mock 场景、请求示例与响应模板。
- **app/api/service/mockParserService.py**（服务层）— 解析 OpenAPI、YApi、手动 JSON 及文本/docx 源，归一化为 Mock 接口定义，并支持 AI 回退解析。
- **app/api/service/mockService.py**（服务层）— Mock 核心编排：文档导入流水线、接口/场景管理、日志记录与 HTTP 运行时响应组装。
- **config/skills/skill-creator/scripts/generate_report.py**（配置层）— 将技能评估 JSON 数据渲染为可自动刷新的 HTML 报告，供 skill-creator 迭代优化流程查看训练/测试结果。
- **config/skills/skill-creator/scripts/run_eval.py**（配置层）— 对评估集并行执行 Claude 查询，统计技能描述触发率，是 skill-creator 评估流水线的核心执行器。
- **config/skills/skill-creator/scripts/run_loop.py**（配置层）— 编排评估、描述优化与 HTML 报告生成的完整迭代循环，是 skill-creator 自动化调优的主入口脚本。
- **app/api/controller/projectHookController.py**（API层）— 项目 Webhook 控制器，提供钩子配置的 CRUD 及向飞书、钉钉、企业微信发送通知的能力。
- **.plan/1ZFcjkLpHmrHbluVoOtA4.md**（文档层）— pytest 与 Jenkins 自动化执行接入的完整后端设计，涵盖 auto_execution 表结构、MVC 分层职责、触发/拉取/回调接口、状态流转、Jenkins 参数与联调示例，可直接交付 AI 编码落地。
- **.plan/YCGiVLWod2rghU8nT3fEv.md**（文档层）— 角色/用户/菜单 RBAC 详细设计，定义 user、role、permission、menu 及关联表 schema，并规划 userModel/rbacModel、DAO、Service、Controller 与 views 路由清单，仅输出设计不改业务代码。
- **config/skills/skill-creator/agents/analyzer.md**（文档层）— 定义事后分析（Post-hoc Analyzer）智能体：在盲评比较出胜负后，对照技能文件与执行 transcript，分析获胜原因并生成可操作的改进建议；另含基准测试结果聚合分析流程。
- **resources/automation_api_doc.md**（文档层）— 自动化执行 REST API 接口文档，涵盖单条/计划触发、执行记录查询、状态枚举及 Jenkins/pytest 内部回调说明，供前端与联调使用。

## 统计

- 节点：349 · 边：772 · 分层：9 · 导览：12 步
