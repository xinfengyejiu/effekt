<template>
  <div class="effekt-home">
    <el-row :gutter="20" class="top-row">
      <el-col :xs="24" :md="10">
        <el-card shadow="never" class="greet-card">
          <div class="greet-line">{{ greetingPrefix }}{{ greetingTime }}</div>
          <div class="greet-date">{{ todayText }}</div>
          <div v-if="currentUser" class="greet-progress">
            <span class="greet-progress-label">待处理进度</span>
            <el-progress :percentage="100" :stroke-width="10" status="success" />
            <span class="greet-progress-tip">已完成 100%</span>
          </div>
          <div v-else class="greet-login-tip">
            <el-link type="primary" @click="goLogin">登录后查看个人工作台</el-link>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="14">
        <el-card shadow="never" class="work-card">
          <div class="work-card-title">今天剩余工作总计</div>
          <div class="work-stats">
            <div class="work-stat">
              <div class="work-stat-value">{{ formatCount(workCountOpportunity) }}</div>
              <div class="work-stat-label">我的机会</div>
            </div>
            <div class="work-stat work-stat--click" @click="goMyBugs">
              <div class="work-stat-value">{{ formatCount(workCountBug) }}</div>
              <div class="work-stat-label">我的 BUG</div>
              <div class="work-stat-hint">点击查看指派给我</div>
            </div>
            <div class="work-stat work-stat--click" @click="goMyPlans">
              <div class="work-stat-value">{{ formatCount(workCountPlan) }}</div>
              <div class="work-stat-label">我的计划</div>
              <div class="work-stat-hint">点击查看我负责的</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="links-card">
      <div class="links-card-title">测试流程与AI辅助边界</div>
      <p class="home-desc">这里说明测试需要做什么、按什么流程开展，以及哪些环节可以由AI辅助、哪些必须由测试人员判断和兜底。</p>

      <div class="project-block test-guide-block">
        <div class="project-title">测试流程说明</div>
        <p class="guide-desc">测试不是简单执行用例，而是从需求评审开始识别风险、设计验证策略、推动缺陷闭环，并在上线前给出质量结论。</p>
        <div class="process-list">
          <div
            v-for="(step, index) in testProcess"
            :key="step.title"
            class="process-item">
            <div class="process-index">{{ index + 1 }}</div>
            <div class="process-content">
              <div class="process-title">{{ step.title }}</div>
              <div class="process-goal">{{ step.goal }}</div>
              <ul class="process-points">
                <li v-for="point in step.points" :key="point">{{ point }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div class="project-block test-guide-block vibe-quality-block">
        <div class="guide-title-row vibe-title-row">
          <div>
            <div class="project-title">Vibe Coding下为什么更需要测试</div>
            <p class="guide-desc vibe-lead">AI能快速产出代码，但速度越快，越需要测试把需求、实现、数据和上线风险重新拉回可验证状态。</p>
          </div>
          <el-button size="mini" type="primary" plain @click="showAiBoundaryDetail = true">查看详情</el-button>
        </div>

        <div class="vibe-warning-panel">
          <div class="vibe-warning-title">Vibe Coding当前主要缺陷</div>
          <div class="vibe-warning-grid">
            <div v-for="item in vibeCodingRisks" :key="item.title" class="vibe-warning-item">
              <div class="vibe-warning-name">{{ item.title }}</div>
              <div class="vibe-warning-desc">{{ item.desc }}</div>
            </div>
          </div>
        </div>

        <div class="quality-reason-grid">
          <div v-for="item in testingImportanceRows" :key="item.title" class="quality-reason-item">
            <div class="quality-reason-kicker">{{ item.kicker }}</div>
            <div class="quality-reason-title">{{ item.title }}</div>
            <div class="quality-reason-desc">{{ item.desc }}</div>
          </div>
        </div>

        <div class="testing-workflow-panel">
          <div class="testing-workflow-head">
            <div class="testing-workflow-title">测试要做的具体工作</div>
            <div class="testing-workflow-desc">不是点点页面，而是把AI生成代码放进真实业务链路、数据状态、权限角色和上线约束里验证。</div>
          </div>
          <div class="testing-workflow-list">
            <div v-for="item in testingWorkRows" :key="item.stage" class="testing-workflow-item">
              <div class="testing-workflow-stage">{{ item.stage }}</div>
              <div class="testing-workflow-content">
                <div class="testing-workflow-action">{{ item.action }}</div>
                <div class="testing-workflow-output">输出：{{ item.output }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog
      title="AI辅助测试能力边界详情"
      :visible.sync="showAiBoundaryDetail"
      width="86%"
      custom-class="boundary-detail-dialog">
      <p class="guide-desc detail-desc">细粒度说明用于明确每个测试环节中 AI 可以辅助什么、不能替代什么，以及测试人员需要负责的核心价值。</p>
      <div class="boundary-table-wrap detail-table-wrap">
        <table class="boundary-table">
          <thead>
            <tr>
              <th>测试环节</th>
              <th>AI可辅助</th>
              <th>AI无法完全替代</th>
              <th>测试人员核心价值</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in aiBoundaryRows" :key="item.stage">
              <td>{{ item.stage }}</td>
              <td>{{ item.ai }}</td>
              <td>{{ item.limit }}</td>
              <td>{{ item.value }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { getBugList } from '@/api/bugApi'
import { getPlanList } from '@/api/planApi'
import { readLastProductProjectCache } from '@/utils/lastProductProjectCache'

export default {
  name: 'EffektHome',
  data() {
    return {
      workCountOpportunity: null,
      workCountBug: null,
      workCountPlan: null,
      showAiBoundaryDetail: false,
      testProcess: [
        {
          title: '需求评审与风险识别',
          goal: '明确测什么、为什么测、哪些问题会影响上线。',
          points: [
            '阅读需求、原型、接口说明和历史缺陷，梳理业务流程、角色权限、数据流转和上下游依赖',
            '确认验收标准、异常规则、老数据兼容、审批/撤回/重试/失败补偿等边界逻辑',
            '输出疑问清单、风险点、测试范围和暂不覆盖范围'
          ]
        },
        {
          title: '测试设计与用例准备',
          goal: '把业务风险转成可执行、可验收的测试场景。',
          points: [
            '设计正常流程、异常流程、边界值、权限、数据状态、兼容性、接口和跨系统联动用例',
            '按业务影响确定优先级，标记核心链路、阻塞场景、回归范围和冒烟范围',
            '准备测试数据、账号角色、环境依赖、接口参数和预期结果'
          ]
        },
        {
          title: '测试执行与联调验证',
          goal: '验证功能、数据、接口、权限和用户操作链路是否闭环。',
          points: [
            '执行功能测试、接口测试、权限验证、数据落库校验、前后端联调和第三方依赖验证',
            '覆盖用户非标准操作，如重复提交、返回修改、多标签页、网络异常、审批中断和权限切换',
            '记录实际结果、复现路径、截图/日志/请求参数，确保问题可定位'
          ]
        },
        {
          title: '缺陷管理与回归验证',
          goal: '推动问题闭环，确认修复没有引入新风险。',
          points: [
            '提交缺陷并判断严重程度、影响范围、处理优先级和是否阻塞上线',
            '协助开发定位日志、接口、数据或环境问题，跟踪修复进度',
            '复测修复结果，按改动影响执行精准回归和核心链路回归'
          ]
        },
        {
          title: '上线评估与生产验证',
          goal: '给出质量结论，保障上线后核心业务可用。',
          points: [
            '汇总测试范围、执行结果、缺陷状态、遗留风险和上线建议',
            '确认阻塞问题已关闭，明确可接受风险、回滚方案和上线后检查项',
            '上线后执行生产冒烟、核心链路、数据落库、消息/任务/报表等验证'
          ]
        }
      ],
      vibeCodingRisks: [
        { title: '需求理解会漂移', desc: 'AI容易按字面补全功能，却不一定理解业务规则、历史兼容、角色权限和异常状态。' },
        { title: '代码看似完整但缺少闭环', desc: '页面、接口、数据库、消息任务和第三方依赖可能分别能跑，串起来却断在关键链路。' },
        { title: '隐藏风险更难被发现', desc: 'AI生成代码常覆盖正常路径，遗漏重复提交、并发、脏数据、弱网、回滚和越权等真实风险。' },
        { title: '修改速度放大回归成本', desc: '快速迭代会频繁触碰旧逻辑，没有测试就无法判断本次变更影响了哪些历史功能。' }
      ],
      testingImportanceRows: [
        { kicker: '把想法变成标准', title: '确认做的是不是对的', desc: '测试把模糊需求拆成验收标准、业务规则、边界条件和不可接受风险，避免只验证代码能运行。' },
        { kicker: '把功能放进业务', title: '确认链路是不是通的', desc: '从用户操作、接口返回、数据落库、权限控制到消息任务，验证系统在真实流程里是否闭环。' },
        { kicker: '把风险暴露出来', title: '确认问题会不会上线', desc: '通过缺陷复现、影响范围判断、回归验证和上线评估，把不可控问题提前暴露并推动关闭。' }
      ],
      testingWorkRows: [
        { stage: '需求阶段', action: '评审需求、原型和接口说明，追问业务规则、异常流程、权限边界和历史兼容。', output: '疑问清单、风险点、测试范围、验收标准' },
        { stage: '设计阶段', action: '设计核心链路、异常路径、边界值、数据状态、角色权限、接口联动和回归场景。', output: '测试用例、优先级、数据准备清单、冒烟范围' },
        { stage: '执行阶段', action: '按真实用户路径操作系统，同时核对接口、数据库、日志、消息、任务和第三方回调。', output: '执行结果、截图日志、复现步骤、实际影响' },
        { stage: '缺陷阶段', action: '定位问题触发条件，判断严重程度、影响范围和是否阻塞上线，跟进修复闭环。', output: '缺陷单、原因分析、修复验证、精准回归范围' },
        { stage: '上线阶段', action: '汇总执行结果、遗留风险、回滚方案和生产冒烟项，给出质量结论。', output: '测试报告、上线建议、风险说明、生产验证清单' }
      ],
      aiBoundaryRows: [
        { stage: '需求理解', ai: '根据文档提炼功能点、生成基础测试点和评审问题', limit: '无法完整理解公司业务背景、历史逻辑、特殊客户规则和隐性流程', value: '识别需求漏洞，追问关键规则，明确验收标准和风险边界' },
        { stage: '测试用例设计', ai: '生成正常流程、异常输入、边界值、字段校验和权限检查初稿', limit: '无法判断哪些场景最危险、哪些必须优先覆盖、哪些可以降级', value: '按业务影响设计场景、确定优先级，保障核心链路覆盖' },
        { stage: '测试数据准备', ai: '构造通用数据、边界数据、异常字符和接口参数样例', limit: '难以构造依赖真实业务状态、历史数据、审批流和角色权限的数据组合', value: '准备符合业务链路的数据，覆盖关键状态和复杂组合' },
        { stage: '自动化测试', ai: '辅助生成脚本、断言、接口请求和维护建议', limit: '无法保证脚本覆盖核心风险，也无法判断长期维护价值', value: '选择适合自动化的稳定场景，保障脚本可靠、可维护、可复用' },
        { stage: '接口与联调测试', ai: '根据接口文档生成请求、断言、异常参数和调用链草稿', limit: '难以判断接口在完整业务流程、数据库、消息、任务和第三方系统中的真实影响', value: '验证前端、后端、数据、权限和外部依赖是否形成闭环' },
        { stage: '探索性测试', ai: '提供异常场景建议和历史问题排查方向', limit: '无法像真实用户一样结合经验随机操作、联想历史问题和判断异常体验', value: '主动挖掘非标准路径风险，如重复提交、返回修改、网络中断和权限切换' },
        { stage: '缺陷分析', ai: '辅助分析日志、堆栈、接口返回和报错信息', limit: '无法最终判断缺陷严重程度、业务影响范围和处理优先级', value: '准确复现问题，推动修复闭环，确认修复没有引入新问题' },
        { stage: '回归测试', ai: '生成回归清单初稿，辅助执行部分自动化回归', limit: '无法仅凭代码或文档准确判断本次改动影响哪些历史功能', value: '结合改动范围、系统经验和线上风险确定精准回归重点' },
        { stage: '用户体验验证', ai: '提出通用交互、提示语和页面一致性建议', limit: '无法站在真实业务用户角度判断操作是否顺畅、信息是否足够、提示是否可处理', value: '验证用户是否能高效、正确完成业务操作，发现体验和易用性问题' },
        { stage: '上线质量评估', ai: '整理测试报告、缺陷统计、风险清单和冒烟检查项', limit: '无法承担上线质量判断和风险兜底责任', value: '给出是否可上线、哪些风险可接受、哪些必须修复的质量结论' }
      ]
    }
  },
  computed: {
    currentUser() {
      return this.$store.state.currentUser
    },
    greetingPrefix() {
      const u = this.currentUser
      if (!u) return ''
      const name = u.realName || u.username || ''
      return name ? `${name}，` : ''
    },
    greetingTime() {
      const h = new Date().getHours()
      if (h < 12) return '上午好！'
      if (h < 18) return '下午好！'
      return '晚上好！'
    },
    todayText() {
      const d = new Date()
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}年${m}月${day}日`
    }
  },
  mounted() {
    this.refreshWorkCounts()
  },
  methods: {
    formatCount(n) {
      if (n === null || n === undefined || Number.isNaN(Number(n))) return '—'
      return String(n)
    },
    goLogin() {
      this.$router.push({ name: 'login' })
    },
    goMyBugs() {
      if (!this.currentUser) {
        this.$message.warning('请先登录')
        this.goLogin()
        return
      }
      const c = readLastProductProjectCache()
      const q = { assignToMe: '1' }
      if (c && c.productId !== undefined && c.productId !== null && String(c.productId).trim() !== '') {
        q.productId = String(c.productId)
      }
      if (c && c.projectId !== undefined && c.projectId !== null && String(c.projectId).trim() !== '') {
        q.projectId = String(c.projectId)
      }
      this.$router.push({ path: '/bug/list', query: q })
    },
    goMyPlans() {
      if (!this.currentUser) {
        this.$message.warning('请先登录')
        this.goLogin()
        return
      }
      const c = readLastProductProjectCache()
      const q = { planOwnerSelf: '1' }
      if (c && c.productId !== undefined && c.productId !== null && String(c.productId).trim() !== '') {
        q.productId = String(c.productId)
      }
      if (c && c.projectId !== undefined && c.projectId !== null && String(c.projectId).trim() !== '') {
        q.projectId = String(c.projectId)
      }
      this.$router.push({ path: '/test-platform/plan', query: q })
    },
    refreshWorkCounts() {
      const u = this.currentUser
      const c = readLastProductProjectCache()
      this.workCountOpportunity = null
      this.workCountBug = null
      this.workCountPlan = null
      if (!u || u.id == null || u.id === '' || !c || !c.projectId) {
        return
      }
      getBugList({
        productId: c.productId,
        projectId: c.projectId,
        assigneeId: u.id,
        pageNo: 1,
        pageSize: 1
      })
        .then(res => {
          const data = (res && res.data) || res || {}
          this.workCountBug = Number(data.total != null ? data.total : 0)
        })
        .catch(() => {
          this.workCountBug = null
        })
      getPlanList(c.projectId, {
        owner_id: u.id,
        owner: u.id,
        pageNo: 1,
        pageSize: 1
      })
        .then(res => {
          const data = (res && res.data) || res || {}
          this.workCountPlan = Number(data.total != null ? data.total : 0)
        })
        .catch(() => {
          this.workCountPlan = null
        })
    }
  }
}
</script>

<style scoped>
.effekt-home, .effekthome {
  max-width: 1240px;
  margin: 0 auto;
}

.top-row {
  margin-bottom: 20px;
}

.greet-card,
.work-card,
.links-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  background: #ffffff;
}

.greet-card,
.work-card {
  min-height: 174px;
}

.greet-card {
  position: relative;
  background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%);
  color: #fff;
  border-color: transparent;
}

.greet-card:after {
  content: '';
  position: absolute;
  right: -44px;
  bottom: -54px;
  width: 170px;
  height: 170px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(249, 115, 22, 0.2), transparent 68%);
}

.greet-card >>> .el-card__body,
.work-card >>> .el-card__body,
.links-card >>> .el-card__body {
  padding: 24px;
  position: relative;
  z-index: 1;
}

.greet-line {
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 8px;
  letter-spacing: 0.2px;
}

.greet-date {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  margin-bottom: 22px;
}

.greet-progress-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  display: block;
  margin-bottom: 8px;
}

.greet-progress >>> .el-progress-bar__outer {
  background-color: rgba(255, 255, 255, 0.2);
}

.greet-progress >>> .el-progress-bar__inner {
  background: linear-gradient(90deg, #f97316 0%, #fbbf24 100%);
}

.greet-progress-tip {
  font-size: 12px;
  color: #a7f3d0;
  margin-top: 8px;
  display: block;
}

.greet-login-tip {
  margin-top: 8px;
}

.greet-login-tip >>> .el-link.el-link--primary {
  color: #ffffff;
  font-weight: 700;
}

.work-card-title,
.links-card-title {
  position: relative;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
  margin-bottom: 18px;
  padding-left: 12px;
  letter-spacing: 0.3px;
}

.work-card-title:before,
.links-card-title:before {
  content: '';
  position: absolute;
  left: 0;
  top: 3px;
  width: 3px;
  height: 16px;
  border-radius: 2px;
  background: #f97316;
}

.work-stats {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 14px;
}

.work-stat {
  flex: 1;
  min-width: 126px;
  text-align: left;
  padding: 18px;
  border-radius: 8px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  cursor: default;
  transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.2s ease, background 0.2s ease;
}

.work-stat--click {
  cursor: pointer;
}

.work-stat--click:hover {
  border-color: #f97316;
  background: #fff7ed;
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.08);
  transform: translateY(-2px);
}

.work-stat-value {
  font-size: 32px;
  font-weight: 800;
  color: #1e40af;
  line-height: 1.1;
}

.work-stat-label {
  margin-top: 10px;
  font-size: 14px;
  color: #374151;
  font-weight: 600;
}

.work-stat-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #9ca3af;
}

.links-card {
  background: #ffffff;
}

.home-content {
  display: flex;
  flex-direction: column;
}

.home-desc {
  margin: 0 0 18px;
  color: #6b7280;
  font-size: 13px;
}

.project-block {
  padding: 18px;
  margin-bottom: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
}

.project-block:last-child {
  margin-bottom: 0;
}

.project-title {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}

.link-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 10px;
  line-height: 22px;
}

.link-item:last-child {
  margin-bottom: 0;
}

.link-label {
  min-width: 150px;
  color: #374151;
  font-weight: 600;
}

.doc-link {
  word-break: break-all;
}

.doc-link >>> span {
  color: #1e40af;
}

.test-guide-block {
  margin-top: 18px;
}

.guide-desc {
  margin: 0 0 16px;
  color: #6b7280;
  font-size: 13px;
  line-height: 22px;
}

.guide-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.guide-title-row .project-title {
  margin-bottom: 0;
}

.vibe-quality-block {
  padding-bottom: 18px;
}

.vibe-title-row {
  align-items: flex-start;
}

.vibe-lead {
  max-width: 860px;
  margin: 6px 0 0;
}

.vibe-warning-panel {
  margin-top: 14px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #fecaca;
  background: #fef2f2;
}

.vibe-warning-title {
  margin-bottom: 12px;
  color: #dc2626;
  font-size: 14px;
  font-weight: 700;
}

.vibe-warning-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.vibe-warning-item {
  padding-left: 12px;
  border-left: 3px solid #dc2626;
}

.vibe-warning-name {
  color: #111827;
  font-size: 13px;
  font-weight: 700;
  line-height: 20px;
}

.vibe-warning-desc {
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
  line-height: 20px;
}

.quality-reason-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.quality-reason-item {
  padding: 15px 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}

.quality-reason-kicker {
  color: #f97316;
  font-size: 12px;
  font-weight: 700;
  line-height: 18px;
}

.quality-reason-title {
  margin-top: 5px;
  color: #111827;
  font-size: 15px;
  font-weight: 700;
  line-height: 22px;
}

.quality-reason-desc {
  margin-top: 8px;
  color: #6b7280;
  font-size: 12px;
  line-height: 21px;
}

.testing-workflow-panel {
  margin-top: 14px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}

.testing-workflow-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 12px;
}

.testing-workflow-title {
  flex: none;
  color: #111827;
  font-size: 14px;
  font-weight: 700;
  line-height: 22px;
}

.testing-workflow-desc {
  max-width: 680px;
  color: #6b7280;
  font-size: 12px;
  line-height: 20px;
}

.testing-workflow-list {
  display: grid;
  gap: 10px;
}

.testing-workflow-item {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 12px;
  padding: 12px 0;
  border-top: 1px solid #e5e7eb;
}

.testing-workflow-stage {
  color: #1e40af;
  font-size: 13px;
  font-weight: 700;
  line-height: 22px;
}

.testing-workflow-action {
  color: #111827;
  font-size: 13px;
  line-height: 22px;
}

.testing-workflow-output {
  margin-top: 4px;
  color: #f97316;
  font-size: 12px;
  line-height: 20px;
}

.process-list {
  display: grid;
  gap: 14px;
}

.process-item {
  display: flex;
  gap: 14px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #ffffff;
}

.process-index {
  flex: 0 0 32px;
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  border-radius: 50%;
  color: #ffffff;
  font-weight: 800;
  background: #1e40af;
}

.process-content {
  flex: 1;
  min-width: 0;
}

.process-title {
  color: #111827;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 6px;
}

.process-goal {
  color: #1e40af;
  font-size: 13px;
  line-height: 21px;
  margin-bottom: 8px;
}

.process-points {
  margin: 0;
  padding-left: 18px;
  color: #6b7280;
  font-size: 13px;
  line-height: 22px;
}

.boundary-table-wrap {
  width: 100%;
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.boundary-table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
  color: #6b7280;
  font-size: 13px;
  line-height: 22px;
}

.boundary-table--summary {
  min-width: 720px;
}

.boundary-table th,
.boundary-table td {
  padding: 12px 14px;
  border-bottom: 1px solid #e5e7eb;
  vertical-align: top;
  text-align: left;
}

.boundary-table th {
  color: #111827;
  font-weight: 700;
  background: #f9fafb;
  white-space: nowrap;
}

.boundary-table tr:last-child td {
  border-bottom: 0;
}

.boundary-table td:first-child {
  width: 120px;
  color: #1e40af;
  font-weight: 700;
}

.detail-desc {
  margin-top: 0;
}

.detail-table-wrap {
  max-height: 62vh;
}

.boundary-detail-dialog >>> .el-dialog__body {
  padding-top: 8px;
}

/* ========== Dark Theme ========== */
body.theme-dark .greet-card,
body.theme-dark .work-card,
body.theme-dark .links-card {
  background: #1f2937;
  border-color: #374151;
  box-shadow: none;
}

body.theme-dark .greet-card {
  background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
  color: #ffffff;
  border-color: transparent;
}

body.theme-dark .work-card-title,
body.theme-dark .links-card-title,
body.theme-dark .project-title {
  color: #f9fafb;
}

body.theme-dark .work-stat,
body.theme-dark .project-block {
  background: #111827;
  border-color: #374151;
}

body.theme-dark .work-stat--click:hover {
  background: #1f2937;
  border-color: #fb923c;
}

body.theme-dark .work-stat-value {
  color: #3b82f6;
}

body.theme-dark .work-stat-label,
body.theme-dark .link-label {
  color: #d1d5db;
}

body.theme-dark .work-stat-hint,
body.theme-dark .home-desc,
body.theme-dark .guide-desc {
  color: #9ca3af;
}

body.theme-dark .doc-link >>> span {
  color: #3b82f6;
}

body.theme-dark .process-item,
body.theme-dark .quality-reason-item,
body.theme-dark .testing-workflow-panel {
  background: #1f2937;
  border-color: #374151;
}

body.theme-dark .vibe-warning-panel {
  background: rgba(220, 38, 38, 0.08);
  border-color: rgba(220, 38, 38, 0.2);
}

body.theme-dark .vibe-warning-title {
  color: #f87171;
}

body.theme-dark .vibe-warning-item {
  border-left-color: #f87171;
}

body.theme-dark .vibe-warning-name {
  color: #f9fafb;
}

body.theme-dark .vibe-warning-desc {
  color: #d1d5db;
}

body.theme-dark .quality-reason-kicker,
body.theme-dark .testing-workflow-stage {
  color: #fb923c;
}

body.theme-dark .quality-reason-title,
body.theme-dark .testing-workflow-title,
body.theme-dark .testing-workflow-action {
  color: #f9fafb;
}

body.theme-dark .quality-reason-desc,
body.theme-dark .testing-workflow-desc {
  color: #9ca3af;
}

body.theme-dark .testing-workflow-output {
  color: #fb923c;
}

body.theme-dark .testing-workflow-item {
  border-top-color: #374151;
}

body.theme-dark .process-title,
body.theme-dark .boundary-table th {
  color: #f9fafb;
}

body.theme-dark .process-goal {
  color: #3b82f6;
}

body.theme-dark .process-points,
body.theme-dark .boundary-table {
  color: #d1d5db;
}

body.theme-dark .boundary-table-wrap {
  border-color: #374151;
}

body.theme-dark .boundary-table th {
  background: #374151;
}

body.theme-dark .boundary-table th,
body.theme-dark .boundary-table td {
  border-bottom-color: #374151;
}

body.theme-dark .boundary-table td:first-child {
  color: #3b82f6;
}

@media (max-width: 1100px) {
  .quality-reason-grid {
    grid-template-columns: 1fr;
  }

  .vibe-warning-grid {
    grid-template-columns: 1fr;
  }

  .testing-workflow-head {
    display: block;
  }

  .testing-workflow-desc {
    margin-top: 6px;
  }
}

@media (max-width: 640px) {
  .testing-workflow-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .vibe-title-row {
    display: block;
  }

  .vibe-title-row .el-button {
    margin-top: 10px;
  }
}
</style>
