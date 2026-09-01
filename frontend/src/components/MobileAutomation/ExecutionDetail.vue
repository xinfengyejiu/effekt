<template>
  <div class="process-workspace">
    <header v-if="execution" class="process-header">
      <div class="title-block">
        <el-button size="mini" @click="$router.push({ path: '/mobile-automation/executions' })">返回</el-button>
        <div>
          <h2>{{ execution.execution_no }}</h2>
          <span>{{ ext.app_package || '-' }} · {{ ext.device_serial || '-' }}</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button v-if="htmlReportArtifactId" size="small" type="primary" @click="previewHtmlReport">查看 HTML 报告</el-button>
        <el-button size="small" :loading="loading" @click="refresh">刷新</el-button>
        <el-tag :type="statusTag(execution.status)">{{ statusLabel(execution.status) }}</el-tag>
      </div>
    </header>

    <el-empty v-if="!execution && !loading" description="未找到移动执行记录" />

    <template v-else>
      <main class="process-grid">
        <aside class="device-panel">
          <div class="panel-head">
            <b>设备画面</b>
            <span>{{ screenHint }}</span>
          </div>
          <div class="device-screen">
            <img v-if="screenshotUrl" :src="screenshotUrl" alt="设备执行画面">
            <div v-else class="screen-empty">
              <i class="el-icon-mobile-phone" />
              <span>{{ selectedStep ? '该步骤暂无截图' : '暂无设备截图' }}</span>
            </div>
          </div>
          <div class="device-meta">
            <b>{{ ext.device_serial || '-' }}</b>
            <span>{{ ext.app_package || '-' }}</span>
          </div>
          <div v-if="selectedStep" class="step-detail">
            <div class="step-detail-title">
              <b>步骤 {{ selectedStep.step_no }} 详情</b>
              <el-tag size="mini" :type="stepTag(selectedStep.status)">{{ selectedStep.status || 'pending' }}</el-tag>
            </div>
            <p class="step-detail-instruction">{{ selectedStep.instruction || selectedStep.action_type || '-' }}</p>
            <p v-if="selectedStep.duration_ms" class="step-detail-meta">耗时：{{ selectedStep.duration_ms }} ms</p>
            <div v-if="selectedStep.status === 'failed' || selectedStep.error_message" class="step-detail-error">
              <b>失败原因</b>
              <pre>{{ selectedStep.error_message || '未提供失败详情' }}</pre>
            </div>
            <div v-else class="step-detail-tip">点击左侧步骤可切换查看对应截图；失败步骤会展示失败原因。</div>
          </div>
        </aside>

        <section class="execution-main">
          <section class="progress-panel">
            <div class="progress-top">
              <div>
                <b>执行进度</b>
                <span>{{ metrics.completed || 0 }}/{{ metrics.total || 0 }} 用例完成</span>
              </div>
              <span>{{ elapsed }}</span>
            </div>
            <el-progress
              :percentage="progressPercent"
              :stroke-width="10"
              :show-text="false"
              :status="execution && execution.status === 5 ? 'exception' : execution && execution.status === 4 ? 'success' : undefined"
            />
            <div class="metric-row">
              <div><strong>{{ metrics.passed || 0 }}</strong><span>成功</span></div>
              <div><strong>{{ metrics.failed || 0 }}</strong><span>失败</span></div>
              <div><strong>{{ steps.length }}</strong><span>执行步骤</span></div>
              <div><strong>{{ elapsed }}</strong><span>耗时</span></div>
            </div>
          </section>

          <section class="task-panel">
            <div class="panel-head">
              <b>执行过程</b>
              <span>{{ steps.length }} 个阶段 · 点击步骤查看截图</span>
            </div>
            <div v-if="steps.length" class="step-list">
              <article
                v-for="step in steps"
                :key="step.id"
                :class="['step-item', 'step-' + step.status, { active: selectedStep && selectedStep.id === step.id }]"
                @click="focusStep(step)"
              >
                <div class="step-dot">
                  <i :class="step.status === 'success' ? 'el-icon-check' : step.status === 'failed' ? 'el-icon-close' : 'el-icon-loading'" />
                </div>
                <div class="step-copy">
                  <b>步骤 {{ step.step_no }} · {{ step.instruction || step.action_type }}</b>
                  <small v-if="step.status === 'failed' && step.error_message" class="fail-text">{{ step.error_message }}</small>
                  <small v-else>{{ (step.duration_ms && step.duration_ms + ' ms') || '等待执行' }}</small>
                </div>
                <i
                  v-if="step.after_screenshot_artifact_id || step.before_screenshot_artifact_id"
                  class="el-icon-picture-outline shot-icon"
                  title="有步骤截图"
                />
                <el-tag size="mini" :type="stepTag(step.status)">{{ step.status || 'pending' }}</el-tag>
              </article>
            </div>
            <div v-else class="empty-process">等待执行器写入步骤…</div>
          </section>

          <section class="case-panel">
            <div class="panel-head"><b>子任务结果</b></div>
            <div v-for="item in cases" :key="item.id" class="case-row">
              <span class="case-order">{{ item.run_order }}</span>
              <div class="case-info">
                <b>{{ item.case_title || item.case_key }}</b>
                <div v-if="getAiVerify(item)" class="ai-verify-badge">
                  <el-tag
                    size="mini"
                    :type="aiVerifyTag(getAiVerify(item).verdict)"
                    effect="plain"
                  >AI: {{ aiVerifyLabel(getAiVerify(item).verdict) }}</el-tag>
                  <span class="ai-confidence" :title="getAiVerify(item).reason">
                    {{ getAiVerify(item).reason }}
                  </span>
                </div>
              </div>
              <small>{{ item.result_message || item.error_message || '等待执行' }}</small>
              <el-tag size="mini" :type="caseTag(item.status)">{{ caseLabel(item.status) }}</el-tag>
            </div>
          </section>
        </section>
      </main>

      <section class="log-panel">
        <div class="panel-head"><b>执行日志</b><span v-if="isRunning" class="live-dot">实时</span></div>
        <pre>{{ consoleTail || '等待执行日志…' }}</pre>
      </section>
    </template>
  </div>
</template>

<script>
import { getMobileExecutionProgress, previewMobileArtifact } from '@/api/mobileAutomationApi'

const STATUS = { 0: '待触发', 3: '执行中', 4: '成功', 5: '失败', 6: '已取消', 7: '触发失败' }
const CASE_STATUS = { 0: '待执行', 1: '执行中', 2: '通过', 3: '失败', 4: '阻塞', 5: '跳过', 6: '未找到', 7: '已取消' }

export default {
  name: 'MobileAutomationExecutionDetail',
  data () {
    return {
      loading: false,
      execution: null,
      cases: [],
      steps: [],
      metrics: {},
      consoleTail: '',
      screenshotUrl: '',
      screenshotArtifactId: null,
      htmlReportArtifactId: null,
      selectedStep: null,
      userLockedScreenshot: false,
      pollTimer: null,
      now: Date.now()
    }
  },
  computed: {
    executionId () { return this.$route.query.execution_id },
    ext () { return (this.execution && this.execution.ext) || {} },
    isRunning () { return this.execution && [0, 3].includes(Number(this.execution.status)) },
    progressPercent () {
      const total = Number(this.metrics.total || 0)
      return total ? Math.min(100, Math.round(Number(this.metrics.completed || 0) / total * 100)) : 0
    },
    elapsed () {
      if (!this.execution || !this.execution.start_time) return '--'
      const end = this.execution.end_time ? new Date(this.execution.end_time).getTime() : this.now
      const seconds = Math.max(0, Math.floor((end - new Date(this.execution.start_time).getTime()) / 1000))
      const minutes = Math.floor(seconds / 60)
      return (minutes ? String(minutes).padStart(2, '0') + ':' : '') + String(seconds % 60).padStart(2, '0')
    },
    screenHint () {
      if (this.selectedStep) {
        return '步骤 ' + this.selectedStep.step_no + ' 截图'
      }
      return this.isRunning ? '实时刷新' : '最后画面'
    }
  },
  created () { this.refresh() },
  beforeDestroy () {
    this.stopPolling()
    if (this.screenshotUrl) URL.revokeObjectURL(this.screenshotUrl)
  },
  methods: {
    dataOf (res) { return (res && res.data) || res || {} },
    refresh () {
      if (!this.executionId) return
      this.loading = true
      return getMobileExecutionProgress(this.executionId).then(res => {
        const data = this.dataOf(res)
        this.execution = data.execution || null
        this.cases = data.cases || []
        this.steps = data.steps || []
        this.metrics = data.metrics || {}
        this.consoleTail = data.console_tail || ''
        this.htmlReportArtifactId = data.html_report_artifact_id || null
        this.now = Date.now()
        this.syncSelectedStep()
        if (this.userLockedScreenshot && this.selectedStep) {
          const artifactId = this.selectedStep.after_screenshot_artifact_id || this.selectedStep.before_screenshot_artifact_id
          this.loadScreenshot(artifactId)
        } else {
          this.loadScreenshot(data.latest_screenshot_artifact_id)
        }
        this.syncPolling()
      }).finally(() => { this.loading = false })
    },
    syncSelectedStep () {
      if (!this.steps.length) {
        this.selectedStep = null
        return
      }
      if (this.selectedStep) {
        const matched = this.steps.find(item => String(item.id) === String(this.selectedStep.id))
        if (matched) {
          this.selectedStep = matched
          return
        }
      }
      const failed = this.steps.find(item => item.status === 'failed')
      if (failed && (!this.isRunning || Number(this.execution && this.execution.status) === 5)) {
        this.focusStep(failed, false)
      }
    },
    syncPolling () {
      this.stopPolling()
      if (this.isRunning) this.pollTimer = setInterval(() => this.refresh(), 3000)
    },
    stopPolling () {
      if (this.pollTimer) clearInterval(this.pollTimer)
      this.pollTimer = null
    },
    loadScreenshot (artifactId) {
      if (!artifactId) {
        if (this.screenshotUrl) {
          URL.revokeObjectURL(this.screenshotUrl)
          this.screenshotUrl = ''
        }
        this.screenshotArtifactId = null
        return
      }
      if (String(artifactId) === String(this.screenshotArtifactId)) return
      this.screenshotArtifactId = artifactId
      previewMobileArtifact(artifactId).then(blob => {
        if (this.screenshotUrl) URL.revokeObjectURL(this.screenshotUrl)
        this.screenshotUrl = URL.createObjectURL(blob)
      }).catch(() => { this.screenshotUrl = '' })
    },
    previewHtmlReport () {
      previewMobileArtifact(this.htmlReportArtifactId).then(blob => {
        const url = URL.createObjectURL(blob)
        window.open(url, '_blank')
        window.setTimeout(() => URL.revokeObjectURL(url), 60000)
      })
    },
    focusStep (step, lock = true) {
      this.selectedStep = step
      if (lock) this.userLockedScreenshot = true
      const artifactId = step.after_screenshot_artifact_id || step.before_screenshot_artifact_id
      this.loadScreenshot(artifactId)
    },
    statusLabel (value) { return STATUS[value] || value || '-' },
    statusTag (value) { return { 0: 'info', 3: 'warning', 4: 'success', 5: 'danger', 6: 'info', 7: 'danger' }[value] || 'info' },
    caseLabel (value) { return CASE_STATUS[value] || value || '-' },
    caseTag (value) { return { 2: 'success', 3: 'danger', 1: 'warning', 7: 'info' }[value] || 'info' },
    stepTag (value) { return { success: 'success', failed: 'danger', running: 'warning' }[value] || 'info' },
    getAiVerify (item) {
      const ext = item && item.ext
      if (ext && ext.ai_verify) return ext.ai_verify
      return null
    },
    aiVerifyLabel (verdict) {
      return { pass: '通过', fail: '失败', uncertain: '待确认' }[verdict] || verdict || '-'
    },
    aiVerifyTag (verdict) {
      return { pass: 'success', fail: 'danger', uncertain: 'warning' }[verdict] || 'info'
    }
  }
}
</script>

<style scoped>
.process-workspace { min-height: 100%; padding: 20px; background: #f5f7fb; color: #24324a; }
.process-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding: 16px 20px; background: #fff; border: 1px solid #e5ebf5; border-radius: 10px; }
.title-block { display: flex; align-items: center; gap: 14px; }.title-block h2 { margin: 0 0 2px; font-size: 20px; }.title-block span, .panel-head span, small { color: #8190a5; font-size: 12px; }.header-actions { display: flex; align-items: center; gap: 10px; }
.process-grid { display: grid; grid-template-columns: 330px minmax(0, 1fr); gap: 16px; }.device-panel, .execution-main > section, .log-panel { background: #fff; border: 1px solid #e5ebf5; border-radius: 10px; overflow: hidden; }.panel-head { display: flex; justify-content: space-between; align-items: center; padding: 13px 16px; border-bottom: 1px solid #edf1f6; }.device-screen { min-height: 420px; display: flex; align-items: center; justify-content: center; background: #1f2937; }.device-screen img { display: block; width: 100%; max-height: 560px; object-fit: contain; }.screen-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; color: #b7c1d0; }.screen-empty i { font-size: 42px; }.device-meta { padding: 12px 16px; display: flex; flex-direction: column; gap: 4px; font-size: 12px; border-top: 1px solid #edf1f6; }
.step-detail { padding: 12px 16px 16px; border-top: 1px solid #edf1f6; background: #fafcff; }.step-detail-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }.step-detail-instruction { margin: 0 0 8px; font-size: 13px; line-height: 1.5; color: #31425c; }.step-detail-meta { margin: 0 0 8px; font-size: 12px; color: #8190a5; }.step-detail-error { margin-top: 8px; padding: 10px 12px; border-radius: 8px; background: #fff5f5; border: 1px solid #f5c6c6; }.step-detail-error b { display: block; margin-bottom: 6px; color: #d64545; font-size: 12px; }.step-detail-error pre { margin: 0; white-space: pre-wrap; word-break: break-word; color: #8a2f2f; font: 12px/1.6 Consolas, 'Courier New', monospace; }.step-detail-tip { font-size: 12px; color: #98a5b7; line-height: 1.5; }
.execution-main { display: flex; flex-direction: column; gap: 16px; }.progress-panel { padding: 16px; }.progress-top { display: flex; justify-content: space-between; margin-bottom: 12px; }.progress-top b { margin-right: 12px; }.metric-row { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 16px; }.metric-row div { display: flex; flex-direction: column; gap: 2px; border-right: 1px solid #edf1f6; padding-left: 12px; }.metric-row div:last-child { border-right: 0; }.metric-row strong { font-size: 20px; color: #2d76f9; }.step-list { padding: 8px; }.step-item { display: flex; align-items: center; gap: 12px; min-height: 58px; margin: 6px 0; padding: 10px 12px; border: 1px solid #e8edf5; border-left: 3px solid #aab7c7; border-radius: 7px; cursor: pointer; }.step-item:hover { background: #f8fbff; }.step-item.active { box-shadow: inset 0 0 0 1px #7aa7ff; background: #eef5ff; }.step-success { border-color: #b7e7c5; background: #f3fcf5; }.step-failed { border-color: #f4c0c0; background: #fff7f7; }.step-running { border-color: #b8d4ff; background: #f4f8ff; }.step-dot { width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: #eef2f7; color: #75839a; }.step-success .step-dot { background: #dff5e5; color: #36a65f; }.step-failed .step-dot { background: #fee4e4; color: #dc4f4f; }.step-copy { flex: 1; display: flex; flex-direction: column; gap: 3px; min-width: 0; }.step-copy b { font-size: 13px; }.fail-text { color: #d64545 !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }.shot-icon { color: #5b8def; font-size: 16px; }.empty-process { padding: 30px; text-align: center; color: #98a5b7; }.case-row { display: grid; grid-template-columns: 32px minmax(130px, 1fr) minmax(160px, 1.4fr) auto; align-items: center; gap: 10px; padding: 11px 16px; border-bottom: 1px solid #edf1f6; font-size: 13px; }.case-order { color: #4c84ed; font-weight: 700; }.case-row small { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }.case-info { min-width: 0; }.case-info b { display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }.ai-verify-badge { display: flex; align-items: center; gap: 8px; margin-top: 4px; font-size: 11px; }.ai-confidence { color: #8190a5; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }.log-panel { margin-top: 16px; }.log-panel pre { max-height: 300px; margin: 0; padding: 14px 16px; overflow: auto; background: #111827; color: #d5e2f3; font: 12px/1.75 Consolas, 'Courier New', monospace; white-space: pre-wrap; }.live-dot { color: #24a55a !important; font-weight: 600; }.live-dot::before { content: ''; display: inline-block; width: 7px; height: 7px; margin-right: 5px; border-radius: 50%; background: #24a55a; }
@media (max-width: 960px) { .process-grid { grid-template-columns: 1fr; }.device-screen { min-height: 300px; }.metric-row { grid-template-columns: repeat(2, 1fr); gap: 12px; }.metric-row div { border: 0; }.case-row { grid-template-columns: 28px 1fr auto; }.case-row small { display: none; }.process-header { align-items: flex-start; gap: 12px; flex-direction: column; } }
</style>
