# AI工作量预估设计方案

## 背景

平台已经具备产品、项目、项目成员、需求问答文档、AI测试评审等能力。现在需要新增一个独立菜单：`AI工作量预估`，用于基于本次 PRD 生成测试工作量、用例数量和 Token 消耗预估，并支持单人负责人分配、列表查询和详情追溯。

本功能只新增一个菜单入口，不拆多个子菜单。历史需求文档只作为复杂度参考，不作为本次预估范围。

## 目标

- 左侧菜单新增 `AI工作量预估`。
- 支持选择产品、项目、负责人。
- 支持上传或选择本次 PRD，并通过复选框勾选参与本次预估的 PRD。
- 基于本次 PRD 输出模块、功能点、用例数量、测试设计工时、QA执行工时、总工时和 Token 预估。
- 历史需求问答文档按产品维度检索，只用于复杂度参考和校准。
- 列表页展示预估记录，并支持按产品名称、项目名称搜索。
- 详情页展示预估具体数据、PRD 来源、历史参考、风险假设和负责人信息。

## 非目标

- 第一版不做多人协作分配。
- 第一版不做资源日历和冲刺容量排期。
- 第一版不自动生成测试计划。
- 第一版不把历史 PRD 当成本次预估范围。
- 第一版不做跨产品历史参考。
- 第一版不自动回写测试计划或用例库。

## 菜单与路由

左侧只新增一个菜单：`AI工作量预估`。

建议挂在现有 `AI质量助手` 分组下，与 `需求问答`、`AI测试评审`、`测试资产治理`、`精准测试` 保持同类归属。

前端路由：

```text
/ai-workload-estimate
/ai-workload-estimate/create
/ai-workload-estimate/detail
```

左侧菜单只显示 `/ai-workload-estimate`。创建页和详情页作为隐藏路由或页面跳转使用，不单独出现在左侧菜单。

## 用户流程

核心流程：

```text
进入AI工作量预估列表
-> 新建预估
-> 选择产品
-> 选择项目
-> 选择单人负责人
-> 上传或选择本次PRD
-> 勾选参与本次预估的PRD
-> 执行AI预估
-> 查看详情
-> 人工确认
```

重新分配负责人流程：

```text
列表或详情点击分配负责人
-> 加载当前项目成员
-> 选择一个负责人
-> 保存
-> 刷新列表和详情
```

## PRD 来源设计

文档分为两类。

### 本次 PRD

本次 PRD 是预估范围的唯一来源。只有用户本次上传或勾选的 PRD 会进入：

- 模块拆解
- 功能点拆解
- 用例数量估算
- 测试设计工时估算
- QA执行工时估算
- Token 预估

本次 PRD 从现有需求问答文档能力复用。用户选择产品和项目后，页面展示该产品、项目下已解析的文档，用户通过复选框选择参与本次预估的 PRD。上传、解析能力复用现有需求问答文档链路。

### 历史参考文档

历史文档按产品维度检索，只用于复杂度参考。历史文档不参与本次功能范围，不直接增加本次功能点或用例数。

历史参考用于辅助判断：

- 相似模块的历史用例密度。
- 相似功能的复杂度等级。
- 同产品历史需求中常见风险。
- 权限、状态流转、导入导出、消息通知、跨端兼容等复杂特征。

详情页必须清晰区分：

- 本次参与预估的 PRD。
- 历史复杂度参考文档。
- 哪些结论来自本次 PRD。
- 哪些复杂度判断参考了历史材料。

## 负责人设计

负责人采用单人负责人模型。

- 新建预估时选择负责人。
- 负责人从当前项目成员中选择。
- 创建人不等于负责人。
- 列表和详情都支持重新分配负责人。
- 如果项目暂无成员，允许负责人为空创建，列表显示 `未分配`。

需要记录：

- 当前负责人。
- 分配人。
- 分配时间。
- 确认人。
- 确认时间。
- 确认备注。

## 状态流转

第一版状态：

```text
draft       草稿
estimating  预估中
completed   预估完成
failed      预估失败
confirmed   人工确认
archived    归档
```

状态规则：

- 新建后默认为 `draft`。
- 执行预估时置为 `estimating`。
- AI预估和本地校准完成后置为 `completed`。
- AI调用失败、JSON解析失败或文档内容不可用时置为 `failed`，并保存失败原因。
- 用户确认后置为 `confirmed`。
- 归档后置为 `archived`。

## 预估逻辑

预估流程分为四步。

### 1. 读取本次 PRD

读取用户勾选的本次 PRD 文档内容、标题、来源、版本、产品、项目。

只把本次 PRD 作为范围输入。

### 2. 检索历史参考

按产品维度检索历史需求问答文档和知识分片，找到相似模块、相似功能、历史复杂度证据。

历史内容只作为复杂度、用例密度和风险判断参考。

### 3. AI结构化拆解

AI输出：

- 模块列表。
- 功能点列表。
- 场景类型。
- 用例数量。
- 测试设计工时。
- QA执行工时。
- Token 预估。
- 风险项。
- 不确定项。
- 历史参考证据。

### 4. 本地校准

后端对 AI 结果做规则校准：

- 正常产能按每天 40-50 条测试用例作为参考。
- 高复杂度功能增加设计工时系数。
- 涉及权限、支付、状态机、批量、导入导出、消息通知、跨端一致性的功能增加风险系数。
- 总工时不能低于功能点明细累计值。
- Token 预估按 PRD长度、拆解深度和生成轮次估算。
- 参考样本：240 条功能用例对应测试设计和 QA 时间约 100 小时。

## AI 输出结构

AI服务输出必须是结构化 JSON。

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

模块对象：

```json
{
  "moduleName": "订单管理",
  "description": "模块说明",
  "complexityLevel": "high",
  "functionPointCount": 8,
  "caseCount": 55,
  "caseDesignHours": 12,
  "qaExecutionHours": 15,
  "totalHours": 27,
  "risks": ["状态流转复杂", "权限分支较多"]
}
```

功能点对象：

```json
{
  "moduleName": "订单管理",
  "functionName": "订单取消",
  "description": "支持不同订单状态下取消订单",
  "testScope": "状态流转、权限、库存回滚、消息通知",
  "positiveCaseCount": 6,
  "negativeCaseCount": 8,
  "boundaryCaseCount": 4,
  "permissionCaseCount": 3,
  "integrationCaseCount": 5,
  "caseCount": 26,
  "complexityReason": "存在多状态、多角色和库存回滚",
  "caseDesignHours": 5,
  "qaExecutionHours": 7,
  "totalHours": 12,
  "estimatedTokens": 12000
}
```

## 后端设计

后端沿用当前模式：

```text
Controller -> Service -> DAO/Model -> views.py
```

建议新增文件：

```text
app/api/model/aiWorkloadEstimateModel.py
app/api/dao/aiWorkloadEstimateDao.py
app/api/service/aiWorkloadEstimateService.py
app/api/controller/aiWorkloadEstimateController.py
resources/sql/ai_workload_estimate_pgsql.sql
resources/sql/ai_workload_estimate_menu_permission.sql
```

### 表结构

#### ai_workload_estimate

主表，存每次预估任务。

字段建议：

- `id`
- `estimate_no`
- `title`
- `product_id`
- `product_name`
- `project_id`
- `project_name`
- `owner_id`
- `owner_name`
- `document_ids`
- `reference_document_ids`
- `prd_snapshot`
- `reference_summary`
- `result_summary`
- `raw_ai_output`
- `failure_reason`
- `complexity_level`
- `confidence`
- `total_function_points`
- `total_case_count`
- `case_design_hours`
- `qa_execution_hours`
- `total_effort_hours`
- `estimated_tokens`
- `status`
- `created_by`
- `assigned_by`
- `assigned_time`
- `confirmed_by`
- `confirmed_time`
- `confirm_info`
- `is_delete`
- `created_time`
- `updated_time`

#### ai_workload_estimate_module

模块明细表。

字段建议：

- `id`
- `estimate_id`
- `module_name`
- `description`
- `complexity_level`
- `function_point_count`
- `case_count`
- `case_design_hours`
- `qa_execution_hours`
- `total_hours`
- `risk_summary`
- `sort_order`
- `created_time`
- `updated_time`

#### ai_workload_estimate_function

功能点明细表。

字段建议：

- `id`
- `estimate_id`
- `module_id`
- `module_name`
- `function_name`
- `description`
- `test_scope`
- `positive_case_count`
- `negative_case_count`
- `boundary_case_count`
- `permission_case_count`
- `integration_case_count`
- `case_count`
- `complexity_reason`
- `case_design_hours`
- `qa_execution_hours`
- `total_hours`
- `estimated_tokens`
- `risk_level`
- `sort_order`
- `created_time`
- `updated_time`

### 接口

新增接口：

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
```

### 权限码

```text
ai_workload_estimate:list
ai_workload_estimate:create
ai_workload_estimate:detail
ai_workload_estimate:execute
ai_workload_estimate:assign
ai_workload_estimate:confirm
```

## 前端设计

新增文件：

```text
D:\zhyy\effekt-interface-frontend\src\api\aiWorkloadEstimateApi.js
D:\zhyy\effekt-interface-frontend\src\components\AIWorkloadEstimate\EstimateList.vue
D:\zhyy\effekt-interface-frontend\src\components\AIWorkloadEstimate\EstimateCreate.vue
D:\zhyy\effekt-interface-frontend\src\components\AIWorkloadEstimate\EstimateDetail.vue
```

### 列表页

筛选条件：

- 产品名称。
- 项目名称。
- 负责人。
- 状态。
- 关键词，匹配预估编号和标题。
- 创建时间范围。

其中产品名称和项目名称必须支持模糊搜索。

表格列：

- 预估编号。
- 标题。
- 产品名称。
- 项目名称。
- 负责人。
- PRD文档数。
- 功能点数。
- 预估用例数。
- 设计工时。
- QA工时。
- 总工时。
- Token预估。
- 复杂度。
- 置信度。
- 状态。
- 创建时间。
- 操作。

操作：

- 查看详情。
- 重新预估。
- 分配负责人。
- 确认预估。

### 新建页

字段：

- 预估标题。
- 产品。
- 项目。
- 负责人。
- 本次 PRD 文档。
- 备注。

校验：

- 产品必选。
- 项目必选。
- 至少选择 1 个本次 PRD。
- 未解析成功的文档不能用于预估。

### 详情页

详情页分区：

- 基础信息。
- 负责人信息。
- 预估总览。
- 本次 PRD。
- 历史参考。
- 模块明细。
- 功能点明细。
- 风险与假设。
- 操作记录。

详情页必须展示到功能点级别，包含功能点用例数、设计工时、QA工时和 Token 预估。

## 错误处理

- 没有选择本次 PRD 时，禁止执行预估。
- 本次 PRD 没有解析内容时，提示先解析文档。
- AI调用失败时，状态置为 `failed`，保存失败原因。
- AI返回 JSON 不合法时，保存原始输出，状态置为 `failed`。
- 历史参考文档为空时，不阻断预估，只降低置信度或给出说明。
- 项目成员为空时，允许负责人为空，但列表显示 `未分配`。

## 验收标准

- 左侧 `AI质量助手` 下显示 `AI工作量预估`。
- 点击菜单进入列表页。
- 列表支持按产品名称、项目名称、负责人、状态、关键词查询。
- 新建预估时可以选择产品、项目和单人负责人。
- 新建预估时可以上传或选择本次 PRD，并通过复选框勾选参与预估的文档。
- 历史文档只作为同产品复杂度参考，不作为本次范围。
- 执行预估后可以在详情页看到模块明细和功能点明细。
- 详情页展示用例数、测试设计工时、QA执行工时、总工时和 Token 预估。
- 列表和详情都能重新分配负责人。
- 预估失败时可以看到失败原因。
- 人工确认后状态变为 `confirmed`。

## 后续增强

- 导出 Excel 明细表。
- 支持人工调整功能点、用例数和工时。
- 支持实际工时回填，用真实数据持续校准模型。
- 支持个人工作量视图。
- 支持接入测试计划。
- 支持保守、正常、激进三档估算策略。
- 支持历史类似需求对比。
