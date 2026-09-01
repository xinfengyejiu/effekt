---
name: test-case-generator
description: Generate structured software test cases from requirements using a strict four-stage workflow: requirement analysis and test point identification, test case design, quality review and optimization, and final deduplication/output. Use this skill whenever the user asks to analyze requirements, identify test points, write test cases, review test cases, optimize QA cases, export JSON test cases, or ensure test case coverage is aligned with requirement documents.
---

# Test Case Generator

Use this skill to generate high-quality software test cases from requirement documents, PRDs, user stories, feature descriptions, API specifications, UI interaction descriptions, bug reports, or change notes.

The workflow has four required stages:

1. 需求分析与测试点识别
2. 测试用例设计
3. 质量审核与优化
4. 最终整理与输出

Core rule: requirement documents are the source of truth. Test points guide titles and coverage scope, but concrete test steps and expected results must come from the actual requirement content.

## When to use this skill

Use this skill when the user asks for any of the following:

- 生成测试用例、编写测试用例、设计测试用例
- 根据需求文档提取测试点
- 根据测试点生成 JSON 测试用例
- 审核、优化、补充测试用例
- 去重整合测试用例
- 输出可导入测试管理平台的测试用例集合
- 生成正常流程、异常流程、边界值、专项验证、回归测试用例

If the user only provides rough requirements, continue with explicit assumptions and mark missing information as open questions. Do not invent unsupported business behavior as if it were stated in the requirement.

## Global principles

- Requirement document = source for test steps, expected results, preconditions, data, and business behavior.
- Test point list = title and coverage guidance.
- One atomic scenario maps to one test case; do not compress multiple independent rules, validations, states, or exception branches into one large case.
- Test case count must equal atomic scenario count in the final output.
- Test case order must follow the module order and business flow order.
- Only generate modules for testable business functions, backend operations, user flows, acceptance criteria, non-functional requirements, or explicit business rules. Do not generate test cases or modules for document metadata/background-only sections such as 文档说明、文档目的、资料来源、产品定位、用户角色说明、版本规划、待完善事项清单、风险与注意事项、附录, unless they contain explicit testable behavior.
- Functional modules must strictly follow the PRD numbering hierarchy for upper levels after non-testable metadata sections are excluded. First-level modules follow PRD first-level testable sections; second-level modules follow child numbered sections under each first-level section.
- Use `一级模块/二级模块/三级模块/四级模块` to carry PRD numbered sections and analyzed lower-level functional structure. Third-level and fourth-level modules must be filled from actual analysis results when the PRD has shallow numbering, using child headings, tables, feature groups, business rules, and flow nodes.
- Test case names must directly describe the atomic scenario, including normal, exception, boundary, permission, state, data, or integration context.
- Include exception, boundary, UI, permission, performance, compatibility, or security tests when the requirement explicitly supports them or when business risk clearly justifies them; uncertain details must be marked as open questions or “待确认”.
- Every step must be executable and every expected result must be verifiable.
- Prefer detailed coverage over overly terse output. For each explicit requirement point, identify all applicable normal, exception, boundary, data validation, state transition, permission, UI feedback, and persistence scenarios.

## PRD Numbering Module Hierarchy

When generating cases for platform import, design the module hierarchy strictly from the PRD's numbered structure before writing test cases.

### Numbering-to-module rules

- First-level modules must exactly follow the PRD's first-level numbered sections. If the PRD has 5 first-level sections, generate exactly 5 first-level modules.
- Second-level modules must follow the child numbered sections under each first-level section. If section 1 has 7 child sections, create 7 second-level modules under the first first-level module.
- Continue mapping lower numbered sections into third-level and fourth-level modules when the PRD provides that structure.
- The module path may use up to four levels: `一级模块/二级模块/三级模块/四级模块`.
- Do not create additional first-level modules from pages, buttons, entry points, popups, fields, status values, exception states, or isolated operations when they do not correspond to PRD first-level numbering.

### Handling unnumbered or shallow PRDs

- If the PRD has no explicit numbering, first infer an implicit numbering hierarchy before generating cases.
- Infer implicit first-level modules from top-level headings, table-of-content entries, large functional sections, or repeated major topic blocks.
- Infer second-level to fourth-level modules from child headings, list indentation, table sections, feature groups, user flows, or semantically subordinate paragraphs.
- If the PRD has clear headings but no explicit numbering, treat the inferred top-level headings as first-level modules and child headings as lower-level modules.
- If a PRD section contains many atomic scenarios but no lower-level headings, keep them under the closest inferred module and put the scenario difference in the test case title.
- If the PRD has more than four heading levels, preserve the first four meaningful levels and move deeper detail into the test case title.
- Keep naming consistent with the PRD headings. Do not invent synonyms or merge numbered sections unless the PRD itself indicates they are the same scope.

### Module path format

- `module_name` / `所属模块` must use `一级模块/二级模块/三级模块/四级模块` when the PRD supports it.
- The path should have at most four levels.
- Use the PRD numbering only to determine hierarchy. Module names should use the title text of each numbered heading as much as possible, without adding the numeric prefix unless the title itself requires it.
- Each level should correspond to the nearest PRD numbered heading or explicit heading title.

Examples of acceptable module paths:

- `账号登录与访问权限/登录认证/账号密码登录/异常密码校验`
- `搜索与多语言/搜索结果/多语言检索/无结果提示`
- `社区首页与内容发现/推荐内容/信息流展示/分页加载`

Avoid these patterns:

- PRD has first-level sections `1` to `5`, but generated first-level modules exceed 5.
- Creating modules for non-testable metadata/background-only headings such as `文档说明/资料来源`, `文档说明/文档目的`, `附录/字段说明`, or `风险与注意事项` when they only describe documentation context.
- Section `1` has 7 child numbered testable sections, but generated second-level modules under section `1` do not match those 7 child sections.
- Using page names, dialog names, button names, field names, or single operations as first-level modules when they are not PRD first-level headings.

## Stage 1: 需求分析与测试点识别

Act as a requirement analyst. Deeply analyze the requirement document and identify all test points.

Important notes:

- The test points you provide will become the titles and coverage guidance for the test cases.
- The test case designer will use the test points to determine the testing scope, but the concrete test steps must be extracted directly from the requirement document.
- Therefore, the test point list must be complete, accurate, and structured to avoid missed coverage.

### Responsibilities

1. Deeply read the requirement document and understand business functions, operation flows, UI interactions, data processing, and constraints.
2. Identify functional modules according to business logic.
3. Extract all key requirement points for each functional module, including pages, fields, buttons, APIs, status transitions, messages, persistence, permissions, background jobs, and integrations.
4. Split each requirement point into atomic scenarios: normal flow, exception flow, boundary value, data validation, permission, state transition, UI feedback, persistence, and regression impact when applicable.
5. Output a structured atomic scenario checklist for test case design. Do not output only high-level module summaries.

### Test point identification strategy

#### Normal flow test points: must cover

Include:

- Main-flow test points for core business functions.
- Standard user operation paths.
- Basic UI interaction functions.
- Successful create, query, update, delete, submit, approve, export, import, sync, or callback flows when mentioned.
- Data persistence and state transition verification for each operation that changes data.

#### Exception and boundary value test points: include only when applicable

Only include exception and boundary test points when at least one of these conditions is true:

- The requirement explicitly mentions input restrictions, such as length, numeric range, format, type, uniqueness, required fields, allowed values, file size, file type, time range, count limit, or status limit.
- The requirement describes exception handling, such as error messages, alternative flows, failure states, retries, rollback, duplicate operations, expired data, invalid tokens, or missing permissions.
- The feature involves critical data processing, audit records, financial amounts, workflow state changes, or security-sensitive operations.
- The requirement is complex and contains multiple business rules or constraints.

Do not fabricate boundary or exception rules that are not supported by the requirement. If they are likely important but missing, list them as open questions instead of test points.

#### Special verification test points: include only when explicitly required

Only include these sections when the requirement explicitly mentions the relevant requirement:

- UI verification: display, interaction experience, responsive layout, visual state, or UI copy.
- Permission verification: user permissions, operation permissions, data permissions, roles, tenants, or scopes.
- Performance verification: response time, concurrency, throughput, resource usage, or capacity.
- Compatibility verification: browser, device, operating system, app version, or platform support.
- Security verification: data security, access security, transmission security, sensitive information, or attack prevention.

### Stage 1 output format

Use this exact structure:

```markdown
## 功能模块1：[模块名称]
### 正常流程测试点：
- [编号]、[测试点名称]：[简要说明]
- [编号]、[测试点名称]：[简要说明]

### 异常&边界值测试点：（仅在需求文档明确涉及时才包含此部分）
- [编号]、[测试点名称]：[简要说明]
- [编号]、[测试点名称]：[简要说明]

### 专项验证测试点：（仅在需求文档明确提及相关要求时才包含此部分）
- [编号]、[测试点名称]：[简要说明]
- [编号]、[测试点名称]：[简要说明]
```

If a section is not applicable, omit the section unless the user asks to show empty sections.

## Stage 2: 测试用例设计

Act as a test case designer. Write detailed test cases based on both the test point checklist and the original requirement document.

### Mandatory workflow

Strictly follow these steps:

1. Carefully read the original requirement document and understand business functions, operation flows, UI interactions, data processing, and details.
2. List all test points from the requirement analyst one by one.
3. Write test cases one by one in the exact order of the test points.
4. Write concrete test steps based on the requirement document's actual functional description.
5. Final-check count and order: test case count must equal test point count, and order must be exactly the same.

### Important principles

- Requirement analyst test points = case titles and testing scope guidance.
- Requirement document functional descriptions = source for concrete test steps.
- Never write test steps only from the test point name. Always return to the requirement document to find the corresponding functional details.

### Design principles

- Strictly follow test point order.
- One test point maps to one test case.
- Test point as title, requirement document as content.
- Steps must be concrete and executable, including what to click, what to input, which page to operate on, which API to call, or which data to prepare.
- Expected results must be verifiable, including visible results, state changes, data changes, messages, status codes, or persisted records.

### Before writing cases: count test points first

Before generating JSON, output a test point count section:

```markdown
测试点统计：
功能模块X：
- 正常流程测试点：[测试点1]、[测试点2]...（共X个）
- 异常&边界值测试点：[测试点1]、[测试点2]...（共X个）【如果需求分析师未提供此类测试点，则显示"无"】
- 专项验证测试点：[测试点1]、[测试点2]...（共X个）【如果需求分析师未提供此类测试点，则显示"无"】
总计：X个测试点，需要编写X个测试用例
```

### Stage 2 JSON output format

After the count section, generate test cases using this JSON shape:

```json
{
  "业务模块名称": [
    {
      "ID": "用例编号",
      "用例名称": "[测试点名称]（直接使用需求分析师的测试点名称，不要修改）",
      "所属模块": "业务模块名称",
      "前置条件": "前置条件描述（基于需求文档的具体要求）",
      "备注": "测试用例相关备注说明",
      "步骤描述": "具体操作步骤1（基于需求文档的功能描述）\n具体操作步骤2（基于需求文档的功能描述）\n具体操作步骤3（基于需求文档的功能描述）",
      "预期结果": "具体预期结果1（基于需求文档的功能要求）\n具体预期结果2（基于需求文档的功能要求）\n具体预期结果3（基于需求文档的功能要求）",
      "编辑模式": "创建",
      "标签": "功能测试",
      "用例等级": "P1/P2/P3/P4/P5",
      "用例状态": "待执行"
    }
  ]
}
```

### Field rules

- ID should be stable and ordered, such as `TC-001`, `TC-002`, or the user's requested format.
- 用例名称 must exactly match the test point name.
- 所属模块 must match the PRD numbering hierarchy and actual analysis results. Prefer `一级模块/二级模块/三级模块/四级模块`, with no more than four levels. Use PRD first-level and second-level numbering for upper levels; when third-level or fourth-level numbering is absent, derive lower levels from child headings, table feature items, business rules, acceptance rows, operation flows, and meaningful functional subdivisions. Use each numbered heading's title text or analyzed functional point as the module name as much as possible, and do not create first-level modules beyond the PRD's first-level headings.
- 前置条件 must come from requirements or clearly stated assumptions.
- 步骤描述 must use newline-separated concrete operations.
- 预期结果 must use newline-separated concrete assertions.
- 编辑模式 defaults to `创建`.
- 标签 defaults to `功能测试` unless another type is clearly more appropriate.
- 用例等级 should reflect business priority and risk:
  - P1: core/blocking flow or high-risk business function.
  - P2: important normal/exception flow.
  - P3: general validation or lower-risk branch.
  - P4/P5: low-risk, compatibility, or optional verification when applicable.
- 用例状态 defaults to `待执行`.

## Stage 3: 质量审核与优化

Act as a test case reviewer. Perform a comprehensive review of the generated test cases.

### Core review principles

- Requirement document is the fundamental basis of the test cases.
- Each test step should be traceable to a functional description in the requirement document.
- Test points guide coverage scope and must all have corresponding test cases.
- Test steps must be concrete and executable, not abstract concepts.

### Review checklist

#### 1. Requirement basis check

Check:

- Can every test step be traced to a corresponding functional description in the requirement?
- Does the operation path match the business flow in the requirement?
- Are data input and output consistent with requirement specifications?
- Does UI interaction reflect the UI design or interaction description in the requirement?
- Are there any imagined steps detached from the requirement and based only on the test point name?

#### 2. Test point coverage check

Check:

- Quantity: does test case count equal test point count?
- Order: does test case order exactly match test point order?
- Normal flow: does every normal flow test point have a corresponding case?
- Exception and boundary: does every exception/boundary test point have a dedicated case?
- Special verification: are data, UI, permission, performance, compatibility, or security points covered when provided?
- Name consistency: does each test case name directly use the test point name?

#### 3. Test quality standard check

Check:

- Step specificity: do steps include concrete operations such as what to click, what to input, and where to operate?
- Result verifiability: are expected results clear enough to determine pass/fail?
- Preconditions completeness: are all required conditions before execution stated?
- Test data sufficiency: are required data and parameters clear?

### Stage 3 output format

Output a concise review report:

```markdown
## 质量审核结果
### 1. 需求文档依据性检查
- 结论：通过/需修改
- 问题：...
- 优化建议：...

### 2. 测试点覆盖度检查
- 测试点数量：X
- 测试用例数量：X
- 顺序一致性：一致/不一致
- 名称一致性：一致/不一致
- 缺失项：无/...

### 3. 测试质量标准检查
- 步骤具体性：通过/需修改
- 结果可验证性：通过/需修改
- 前置条件完整性：通过/需修改
- 数据准备充分性：通过/需修改

### 4. 需要修正的用例
- [ID] [用例名称]：问题与修正建议
```

If issues are found, revise the affected test cases before final output.

## Stage 4: 最终整理与输出

Act as a test case organizer. Perform final deduplication, integration, sorting, and complete output.

### Core responsibilities

1. Collect and extract all JSON-format test cases from previous design and review outputs.
2. Deduplicate and merge repeated or similar test cases so each test point has exactly one best case.
3. Sort the integrated test cases according to the functional module order and test point order from Stage 1.
4. Output a complete deduplicated test case collection.

### Deduplication and integration strategy

#### Same functional point

If multiple cases test the same functional point:

- Choose the version with the most detailed steps and clearest expected results.
- Merge useful steps and assertions from other versions if coverage is improved.
- Do not reduce coverage during merging.

#### Similar cases

If cases have similar objectives but different wording:

- Merge them into a more comprehensive case only if they correspond to the same test point.
- Preserve the core testing value of each case.
- Avoid creating functional testing blind spots.

### Final quality checklist

Before final output, verify:

- [ ] Test case count equals test point count.
- [ ] Test case order exactly matches test point order.
- [ ] Test case names directly use test point names.
- [ ] Every test case step is concrete and executable.
- [ ] Every test case can be traced to the requirement document.
- [ ] All requirement analyst test points are covered.
- [ ] Duplicate and redundant test cases are removed.
- [ ] Expected results are clear and verifiable.

### Stage 4 final output format

Output:

1. Final test point count summary.
2. Final deduplicated JSON test case collection.
3. Final quality checklist result.
4. Assumptions and open questions, if any.

Use this structure:

```markdown
## 最终测试点统计
- 功能模块A：X个
- 功能模块B：X个
- 总计：X个测试点，X个测试用例

## 最终测试用例JSON
```json
{
  "业务模块名称": [
    {
      "ID": "TC-001",
      "用例名称": "测试点名称",
      "所属模块": "业务模块名称",
      "前置条件": "...",
      "备注": "...",
      "步骤描述": "...",
      "预期结果": "...",
      "编辑模式": "创建",
      "标签": "功能测试",
      "用例等级": "P1",
      "用例状态": "待执行"
    }
  ]
}
```

## 最终质量检查
- 测试用例数量是否等于测试点数量：是/否
- 测试用例顺序是否与测试点顺序完全一致：是/否
- 测试用例名称是否直接使用测试点名称：是/否
- 步骤是否具体可操作：是/否
- 是否能追溯到需求文档：是/否
- 是否覆盖所有测试点：是/否
- 是否去除重复冗余：是/否
- 预期结果是否明确可验证：是/否

## 假设与待确认问题
- ...
```

## Default response behavior

When the user asks to generate test cases from a requirement, perform all four stages unless they explicitly request only one stage.

Recommended output order:

1. Stage 1 test point checklist.
2. Stage 2 test point count and JSON test cases.
3. Stage 3 quality review report and any corrections.
4. Stage 4 final deduplicated JSON output.
5. Assumptions and open questions.

If the requirement is very long, you may keep Stage 3 concise but must still perform count, order, name, traceability, and deduplication checks.

## Handling incomplete requirements

When requirements are incomplete:

- Continue generating useful cases based on available information.
- Clearly separate requirement-supported cases from assumptions.
- Do not add unsupported exception/boundary/special verification test points as confirmed facts.
- Put missing business rules, validation limits, permission rules, UI details, or error messages into open questions.

## API-specific adaptation

For API requirements:

- Steps may include method, path, headers, auth state, request body, and execution method.
- Expected results should include status code, response body, database side effects, idempotency, and error format when required.
- Boundary and exception tests should only use limits/rules specified by the API requirement or clearly marked assumptions.

## Frontend-specific adaptation

For frontend/UI requirements:

- Steps should identify page, control, action, input, and navigation path.
- Expected results should include visible UI text, component state, validation message, navigation result, and persisted data when required.
- UI-specific verification should only be included when UI display or interaction requirements are explicit.

## Backend/business-logic adaptation

For backend or business rules:

- Steps should identify data setup, operation trigger, business condition, and verification method.
- Expected results should include state transition, persisted records, downstream effects, event/message production, or rollback behavior when required.

## Example

Input requirement:

```markdown
登录页支持手机号+短信验证码登录。验证码 60 秒内不能重复发送，验证码 5 分钟有效，输错提示“验证码错误”。登录成功后跳转首页。
```

Expected behavior:

- Stage 1 identifies test points such as successful verification-code login, resend restriction within 60 seconds, expired code after 5 minutes, wrong code error, and successful redirect after login.
- Stage 2 outputs one JSON test case for each test point in the same order.
- Stage 3 checks that every step and expected result comes from the requirement.
- Stage 4 outputs deduplicated final JSON and confirms count/order/name consistency.
