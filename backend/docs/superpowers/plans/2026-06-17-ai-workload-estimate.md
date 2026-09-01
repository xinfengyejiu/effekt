# AI工作量预估 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增一个独立菜单“AI工作量预估”，基于本次勾选的 PRD 文档生成测试用例数量、测试设计工时、QA 执行工时、总工时和 Token 消耗预估，并支持单人负责人分配、列表查询、详情追溯和人工确认。

**Architecture:** 后端沿用当前 `Controller -> Service -> DAO/Model -> views.py` 模式，新增独立 `ai_workload_estimate*` 业务表，复用现有 `DocumentSource` 需求问答文档链路、项目成员接口和 `AIService`。前端新增独立 `AIWorkloadEstimate` 页面组，只在左侧新增一个菜单“AI工作量预估”，挂在现有 `AI质量助手` 分组下。

**Tech Stack:** Flask, SQLAlchemy, PostgreSQL JSONB, Vue2, Element UI, existing `AIService`, existing `DocumentSource` / `Product` / `Project` / `ProjectMember` models, existing knowledge document APIs.

**Design Spec:** `docs/superpowers/specs/2026-06-17-ai-workload-estimate-design.md`

**Commit Policy:** 本计划执行过程中不自动提交 git，由用户明确要求后再提交。

---

## Summary

本功能拆成 9 个小功能点：

1. 数据库表与菜单权限
2. 后端模型与 DAO
3. PRD 上下文与历史参考聚合
4. AI 预估执行服务
5. 单人负责人分配
6. Controller 与路由
7. 前端 API、路由与菜单
8. 前端列表与新建页面
9. 前端详情页与操作闭环

---

## Public Interfaces

新增后端接口：

```text
POST /ai/workload-estimate/create
GET  /ai/workload-estimate/list
GET  /ai/workload-estimate/detail
POST /ai/workload-estimate/execute
POST /ai/workload-estimate/assign
POST /ai/workload-estimate/confirm
POST /ai/workload-estimate/retry
```

复用现有文档接口：

```text
GET  /knowledge/document/list
POST /knowledge/document/upload
POST /knowledge/document/parse
GET  /project/member/list
```

新增权限码：

```text
ai_workload_estimate:list
ai_workload_estimate:create
ai_workload_estimate:detail
ai_workload_estimate:execute
ai_workload_estimate:assign
ai_workload_estimate:confirm
```

预估状态固定为：

```text
draft       草稿
estimating  预估中
completed   预估完成
failed      预估失败
confirmed   人工确认
archived    归档
```

AI 输出必须为结构化 JSON，字段固定：

```json
{
  "summary": "本次预估摘要",
  "complexityLevel": "high",
  "confidence": "medium",
  "totalFunctionPoints": 28,
  "totalCaseCount": 240,
  "totalEffortHours": 100,
  "caseDesignHours": 43,
  "qaExecutionHours": 57,
  "estimatedTokens": 180000,
  "modules": [],
  "functionPoints": [],
  "risks": [],
  "assumptions": [],
  "referenceEvidence": []
}
```

---

## File Structure

新增后端文件：

```text
app/api/model/aiWorkloadEstimateModel.py
app/api/dao/aiWorkloadEstimateDao.py
app/api/service/aiWorkloadEstimateContextService.py
app/api/service/aiWorkloadEstimateService.py
app/api/controller/aiWorkloadEstimateController.py
resources/sql/ai_workload_estimate_pgsql.sql
resources/sql/ai_workload_estimate_menu_permission.sql
```

修改后端文件：

```text
app/api/views.py
```

新增前端文件：

```text
D:\zhyy\effekt-interface-frontend\src\api\aiWorkloadEstimateApi.js
D:\zhyy\effekt-interface-frontend\src\components\AIWorkloadEstimate\EstimateList.vue
D:\zhyy\effekt-interface-frontend\src\components\AIWorkloadEstimate\EstimateCreate.vue
D:\zhyy\effekt-interface-frontend\src\components\AIWorkloadEstimate\EstimateDetail.vue
```

修改前端文件：

```text
D:\zhyy\effekt-interface-frontend\src\router\index.js
D:\zhyy\effekt-interface-frontend\src\components\Home.vue
```

---

## Task 1: 数据库表与菜单权限

**Files:**
- Create: `resources/sql/ai_workload_estimate_pgsql.sql`
- Create: `resources/sql/ai_workload_estimate_menu_permission.sql`

- [x] 创建 `ai_workload_estimate` 主表，字段包含 `estimate_no/title/product_id/product_name/project_id/project_name/owner_id/owner_name/document_ids/reference_document_ids/prd_snapshot/reference_summary/result_summary/raw_ai_output/failure_reason/complexity_level/confidence/total_function_points/total_case_count/case_design_hours/qa_execution_hours/total_effort_hours/estimated_tokens/status/created_by/assigned_by/assigned_time/confirmed_by/confirmed_time/confirm_info/is_delete/created_time/updated_time`。
- [x] 创建 `ai_workload_estimate_module` 模块明细表，字段包含 `estimate_id/module_name/description/complexity_level/function_point_count/case_count/case_design_hours/qa_execution_hours/total_hours/risk_summary/sort_order/created_time/updated_time`。
- [x] 创建 `ai_workload_estimate_function` 功能点明细表，字段包含 `estimate_id/module_id/module_name/function_name/description/test_scope/positive_case_count/negative_case_count/boundary_case_count/permission_case_count/integration_case_count/case_count/complexity_reason/case_design_hours/qa_execution_hours/total_hours/estimated_tokens/risk_level/sort_order/created_time/updated_time`。
- [x] 为 `estimate_no/product_id/project_id/owner_id/status/complexity_level/created_time` 建索引。
- [x] 菜单新增“AI工作量预估”，只新增一个左侧菜单入口，路径为 `/ai-workload-estimate`。
- [x] 菜单挂在现有 `AI质量助手` 分组下，与 `需求问答`、`AI测试评审`、`测试资产治理`、`精准测试` 保持同类归属。
- [x] 权限和菜单 SQL 写入 `sys_permission/sys_menu/sys_role_permission/sys_role_menu`，不要写旧表 `permission/menu/role_permission/role_menu`。
- [x] SQL 使用 `CREATE TABLE IF NOT EXISTS`、`CREATE INDEX IF NOT EXISTS`、`ON CONFLICT`，保证重复执行不报错。

SQL 核心表结构参考：

```sql
CREATE TABLE IF NOT EXISTS public.ai_workload_estimate (
    id BIGSERIAL PRIMARY KEY,
    estimate_no VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    product_id BIGINT NOT NULL,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    owner_id BIGINT,
    owner_name VARCHAR(128),
    document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    reference_document_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    prd_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
    reference_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_ai_output JSONB NOT NULL DEFAULT '{}'::jsonb,
    failure_reason TEXT,
    complexity_level VARCHAR(32),
    confidence VARCHAR(32),
    total_function_points INTEGER DEFAULT 0,
    total_case_count INTEGER DEFAULT 0,
    case_design_hours NUMERIC(10,2) DEFAULT 0,
    qa_execution_hours NUMERIC(10,2) DEFAULT 0,
    total_effort_hours NUMERIC(10,2) DEFAULT 0,
    estimated_tokens BIGINT DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    created_by BIGINT,
    assigned_by BIGINT,
    assigned_time TIMESTAMP,
    confirmed_by BIGINT,
    confirmed_time TIMESTAMP,
    confirm_info JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.ai_workload_estimate_module (
    id BIGSERIAL PRIMARY KEY,
    estimate_id BIGINT NOT NULL,
    module_name VARCHAR(128) NOT NULL,
    description TEXT,
    complexity_level VARCHAR(32),
    function_point_count INTEGER DEFAULT 0,
    case_count INTEGER DEFAULT 0,
    case_design_hours NUMERIC(10,2) DEFAULT 0,
    qa_execution_hours NUMERIC(10,2) DEFAULT 0,
    total_hours NUMERIC(10,2) DEFAULT 0,
    risk_summary JSONB NOT NULL DEFAULT '[]'::jsonb,
    sort_order INTEGER DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.ai_workload_estimate_function (
    id BIGSERIAL PRIMARY KEY,
    estimate_id BIGINT NOT NULL,
    module_id BIGINT,
    module_name VARCHAR(128),
    function_name VARCHAR(255) NOT NULL,
    description TEXT,
    test_scope TEXT,
    positive_case_count INTEGER DEFAULT 0,
    negative_case_count INTEGER DEFAULT 0,
    boundary_case_count INTEGER DEFAULT 0,
    permission_case_count INTEGER DEFAULT 0,
    integration_case_count INTEGER DEFAULT 0,
    case_count INTEGER DEFAULT 0,
    complexity_reason TEXT,
    case_design_hours NUMERIC(10,2) DEFAULT 0,
    qa_execution_hours NUMERIC(10,2) DEFAULT 0,
    total_hours NUMERIC(10,2) DEFAULT 0,
    estimated_tokens BIGINT DEFAULT 0,
    risk_level VARCHAR(32),
    sort_order INTEGER DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Verify:

```powershell
Select-String -Path resources\sql\ai_workload_estimate_pgsql.sql -Pattern "ai_workload_estimate"
Select-String -Path resources\sql\ai_workload_estimate_menu_permission.sql -Pattern "ai_workload_estimate"
Select-String -Path resources\sql\ai_workload_estimate_menu_permission.sql -Pattern "sys_permission"
```

---

## Task 2: 后端模型与 DAO

**Files:**
- Create: `app/api/model/aiWorkloadEstimateModel.py`
- Create: `app/api/dao/aiWorkloadEstimateDao.py`

- [x] 定义 `AiWorkloadEstimate`、`AiWorkloadEstimateModule`、`AiWorkloadEstimateFunction` 三个 SQLAlchemy model，字段和 Task 1 表结构一致。
- [x] JSONB 字段使用 PostgreSQL JSONB 类型，默认值与数据库默认值保持一致。
- [x] DAO 支持创建预估任务、更新预估任务、按 ID 查询任务、按编号查询任务。
- [x] DAO 支持列表分页，默认按 `created_time desc` 排序。
- [x] DAO 列表过滤条件支持 `productId/projectId/productName/projectName/ownerId/status/complexityLevel/confidence/keyword/startTime/endTime`。
- [x] `productName` 和 `projectName` 必须使用模糊查询。
- [x] `keyword` 匹配 `estimate_no/title/owner_name`。
- [x] DAO 支持详情聚合，返回 estimate、modules、functions 三类数据。
- [x] DAO 支持先删除或软删除旧 modules/functions，再批量写入新的模块和功能点明细。
- [x] DAO 支持负责人分配字段更新：`owner_id/owner_name/assigned_by/assigned_time`。

Model 关键代码结构：

```python
class AiWorkloadEstimate(Base):
    __tablename__ = 'ai_workload_estimate'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    estimate_no = Column(String(64), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    product_id = Column(BigInteger, nullable=False)
    product_name = Column(String(128))
    project_id = Column(BigInteger, nullable=False)
    project_name = Column(String(128))
    owner_id = Column(BigInteger)
    owner_name = Column(String(128))
    document_ids = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    reference_document_ids = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    prd_snapshot = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    reference_summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    result_summary = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    raw_ai_output = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    failure_reason = Column(Text)
    complexity_level = Column(String(32))
    confidence = Column(String(32))
    total_function_points = Column(Integer, default=0)
    total_case_count = Column(Integer, default=0)
    case_design_hours = Column(Numeric(10, 2), default=0)
    qa_execution_hours = Column(Numeric(10, 2), default=0)
    total_effort_hours = Column(Numeric(10, 2), default=0)
    estimated_tokens = Column(BigInteger, default=0)
    status = Column(String(32), nullable=False, default='draft')
    created_by = Column(BigInteger)
    assigned_by = Column(BigInteger)
    assigned_time = Column(TIMESTAMP)
    confirmed_by = Column(BigInteger)
    confirmed_time = Column(TIMESTAMP)
    confirm_info = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
```

Verify:

```powershell
python -m py_compile app/api/model/aiWorkloadEstimateModel.py app/api/dao/aiWorkloadEstimateDao.py
```

---

## Task 3: PRD 上下文与历史参考聚合

**Files:**
- Create: `app/api/service/aiWorkloadEstimateContextService.py`

- [x] 实现 `build_context(session, estimate)`，输出统一上下文：`currentPrds/referenceDocuments/referenceSummary/rawText/statistics`。
- [x] 根据 `estimate.document_ids` 读取本次勾选的 `DocumentSource`，只允许读取同 `product_id/project_id` 且未删除的文档。
- [x] 本次 PRD 是预估范围的唯一来源，只有 `document_ids` 对应文档进入模块拆解、功能点拆解、用例数量和工时估算。
- [x] 文档必须有 `content`，没有解析内容时抛出明确异常：`本次PRD未解析，请先在需求问答中解析文档`。
- [x] 读取本次 PRD 的 `id/source/type/version/status/content/created_by/created_time`，写入 `prd_snapshot`。
- [x] 按产品维度读取历史需求问答文档作为复杂度参考，过滤掉本次 `document_ids`，限制数量为最近 10 份。
- [x] 历史文档只进入 `referenceDocuments/referenceSummary`，不能拼入本次范围正文。
- [x] 历史参考摘要包含相似模块、复杂度关键词、常见风险，不直接增加功能点和用例数量。
- [x] 输出 `rawText` 时只拼接本次 PRD 内容，保证 AI 范围输入不被历史文档污染。

上下文输出结构：

```python
{
    'currentPrds': [
        {
            'id': 1,
            'source': 'joyhub-v2.12-prd.docx',
            'type': 'requirement',
            'version': 'v1',
            'content': '订单取消、退款审批、库存回滚等本次需求正文',
            'contentLength': 12000
        }
    ],
    'referenceDocuments': [
        {
            'id': 2,
            'source': '历史需求.docx',
            'type': 'requirement',
            'summary': '仅用于复杂度参考的摘要'
        }
    ],
    'referenceSummary': {
        'documentCount': 10,
        'riskKeywords': ['权限', '状态流转', '导入导出'],
        'note': '历史文档仅用于复杂度参考，不作为本次范围'
    },
    'rawText': '订单取消、退款审批、库存回滚等本次需求正文',
    'statistics': {
        'currentPrdCount': 1,
        'rawTextLength': 12000,
        'referenceDocumentCount': 10
    }
}
```

Verify:

```powershell
python -m py_compile app/api/service/aiWorkloadEstimateContextService.py
```

---

## Task 4: AI 预估执行服务

**Files:**
- Create: `app/api/service/aiWorkloadEstimateService.py`

- [x] 实现 `create_estimate(session, req_data, user_id=None)`，校验 `productId/projectId/title/documentIds`，生成 `AWEYYYYMMDDHHMMSS + 4位随机数` 编号并保存 `draft` 任务。
- [x] 创建时保存 `owner_id/owner_name`；如果项目暂无成员，允许负责人为空并在返回值中显示 `未分配`。
- [x] 实现 `list_estimates(session, req_data)`，透传 DAO 列表过滤和分页。
- [x] 实现 `estimate_detail(session, estimate_id)`，返回主表、模块明细、功能点明细、PRD 快照、历史参考、结果摘要。
- [x] 实现 `execute_estimate(session, estimate_id, user_id=None)`，状态改为 `estimating`，聚合上下文，调用现有 `AIService.request_json`。
- [x] AI prompt 必须明确：本次 PRD 是唯一范围，历史文档只可作为复杂度参考。
- [x] AI 返回 JSON 不合法时保存 `raw_ai_output/failure_reason`，并走本地兜底预估，不让任务永久卡在 `estimating`。
- [x] 实现 `_build_fallback_result(context, error_message=None)`，按 PRD 长度、功能关键词、复杂度关键词生成本地兜底结论。
- [x] 实现 `_calibrate_result(result, context)`，用以下规则校准：
  - 平均每天 40-50 条测试用例作为产能参考。
  - 参考样本：240 条功能用例对应测试设计和 QA 时间约 100 小时。
  - 高复杂度功能增加设计工时系数。
  - 涉及权限、支付、状态机、批量、导入导出、消息通知、跨端一致性的功能增加风险系数。
  - 总工时不能低于模块和功能点明细累计值。
  - Token 预估按 PRD 长度、拆解深度和生成轮次估算。
- [x] 将 AI 或兜底结果拆成 `ai_workload_estimate_module` 和 `ai_workload_estimate_function` 明细。
- [x] 执行成功后写入 `result_summary/raw_ai_output/complexity_level/confidence/total_function_points/total_case_count/case_design_hours/qa_execution_hours/total_effort_hours/estimated_tokens/status=completed`。
- [x] 执行失败且兜底也不可用时写入 `status=failed/failure_reason`。
- [x] 实现 `retry_estimate(session, estimate_id, user_id=None)`，允许 `failed/completed` 状态重新预估，重新生成明细。
- [x] 实现 `confirm_estimate(session, req_data, user_id=None)`，状态改为 `confirmed`，写入 `confirmed_by/confirmed_time/confirm_info`。

服务接口结构：

```python
class AiWorkloadEstimateService:
    @staticmethod
    def create_estimate(session, req_data, user_id=None):
        pass

    @staticmethod
    def list_estimates(session, req_data):
        pass

    @staticmethod
    def estimate_detail(session, estimate_id):
        pass

    @staticmethod
    def execute_estimate(session, estimate_id, user_id=None):
        pass

    @staticmethod
    def retry_estimate(session, estimate_id, user_id=None):
        pass

    @staticmethod
    def confirm_estimate(session, req_data, user_id=None):
        pass
```

Verify:

```powershell
python -m py_compile app/api/service/aiWorkloadEstimateService.py
```

---

## Task 5: 单人负责人分配

**Files:**
- Modify: `app/api/service/aiWorkloadEstimateService.py`

- [x] 实现 `assign_owner(session, req_data, user_id=None)`，入参包含 `estimateId/ownerId`。
- [x] 根据预估单的 `project_id` 校验负责人是否属于当前项目成员；如果 `ProjectMember` 表没有该项目成员记录，则返回失败。
- [x] 如果项目暂无成员，允许 `ownerId` 为空，保存为未分配。
- [x] 分配成功后更新 `owner_id/owner_name/assigned_by/assigned_time`。
- [x] 列表和详情返回时统一补充 `ownerNameDisplay`，为空时返回 `未分配`。
- [x] 不做多人分配、资源日历和排期计算。

负责人分配接口结构：

```python
@staticmethod
def assign_owner(session, req_data, user_id=None):
    estimate_id = req_data.get('estimateId')
    owner_id = req_data.get('ownerId')
    if not estimate_id:
        raise ValueError('estimateId不能为空')
    estimate = AiWorkloadEstimateDao.get_by_id(session, estimate_id)
    if not estimate:
        raise ValueError('预估记录不存在')
    # 读取 ProjectMember 校验 owner_id 属于 estimate.project_id
    # 更新 owner_id、owner_name、assigned_by、assigned_time
```

Verify:

```powershell
python -m py_compile app/api/service/aiWorkloadEstimateService.py
```

---

## Task 6: Controller 与路由

**Files:**
- Create: `app/api/controller/aiWorkloadEstimateController.py`
- Modify: `app/api/views.py`

- [x] Controller 方法：`estimate_create/estimate_list/estimate_detail/estimate_execute/estimate_assign/estimate_confirm/estimate_retry`。
- [x] Controller 读取 GET 参数和 POST JSON 时保持现有控制器风格，返回使用项目已有 `_ai_response` 或 `ApiResponse.build_success/build_failure` 风格，和周边 AI 接口保持一致。
- [x] `views.py` 导入 `AiWorkloadEstimateController`。
- [x] 注册 `/ai/workload-estimate/*` 路由。
- [x] 所有接口加 `login_required`。
- [x] 所有接口加对应 `permission_required('ai_workload_estimate:*')`。
- [x] `detail/retry/confirm/assign` 对不存在的预估单返回明确失败信息。

路由映射：

```python
app.add_url_rule(
    '/ai/workload-estimate/create',
    view_func=login_required(permission_required('ai_workload_estimate:create')(AiWorkloadEstimateController.estimate_create)),
    methods=['POST']
)
app.add_url_rule(
    '/ai/workload-estimate/list',
    view_func=login_required(permission_required('ai_workload_estimate:list')(AiWorkloadEstimateController.estimate_list)),
    methods=['GET']
)
app.add_url_rule(
    '/ai/workload-estimate/detail',
    view_func=login_required(permission_required('ai_workload_estimate:detail')(AiWorkloadEstimateController.estimate_detail)),
    methods=['GET']
)
app.add_url_rule(
    '/ai/workload-estimate/execute',
    view_func=login_required(permission_required('ai_workload_estimate:execute')(AiWorkloadEstimateController.estimate_execute)),
    methods=['POST']
)
app.add_url_rule(
    '/ai/workload-estimate/assign',
    view_func=login_required(permission_required('ai_workload_estimate:assign')(AiWorkloadEstimateController.estimate_assign)),
    methods=['POST']
)
app.add_url_rule(
    '/ai/workload-estimate/confirm',
    view_func=login_required(permission_required('ai_workload_estimate:confirm')(AiWorkloadEstimateController.estimate_confirm)),
    methods=['POST']
)
app.add_url_rule(
    '/ai/workload-estimate/retry',
    view_func=login_required(permission_required('ai_workload_estimate:execute')(AiWorkloadEstimateController.estimate_retry)),
    methods=['POST']
)
```

Verify:

```powershell
python -m py_compile app/api/controller/aiWorkloadEstimateController.py app/api/views.py
```

---

## Task 7: 前端 API、路由与菜单

**Files:**
- Create: `D:\zhyy\effekt-interface-frontend\src\api\aiWorkloadEstimateApi.js`
- Modify: `D:\zhyy\effekt-interface-frontend\src\router\index.js`
- Modify: `D:\zhyy\effekt-interface-frontend\src\components\Home.vue`

- [x] 新增前端 API 方法覆盖所有 `/ai/workload-estimate/*` 接口。
- [x] 新增路由：
  - `/ai-workload-estimate`
  - `/ai-workload-estimate/create`
  - `/ai-workload-estimate/detail`
- [x] 页面组件路径使用 `@/components/AIWorkloadEstimate/EstimateList`、`EstimateCreate`、`EstimateDetail`。
- [x] 左侧菜单只显示 `/ai-workload-estimate` 一个入口，不把创建页和详情页展示为左侧菜单。
- [x] `Home.vue` 将“AI工作量预估”归入现有 `AI质量助手` 分组。
- [x] 菜单排序建议放在 `需求问答`、`AI测试评审`、`测试资产治理`、`精准测试` 附近。
- [x] 不继续扩展 `AiPlatform.vue` 或其他旧大页面。

API 文件结构：

```javascript
import request from '@/utils/request'

export function createWorkloadEstimate(data) {
  return request({ url: '/ai/workload-estimate/create', method: 'post', data })
}

export function getWorkloadEstimateList(params) {
  return request({ url: '/ai/workload-estimate/list', method: 'get', params })
}

export function getWorkloadEstimateDetail(params) {
  return request({ url: '/ai/workload-estimate/detail', method: 'get', params })
}

export function executeWorkloadEstimate(data) {
  return request({ url: '/ai/workload-estimate/execute', method: 'post', data })
}

export function assignWorkloadEstimateOwner(data) {
  return request({ url: '/ai/workload-estimate/assign', method: 'post', data })
}

export function confirmWorkloadEstimate(data) {
  return request({ url: '/ai/workload-estimate/confirm', method: 'post', data })
}

export function retryWorkloadEstimate(data) {
  return request({ url: '/ai/workload-estimate/retry', method: 'post', data })
}
```

Verify:

```powershell
Select-String -Path D:\zhyy\effekt-interface-frontend\src\router\index.js -Pattern "ai-workload-estimate"
Select-String -Path D:\zhyy\effekt-interface-frontend\src\components\Home.vue -Pattern "AI工作量预估"
```

---

## Task 8: 前端列表与新建页面

**Files:**
- Create: `D:\zhyy\effekt-interface-frontend\src\components\AIWorkloadEstimate\EstimateList.vue`
- Create: `D:\zhyy\effekt-interface-frontend\src\components\AIWorkloadEstimate\EstimateCreate.vue`

- [x] 列表页筛选条件包含产品名称、项目名称、负责人、状态、关键词、创建时间范围。
- [x] 产品名称和项目名称使用输入框模糊搜索，参数传 `productName/projectName`。
- [x] 列表表格列包含预估编号、标题、产品名称、项目名称、负责人、PRD 文档数、功能点数、预估用例数、设计工时、QA 工时、总工时、Token 预估、复杂度、置信度、状态、创建时间、操作。
- [x] 列表操作包含查看详情、重新预估、分配负责人、确认预估。
- [x] 分配负责人弹窗调用 `/project/member/list`，只展示当前项目成员，单选负责人。
- [x] 新建页字段包含预估标题、产品、项目、负责人、本次 PRD 文档、备注。
- [x] 新建页选择产品后加载项目；选择项目后加载项目成员和该产品项目下的需求问答文档。
- [x] 本次 PRD 文档使用复选框选择，至少选择 1 个已解析成功文档。
- [x] 上传和解析文档复用现有 `/knowledge/document/upload`、`/knowledge/document/parse` 链路。
- [x] 未解析成功的文档禁用勾选，并展示需要先解析的状态。
- [x] 新建成功后跳转详情页，详情页可执行 AI 预估。

列表查询参数：

```javascript
{
  page: 1,
  size: 10,
  productName: '',
  projectName: '',
  ownerId: '',
  status: '',
  keyword: '',
  startTime: '',
  endTime: ''
}
```

Verify:

```powershell
npm.cmd --prefix D:\zhyy\effekt-interface-frontend run build
```

---

## Task 9: 前端详情页与操作闭环

**Files:**
- Create: `D:\zhyy\effekt-interface-frontend\src\components\AIWorkloadEstimate\EstimateDetail.vue`

- [x] 展示基础信息：预估编号、标题、产品、项目、负责人、状态、创建人、创建时间。
- [x] 展示负责人信息：当前负责人、分配人、分配时间，支持重新分配负责人。
- [x] 展示预估总览：复杂度、置信度、功能点数、用例总数、测试设计工时、QA 执行工时、总工时、Token 预估。
- [x] 展示本次 PRD：文档名称、版本、状态、内容长度，明确标记“本次 PRD 是预估范围”。
- [x] 展示历史参考：历史文档数、风险关键词、参考说明，明确标记“历史文档仅用于复杂度参考”。
- [x] 展示模块明细表：模块名称、复杂度、功能点数、用例数、设计工时、QA 工时、总工时、风险摘要。
- [x] 展示功能点明细表：模块、功能点、测试范围、正向/反向/边界/权限/集成用例数、总用例数、设计工时、QA 工时、Token 预估、风险等级。
- [x] 展示风险与假设：`result_summary.risks` 和 `result_summary.assumptions`。
- [x] 提供“执行AI预估”“重新预估”“确认预估”“分配负责人”按钮，并有 loading 状态。
- [x] 预估失败时展示 `failure_reason`，并允许重新预估。
- [x] 人工确认弹窗支持填写确认备注，提交后刷新详情状态为 `confirmed`。
- [x] 详情页刷新后仍能看到 modules 和 functions 明细。

详情页数据结构期望：

```javascript
{
  estimate: {},
  modules: [],
  functions: [],
  prdSnapshot: [],
  referenceSummary: {},
  resultSummary: {}
}
```

Verify:

```powershell
npm.cmd --prefix D:\zhyy\effekt-interface-frontend run build
```

---

## Test Plan

- [x] SQL 检查：

```powershell
Select-String -Path resources\sql\ai_workload_estimate_pgsql.sql -Pattern "ai_workload_estimate"
Select-String -Path resources\sql\ai_workload_estimate_menu_permission.sql -Pattern "sys_menu"
Select-String -Path resources\sql\ai_workload_estimate_menu_permission.sql -Pattern "ai_workload_estimate:list"
```

- [x] 后端编译：

```powershell
python -m py_compile `
  app/api/model/aiWorkloadEstimateModel.py `
  app/api/dao/aiWorkloadEstimateDao.py `
  app/api/service/aiWorkloadEstimateContextService.py `
  app/api/service/aiWorkloadEstimateService.py `
  app/api/controller/aiWorkloadEstimateController.py `
  app/api/views.py
```

- [x] 前端构建：

```powershell
npm.cmd --prefix D:\zhyy\effekt-interface-frontend run build
```

- [ ] API 冒烟场景：

```text
创建预估 -> 查看详情 -> 执行AI预估 -> 查看模块和功能点明细 -> 分配负责人 -> 确认预估
失败预估 -> 查看失败原因 -> 重新预估 -> 状态变为 completed
产品名称模糊查询 -> 返回匹配预估记录
项目名称模糊查询 -> 返回匹配预估记录
本次 PRD 未解析 -> 禁止执行预估并返回明确提示
```

- [ ] 页面验收场景：

```text
AI质量助手下显示且只显示一个“AI工作量预估”菜单
点击菜单进入列表页
列表产品名称和项目名称搜索正常
新建页产品、项目、负责人联动正常
新建页能勾选本次PRD，未解析文档不能勾选
详情页能展示总览、PRD、历史参考、模块明细、功能点明细
历史参考不会被展示成本次预估范围
分配负责人后列表和详情同步刷新
确认预估后状态变为 confirmed
无权限用户不能创建、执行、分配或确认
```

---

## Assumptions

- 第一版只新增一个左侧菜单“AI工作量预估”。
- 第一版只支持单人负责人，不做多人协作分配。
- 第一版负责人从当前项目成员中选择；项目暂无成员时允许为空。
- 第一版本次 PRD 必须由用户上传或从需求问答文档中勾选。
- 第一版本次 PRD 是唯一预估范围，历史文档只用于复杂度参考。
- 第一版历史参考只按同产品检索，不做跨产品参考。
- 第一版不自动生成测试计划，不自动回写测试用例库。
- 第一版不做资源日历、冲刺容量排期和人员负载均衡。
- 第一版 AI 不可用时使用本地兜底和校准规则。
- 本计划执行过程中不提交 git，除非用户后续明确要求提交。
