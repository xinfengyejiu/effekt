---
name: generated-rule
description: 整体生成用例的模块，尽量整合一下，不要生成太多模块了，不然不好展开
---

# 模块整合

## Rule
整体生成用例的模块，尽量整合一下，不要生成太多模块了，不然不好展开

## Applicable scene
适用于根据 PRD、需求文档或用户故事整体生成测试用例时，对测试模块、功能分组、用例目录结构进行组织和拆分的场景。尤其适用于需求范围较大、功能点较多、容易被 AI 过度细分为大量模块的测试用例生成任务。

## Example
输入：某 PRD 包含登录、注册、找回密码、账号安全设置、第三方登录等账号相关能力。场景：AI 生成测试用例模块结构。预期：将相关能力整合为“账号与认证”或少量相近模块，并在模块内展开具体测试点，而不是分别生成大量独立模块导致目录过细、难以展开和维护。

## Test design constraints
- Generate cases that verify this rule is satisfied in normal flows.
- Generate negative and boundary cases when the rule describes validation, limits, state changes, permissions, or data constraints.
- Mark missing prerequisites as “待确认” instead of inventing behavior.

## Metadata
- Code: RULE_20260702142219800401
- Product: edenplayer
- Project: edenplayer-V1.0
- Module: 项目通用
- Priority: 2
- Tags: 测试用例生成, 模块划分, 用例组织, 需求分析
