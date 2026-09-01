# AI测试资产治理中心 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增“AI测试资产治理中心”，对现有测试用例库做重复、低质量、过期、覆盖缺口和未处理 AI 建议的扫描治理，并形成问题闭环。

**Architecture:** 后端沿用当前 `Controller -> Service -> DAO/Model -> views.py` 模式，新增独立 `test_asset_*` 治理表。扫描采用“本地规则优先 + AI摘要增强”的混合模式，保证 AI 不可用时仍能完成治理。前端新增独立 `TestAssetGovernance` 页面组，不继续扩展大型 `CaseList.vue`。

**Tech Stack:** Flask, SQLAlchemy, PostgreSQL JSONB, Vue2, Element UI, existing `AIService`, existing `TestCase` / `Module` / `PlanCase` / `Bug` / `PreciseRecommendation` / `AiTestReviewCaseSuggestion` models.

**OpenSpec Change:** `openspec/changes/add-ai-test-asset-governance`

---

## Summary

本功能拆成 8 个小功能点：

1. 治理扫描任务管理
2. 测试资产上下文聚合
3. 重复用例识别
4. 低质量/过期用例识别
5. 模块覆盖缺口识别
6. AI建议用例待处理识别
7. 治理问题动作闭环
8. 菜单权限与前端页面

---

## Public Interfaces

新增后端接口：

```text
POST /test-asset/governance/scan/create
GET  /test-asset/governance/scan/list
GET  /test-asset/governance/scan/detail
POST /test-asset/governance/scan/execute
GET  /test-asset/governance/issue/list
POST /test-asset/governance/issue/update
POST /test-asset/governance/action/apply
```

新增权限码：

```text
test_asset_governance:list
test_asset_governance:create
test_asset_governance:detail
test_asset_governance:execute
test_asset_governance:issue:update
test_asset_governance:action
```

治理问题类型固定为：

```text
duplicate_case       重复用例
weak_case            低质量用例
stale_case           过期用例
coverage_gap         覆盖缺口
ai_suggestion        AI建议待处理
```

问题状态固定为：

```text
open
accepted
ignored
fixed
reopened
```

动作类型固定为：

```text
keep
merge
improve
deprecate
accept_suggestion
ignore
mark_fixed
reopen
```

扫描摘要结构：

```json
{
  "totalCases": 0,
  "activeCases": 0,
  "aiGeneratedCases": 0,
  "moduleCount": 0,
  "issueCount": 0,
  "issueTypeCounts": {},
  "severityCounts": {},
  "healthScore": 100,
  "summary": "资产健康摘要",
  "recommendedActions": []
}
```

---

## Task 1: 数据库表与菜单权限

**Files:**
- Create: `resources/sql/test_asset_governance_pgsql.sql`

- [x] 创建 `test_asset_scan` 表，字段包含 `scan_no/product_id/product_name/project_id/project_name/title/scan_type/options_json/summary_json/health_score/status/error_message/created_by/started_time/finished_time/is_delete/created_time/updated_time`。
- [x] 创建 `test_asset_issue` 表，字段包含 `scan_id/product_id/project_id/module_id/module_name/issue_type/severity/title/description/evidence_json/suggestion_json/related_case_ids/action_status/assigned_to/resolved_by/resolved_time/is_delete/created_time/updated_time`。
- [x] 创建 `test_asset_action` 表，字段包含 `issue_id/action_type/action_payload/result_payload/status/error_message/created_by/created_time/updated_time`。
- [x] 为 `project_id/status/issue_type/severity/action_status/created_time` 建索引。
- [x] 菜单新增“测试资产治理”，建议挂在“测试平台”或“AI测试评审”附近。
- [x] 权限和菜单 SQL 必须写入 `sys_permission/sys_menu/sys_role_permission/sys_role_menu`，不要使用旧表 `permission/menu/role_permission/role_menu`。
- [x] SQL 使用 `CREATE TABLE IF NOT EXISTS`、`CREATE INDEX IF NOT EXISTS`、`ON CONFLICT`，保证可重复执行。

SQL 核心表结构参考：

```sql
CREATE TABLE IF NOT EXISTS public.test_asset_scan (
    id BIGSERIAL PRIMARY KEY,
    scan_no VARCHAR(64) NOT NULL UNIQUE,
    product_id BIGINT,
    product_name VARCHAR(128),
    project_id BIGINT NOT NULL,
    project_name VARCHAR(128),
    title VARCHAR(255) NOT NULL,
    scan_type VARCHAR(64) NOT NULL DEFAULT 'full',
    options_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    health_score INTEGER,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_by BIGINT,
    started_time TIMESTAMP,
    finished_time TIMESTAMP,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.test_asset_issue (
    id BIGSERIAL PRIMARY KEY,
    scan_id BIGINT NOT NULL,
    product_id BIGINT,
    project_id BIGINT NOT NULL,
    module_id BIGINT,
    module_name VARCHAR(128),
    issue_type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'medium',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    suggestion_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    related_case_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    action_status VARCHAR(32) NOT NULL DEFAULT 'open',
    assigned_to BIGINT,
    resolved_by BIGINT,
    resolved_time TIMESTAMP,
    is_delete INTEGER NOT NULL DEFAULT 0,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.test_asset_action (
    id BIGSERIAL PRIMARY KEY,
    issue_id BIGINT NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    action_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(32) NOT NULL DEFAULT 'success',
    error_message TEXT,
    created_by BIGINT,
    created_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Verify:

```powershell
Select-String -Path resources\sql\test_asset_governance_pgsql.sql -Pattern "test_asset_scan"
Select-String -Path resources\sql\test_asset_governance_pgsql.sql -Pattern "sys_permission"
```

---

## Task 2: 后端模型与 DAO

**Files:**
- Create: `app/api/model/testAssetGovernanceModel.py`
- Create: `app/api/dao/testAssetGovernanceDao.py`

- [x] 定义 `TestAssetScan`、`TestAssetIssue`、`TestAssetAction` 三个 SQLAlchemy model。
- [x] DAO 支持扫描列表分页，默认 `created_time desc`。
- [x] DAO 支持扫描详情聚合，返回 scan、issues、actions。
- [x] DAO 支持问题列表分页，过滤 `scanId/productId/projectId/issueType/severity/actionStatus/keyword`。
- [x] DAO 支持批量写入 issues、创建 action、按 issue 更新状态。

Model 关键代码结构：

```python
class TestAssetScan(Base):
    __tablename__ = 'test_asset_scan'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scan_no = Column(String(64), nullable=False, unique=True)
    product_id = Column(BigInteger)
    product_name = Column(String(128))
    project_id = Column(BigInteger, nullable=False)
    project_name = Column(String(128))
    title = Column(String(255), nullable=False)
    scan_type = Column(String(64), nullable=False, default='full')
    options_json = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    summary_json = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    health_score = Column(Integer)
    status = Column(String(32), nullable=False, default='pending')
    error_message = Column(Text)
    created_by = Column(BigInteger)
    started_time = Column(TIMESTAMP)
    finished_time = Column(TIMESTAMP)
    is_delete = Column(Integer, default=0)
    created_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_time = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), server_onupdate=text('CURRENT_TIMESTAMP'))
```

Verify:

```powershell
python -m py_compile app/api/model/testAssetGovernanceModel.py app/api/dao/testAssetGovernanceDao.py
```

---

## Task 3: 扫描上下文聚合服务

**Files:**
- Create: `app/api/service/testAssetGovernanceService.py`

- [x] 实现 `create_scan(session, req_data, user_id=None)`，生成 `TAGYYYYMMDD...` 编号并保存 pending 任务。
- [x] 实现 `list_scans(session, req_data)` 和 `scan_detail(session, scan_id)`。
- [x] 实现 `_load_context(session, scan)`，读取以下数据：
  - `TestCase`：项目下未删除用例。
  - `Module`：项目下未删除模块。
  - `PlanCase`：按 case_id 聚合最近执行时间、执行次数、失败次数。
  - `Bug`：按 module_id/case_id 聚合缺陷数量和高严重级别缺陷。
  - `PreciseRecommendation`：按 case_id/module_name 聚合精准测试推荐信号。
  - `AiTestReviewCaseSuggestion` + `AiTestReview`：读取 pending AI 建议用例。
- [x] 上下文输出统一 dict：`cases/modules/executionStats/bugStats/preciseSignals/aiSuggestions/options`。

关键聚合接口：

```python
@staticmethod
def _load_context(session, scan):
    return {
        'cases': [...],
        'modules': [...],
        'executionStats': {...},
        'bugStats': {...},
        'preciseSignals': {...},
        'aiSuggestions': [...],
        'options': scan.options_json or {}
    }
```

Verify:

```powershell
python -m py_compile app/api/service/testAssetGovernanceService.py
```

---

## Task 4: 治理规则与健康评分

**Files:**
- Modify: `app/api/service/testAssetGovernanceService.py`

- [x] 实现 `_detect_duplicate_cases(context)`：
  - 只比较同项目 active cases，排除 `status=2` 和 `is_delete=1`。
  - 文本归一化包含 `title/steps/expected_results/tags`。
  - 相似度阈值默认 `0.72`，可由 `options_json.duplicateThreshold` 覆盖。
  - 生成 `duplicate_case` issue，`related_case_ids` 存放候选用例 ID。
- [x] 实现 `_detect_weak_cases(context)`：
  - `steps` 为空或长度小于 8，记为缺步骤。
  - `expected_results` 为空或长度小于 8，记为缺预期。
  - `expected_results` 包含过泛词，如 `正常`、`成功` 且没有更具体断言，记为弱断言。
- [x] 实现 `_detect_stale_cases(context)`：
  - 默认阈值 180 天，可由 `options_json.staleDays` 覆盖。
  - 没有执行记录且创建时间早于阈值，或最近执行时间早于阈值，生成 `stale_case` issue。
- [x] 实现 `_detect_coverage_gaps(context)`：
  - 模块状态正常，active case 数为 0。
  - 同模块存在 active bug、精准测试推荐或 AI建议时生成 `coverage_gap`。
- [x] 实现 `_detect_ai_suggestions(context)`：
  - `action_status` 为 pending/open/空，且未 `created_case_id`/`matched_case_id` 的建议生成 `ai_suggestion`。
- [x] 实现 `_build_summary(context, issues)`：
  - 基础分 100。
  - critical/high/medium/low 分别扣 20/12/6/2。
  - 最低 0。
  - 输出 `issueTypeCounts/severityCounts/recommendedActions`。
- [x] 实现 `_enhance_summary_with_ai(summary, issues)`，调用失败时返回本地 summary。

Verify:

```powershell
python -m py_compile app/api/service/testAssetGovernanceService.py
```

---

## Task 5: 扫描执行与问题动作闭环

**Files:**
- Modify: `app/api/service/testAssetGovernanceService.py`

- [x] 实现 `execute_scan(session, scan_id)`：
  - 状态改为 `running`，记录 `started_time`。
  - 清理该 scan 下未删除旧 issue/action，或软删除旧 issue/action 后重建。
  - 聚合上下文并执行五类检测。
  - 批量写入 `TestAssetIssue`。
  - 更新 `summary_json/health_score/status/finished_time`。
  - 异常时写 `status=failed/error_message/finished_time`。
- [x] 实现 `update_issue(session, req_data, user_id=None)`：
  - 支持 `open/accepted/ignored/fixed/reopened`。
  - 每次更新写入 `TestAssetAction`，`action_type` 取 `mark_fixed/ignore/reopen` 等。
- [x] 实现 `apply_action(session, req_data, user_id=None)`：
  - `deprecate`：校验 `caseId` 属于 issue 的 `related_case_ids`，将 `TestCase.status` 设置为 2。
  - `merge/improve/keep/accept_suggestion`：第一版只记录 action，不自动改 case 内容。
  - action 成功后按动作更新 issue `action_status`。

Verify:

```powershell
python -m py_compile app/api/service/testAssetGovernanceService.py
```

---

## Task 6: Controller 与路由

**Files:**
- Create: `app/api/controller/testAssetGovernanceController.py`
- Modify: `app/api/views.py`

- [x] Controller 方法：
  - `scan_create`
  - `scan_list`
  - `scan_detail`
  - `scan_execute`
  - `issue_list`
  - `issue_update`
  - `action_apply`
- [x] `views.py` 导入 `TestAssetGovernanceController`。
- [x] 注册 `/test-asset/governance/*` 路由。
- [x] 所有接口加 `login_required` 和对应 `permission_required('test_asset_governance:*')`。
- [x] 返回风格沿用 `ApiResponse.build_success/build_failure`。

Verify:

```powershell
python -m py_compile app/api/controller/testAssetGovernanceController.py app/api/views.py
```

---

## Task 7: 前端 API 与路由

**Files:**
- Create: `D:\zhyy\effekt-interface-frontend\src\api\testAssetGovernanceApi.js`
- Modify: `D:\zhyy\effekt-interface-frontend\src\router\index.js`

- [x] API 方法覆盖所有 `/test-asset/governance/*` 接口。
- [x] 新增路由：
  - `/test-asset-governance`
  - `/test-asset-governance/detail`
- [x] 页面组件路径使用：
  - `@/components/TestAssetGovernance/ScanList`
  - `@/components/TestAssetGovernance/ScanDetail`
- [x] 不扩展 `TestPlatform/Case/CaseList.vue`。

API 结构：

```javascript
import request from '@/utils/request'

export function createAssetGovernanceScan(data) {
  return request({ url: '/test-asset/governance/scan/create', method: 'post', data })
}

export function getAssetGovernanceScanList(params) {
  return request({ url: '/test-asset/governance/scan/list', method: 'get', params })
}

export function getAssetGovernanceScanDetail(params) {
  return request({ url: '/test-asset/governance/scan/detail', method: 'get', params })
}

export function executeAssetGovernanceScan(data) {
  return request({ url: '/test-asset/governance/scan/execute', method: 'post', data })
}

export function getAssetGovernanceIssueList(params) {
  return request({ url: '/test-asset/governance/issue/list', method: 'get', params })
}

export function updateAssetGovernanceIssue(data) {
  return request({ url: '/test-asset/governance/issue/update', method: 'post', data })
}

export function applyAssetGovernanceAction(data) {
  return request({ url: '/test-asset/governance/action/apply', method: 'post', data })
}
```

Verify:

```powershell
Select-String -Path D:\zhyy\effekt-interface-frontend\src\router\index.js -Pattern "test-asset-governance"
```

---

## Task 8: 前端扫描列表页

**Files:**
- Create: `D:\zhyy\effekt-interface-frontend\src\components\TestAssetGovernance\ScanList.vue`

- [x] 列表支持产品、项目、状态、风险等级、关键词筛选。
- [x] 表格列：扫描编号、标题、产品、项目、健康分、状态、问题数、高风险数、创建时间、操作。
- [x] 支持新建扫描弹窗：产品、项目、标题、扫描类型、过期天数、重复阈值。
- [x] 支持“执行扫描”按钮并显示 loading。
- [x] 新建成功后跳转详情页或刷新列表。

Verify:

```powershell
npm.cmd --prefix D:\zhyy\effekt-interface-frontend run build
```

---

## Task 9: 前端扫描详情页与动作闭环

**Files:**
- Create: `D:\zhyy\effekt-interface-frontend\src\components\TestAssetGovernance\ScanDetail.vue`

- [x] 展示扫描总览：健康分、状态、总用例数、AI用例数、问题总数、各严重等级数量。
- [x] 展示 issue table，支持按问题类型、严重等级、状态过滤。
- [x] 展示 evidence drawer，格式化 `evidence_json/suggestion_json/related_case_ids`。
- [x] 支持问题动作：
  - 接收
  - 忽略
  - 标记修复
  - 重新打开
  - 记录合并建议
  - 废弃用例
- [x] 动作完成后刷新详情。
- [x] 详情页刷新后仍能看到 issues 和 actions。

Verify:

```powershell
npm.cmd --prefix D:\zhyy\effekt-interface-frontend run build
```

---

## Test Plan

- [ ] OpenSpec 校验：

```powershell
node C:\Users\hasee\AppData\Roaming\npm\node_modules\@fission-ai\openspec\bin\openspec.js status --change add-ai-test-asset-governance
```

- [x] 后端编译：

```powershell
python -m py_compile `
  app/api/model/testAssetGovernanceModel.py `
  app/api/dao/testAssetGovernanceDao.py `
  app/api/service/testAssetGovernanceService.py `
  app/api/controller/testAssetGovernanceController.py `
  app/api/views.py
```

- [x] SQL 检查：

```powershell
Select-String -Path resources\sql\test_asset_governance_pgsql.sql -Pattern "test_asset_scan"
Select-String -Path resources\sql\test_asset_governance_pgsql.sql -Pattern "sys_permission"
```

- [x] 前端构建：

```powershell
npm.cmd --prefix D:\zhyy\effekt-interface-frontend run build
```

- [ ] API 冒烟：

```text
创建治理扫描 -> 执行扫描 -> 查看详情 -> 查看问题列表 -> 更新问题状态 -> 执行废弃用例动作 -> 确认 action history
```

- [ ] 页面验收：

```text
扫描列表筛选正常
新建扫描弹窗正常
执行扫描 loading 正常
详情页健康分和问题统计正常
问题证据抽屉正常
问题动作后状态同步
无权限用户不能执行扫描或动作
```

---

## Assumptions

- 第一版只做项目级扫描，不做跨项目资产治理。
- 第一版不物理删除用例，不自动合并用例。
- 第一版 `deprecate` 动作只把用例 `status` 改为 2。
- 第一版重复识别用本地相似度算法，不新增向量库。
- 第一版 AI 只增强摘要和推荐动作，AI 不可用时使用本地兜底摘要。
- 第一版前端新增独立页面，不继续扩大 `CaseList.vue`。
