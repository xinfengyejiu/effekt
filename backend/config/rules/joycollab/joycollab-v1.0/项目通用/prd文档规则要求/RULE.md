---
name: prd
description: 根据文档，就输出两个方向模块，一个是创作者，一个是管理后台
---

# prd文档规则要求

## Rule
根据文档，就输出两个方向模块，一个是创作者，一个是管理后台

## Applicable scene
适用于根据 PRD 或需求文档生成测试用例时，需要按业务使用方或功能入口拆分测试范围的场景。该规则要求测试用例生成结果围绕两个方向模块展开：创作者模块和管理后台模块。

## Example
输入：PRD 描述了内容发布、作品管理、审核配置、后台运营管理等能力。场景：AI 根据该 PRD 生成测试用例。预期：测试用例应按“创作者”和“管理后台”两个方向模块组织，不应脱离文档额外扩展其他业务模块；创作者侧覆盖发布、编辑、查看、提交等相关用例，管理后台侧覆盖审核、配置、管理、查询等相关用例。

## Test design constraints
- Generate cases that verify this rule is satisfied in normal flows.
- Generate negative and boundary cases when the rule describes validation, limits, state changes, permissions, or data constraints.
- Mark missing prerequisites as “待确认” instead of inventing behavior.

## Metadata
- Code: PRD_20260706134118766254
- Product: joycollab
- Project: joycollab-v1.0
- Module: 项目通用
- Priority: 2
- Tags: PRD解析, 模块划分, 测试用例生成, 创作者, 管理后台
