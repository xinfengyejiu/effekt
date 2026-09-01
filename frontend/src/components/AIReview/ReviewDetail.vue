<template>
  <div class="page-wrap ai-review-page">
    <page-section title="AI测试评审详情">
      <template slot="extra">
        <el-button size="small" @click="$router.push({ path: '/ai-review' })">返回列表</el-button>
        <el-button size="small" type="primary" :loading="executeLoading" @click="executeReview">执行AI评审</el-button>
        <el-button size="small" :loading="confirmLoading" @click="confirmReview">确认评审</el-button>
      </template>

      <el-skeleton v-if="loading" :rows="8" animated />
      <div v-else>
        <el-alert
          v-if="executeLoading"
          title="多个 AI agent 正在并行评审，请等待结果返回"
          type="info"
          show-icon
          :closable="false"
          class="review-running-alert">
        </el-alert>
        <div class="summary-grid">
          <div class="summary-item"><span>评审编号</span><b>{{ field(detail, 'review_no', 'reviewNo') || '-' }}</b></div>
          <div class="summary-item"><span>风险等级</span><el-tag :type="riskTag(field(detail, 'risk_level', 'riskLevel'))">{{ field(detail, 'risk_level', 'riskLevel') || '-' }}</el-tag></div>
          <div class="summary-item"><span>评分</span><b>{{ detail.score == null ? '-' : detail.score }}</b></div>
          <div class="summary-item"><span>状态</span><el-tag :type="statusTag(detail.status)">{{ statusLabel(detail.status) }}</el-tag></div>
        </div>

        <el-card shadow="never" class="detail-card">
          <div slot="header">评审结论</div>
          <h3>{{ result.conclusion || '暂无结论' }}</h3>
          <p>{{ result.summary || '-' }}</p>
          <p class="block-suggestion">{{ result.blockSuggestion || result.block_suggestion || '' }}</p>
          <el-tag v-for="item in result.recommendedActions || []" :key="item" size="small" class="action-tag">{{ item }}</el-tag>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">上下文摘要</div>
          <div class="meta-grid">
            <div class="meta-item"><span>标题</span><b>{{ detail.title || '-' }}</b></div>
            <div class="meta-item"><span>项目</span><b>{{ field(detail, 'project_name', 'projectName') || '-' }}</b></div>
            <div class="meta-item"><span>评审类型</span><b>{{ reviewTypeLabel(field(detail, 'review_type', 'reviewType')) }}</b></div>
            <div class="meta-item"><span>来源类型</span><b>{{ sourceTypeLabel(field(detail, 'source_type', 'sourceType')) }}</b></div>
            <div class="meta-item"><span>来源ID</span><b>{{ field(detail, 'source_id', 'sourceId') || '-' }}</b></div>
            <div class="meta-item"><span>创建时间</span><b>{{ field(detail, 'created_time', 'createdTime') || '-' }}</b></div>
          </div>
          <pre class="context-preview">{{ contextText }}</pre>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">风险发现</div>
          <el-table :data="findings" border style="width:100%;">
            <el-table-column label="风险" width="90"><template slot-scope="scope"><el-tag size="mini" :type="riskTag(field(scope.row, 'risk_level', 'riskLevel'))">{{ field(scope.row, 'risk_level', 'riskLevel') || '-' }}</el-tag></template></el-table-column>
            <el-table-column label="类型" width="120"><template slot-scope="scope">{{ field(scope.row, 'finding_type', 'findingType') || '-' }}</template></el-table-column>
            <el-table-column label="模块" min-width="130" show-overflow-tooltip><template slot-scope="scope">{{ field(scope.row, 'module_name', 'moduleName') || '-' }}</template></el-table-column>
            <el-table-column label="标题" min-width="180" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.title || '-' }}</template></el-table-column>
            <el-table-column label="建议" min-width="220" show-overflow-tooltip><template slot-scope="scope">{{ scope.row.suggestion || '-' }}</template></el-table-column>
            <el-table-column label="状态" width="110"><template slot-scope="scope"><el-tag size="mini">{{ scope.row.status || '-' }}</el-tag></template></el-table-column>
            <el-table-column label="操作" width="210" fixed="right">
              <template slot-scope="scope">
                <el-button type="text" @click="updateFinding(scope.row, 'accepted')">接收</el-button>
                <el-button type="text" @click="updateFinding(scope.row, 'ignored')">忽略</el-button>
                <el-button type="text" @click="updateFinding(scope.row, 'fixed')">修复</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card shadow="never" class="detail-card">
          <div slot="header">建议用例</div>
          <el-table :data="caseSuggestions" border style="width:100%;">
            <el-table-column label="模块" min-width="130" show-overflow-tooltip><template slot-scope="scope">{{ field(scope.row, 'module_name', 'moduleName') || '-' }}</template></el-table-column>
            <el-table-column label="用例标题" min-width="220" show-overflow-tooltip><template slot-scope="scope">{{ field(scope.row, 'case_title', 'caseTitle') || '-' }}</template></el-table-column>
            <el-table-column label="优先级" width="80"><template slot-scope="scope">{{ scope.row.priority }}</template></el-table-column>
            <el-table-column label="状态" width="110"><template slot-scope="scope"><el-tag size="mini">{{ field(scope.row, 'action_status', 'actionStatus') || '-' }}</el-tag></template></el-table-column>
            <el-table-column label="关联用例" width="130"><template slot-scope="scope">{{ caseSuggestionCaseText(scope.row) }}</template></el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template slot-scope="scope">
                <el-button type="text" @click="importCase(scope.row)">导入</el-button>
                <el-button type="text" @click="linkCase(scope.row)">关联</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getAiReviewDetail, executeAiReview, confirmAiReview, updateAiReviewFinding, importAiReviewCase, linkAiReviewCase } from '@/api/aiReviewApi'

const REVIEW_TYPE_LABELS = { requirement: '需求评审', change: '变更评审', case: '用例评审', bug: '缺陷评审', release: '发布评审' }
const SOURCE_TYPE_LABELS = { manual: '手工输入', document: '需求文档', precise_analysis: '精准测试', case: '测试用例', bug: '缺陷', release: '发布' }
const STATUS_LABELS = { pending: '待执行', running: '执行中', success: '已完成', failed: '失败', confirmed: '已确认' }

export default {
  name: 'AiReviewDetail',
  components: { PageSection },
  data() {
    return { loading: false, executeLoading: false, confirmLoading: false, detail: {} }
  },
  computed: {
    reviewId() { return this.$route.query.id },
    result() { return this.field(this.detail, 'result_summary', 'resultSummary') || {} },
    context() { return this.field(this.detail, 'context_payload', 'contextPayload') || {} },
    findings() { return this.detail.findings || [] },
    caseSuggestions() { return this.detail.caseSuggestions || this.detail.case_suggestions || [] },
    contextText() {
      const source = this.context.sourceSummary || {}
      const change = this.context.changeSummary || {}
      const coverage = this.context.coverageSummary || {}
      return JSON.stringify({ sourceSummary: source, changeSummary: change, coverageSummary: coverage }, null, 2)
    }
  },
  created() { this.fetchDetail() },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    field(row, snake, camel) { return row && row[snake] !== undefined ? row[snake] : row ? row[camel] : undefined },
    fetchDetail() {
      this.loading = true
      getAiReviewDetail({ reviewId: this.reviewId }).then(res => { this.detail = this.apiData(res) }).finally(() => { this.loading = false })
    },
    executeReview() {
      this.executeLoading = true
      executeAiReview({ reviewId: this.reviewId })
        .then(() => { this.$message.success('评审执行完成'); this.fetchDetail() })
        .catch(err => {
          const msg = (err && err.message) || (err && err.msg) || '评审执行失败'
          this.$message.error(msg)
          this.fetchDetail()
        })
        .finally(() => { this.executeLoading = false })
    },
    confirmReview() {
      this.confirmLoading = true
      confirmAiReview({ reviewId: this.reviewId }).then(() => { this.$message.success('评审已确认'); this.fetchDetail() }).finally(() => { this.confirmLoading = false })
    },
    updateFinding(row, status) {
      updateAiReviewFinding({ findingId: row.id, status }).then(() => { this.$message.success('风险项已更新'); this.fetchDetail() })
    },
    importCase(row) {
      importAiReviewCase({ suggestionId: row.id }).then(() => { this.$message.success('建议用例已导入'); this.fetchDetail() })
    },
    linkCase(row) {
      this.$prompt('请输入已有用例编号或ID', '关联用例', { inputPattern: /\S+/, inputErrorMessage: '请输入用例编号或ID' }).then(({ value }) => {
        return linkAiReviewCase({ suggestionId: row.id, caseId: value, caseKey: value })
      }).then(() => { this.$message.success('建议用例已关联'); this.fetchDetail() }).catch(() => {})
    },
    caseSuggestionCaseText(row) {
      return this.field(row, 'matched_case_key', 'matchedCaseKey') ||
        this.field(row, 'created_case_key', 'createdCaseKey') ||
        '-'
    },
    reviewTypeLabel(v) { return REVIEW_TYPE_LABELS[v] || v || '-' },
    sourceTypeLabel(v) { return SOURCE_TYPE_LABELS[v] || v || '-' },
    statusLabel(v) { return STATUS_LABELS[v] || v || '-' },
    statusTag(v) { return { pending: 'info', running: 'warning', success: 'success', failed: 'danger', confirmed: 'primary' }[v] || 'info' },
    riskTag(v) { return { low: 'success', medium: 'warning', high: 'danger', critical: 'danger' }[String(v || '').toLowerCase()] || 'info' }
  }
}
</script>

<style scoped>
.review-running-alert { margin-bottom: 14px; }
.summary-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.summary-item { border: 1px solid #ebeef5; padding: 12px; border-radius: 4px; background: #fff; }
.summary-item span { display: block; color: #909399; font-size: 12px; margin-bottom: 8px; }
.summary-item b { font-size: 16px; color: #303133; }
.meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border-top: 1px solid #ebeef5; border-left: 1px solid #ebeef5; }
.meta-item { display: grid; grid-template-columns: 110px minmax(0, 1fr); min-height: 40px; border-right: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5; }
.meta-item span { padding: 10px 12px; color: #606266; background: #fafafa; }
.meta-item b { padding: 10px 12px; color: #303133; font-weight: 400; word-break: break-all; }
.detail-card { margin-top: 14px; }
.block-suggestion { color: #e6a23c; }
.action-tag { margin-right: 8px; margin-top: 8px; }
.context-preview { margin-top: 12px; max-height: 260px; overflow: auto; padding: 12px; background: #f6f8fa; border-radius: 4px; white-space: pre-wrap; }
@media (max-width: 768px) {
  .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .meta-grid { grid-template-columns: 1fr; }
}
</style>
