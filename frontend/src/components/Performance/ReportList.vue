<template>
  <div class="page-wrap performance-page">
    <page-section title="性能报告">
      <el-form :inline="true" size="small" @submit.native.prevent>
        <el-form-item label="Run ID"><el-input v-model.trim="runId" clearable placeholder="执行记录ID" style="width:160px;" @keyup.enter.native="fetchReport" /></el-form-item>
        <el-form-item><el-button type="primary" @click="fetchReport">查询报告</el-button><el-button :disabled="!runId" @click="createAiAnalysis">AI可审计分析</el-button></el-form-item>
      </el-form>
      <el-alert v-if="!runId" title="请从执行记录进入，或输入 Run ID 查询统一报告。" type="info" show-icon :closable="false" style="margin-top:12px;" />
      <div v-loading="loading" class="report-body">
        <div v-if="report" class="report-summary">
          <div class="summary-item"><span>报告ID</span><strong>{{ report.id || '-' }}</strong></div>
          <div class="summary-item"><span>Run ID</span><strong>{{ report.run_id || report.runId || runId }}</strong></div>
          <div class="summary-item"><span>原生报告</span><strong><el-link v-if="nativeUrl" :href="nativeUrl" target="_blank" type="primary">打开原生报告</el-link><template v-else>-</template></strong></div>
          <div class="summary-item"><span>结论</span><strong>{{ summaryText }}</strong></div>
        </div>

        <el-row :gutter="16" style="margin-top:16px;">
          <el-col :span="12">
            <el-card shadow="never"><div slot="header">统一 metrics.json</div><el-table :data="metrics" size="small" border><el-table-column label="指标"><template slot-scope="scope">{{ scope.row.metric_name || scope.row.metricName || '-' }}</template></el-table-column><el-table-column label="值"><template slot-scope="scope">{{ scope.row.metric_value || scope.row.metricValue || '-' }}</template></el-table-column><el-table-column label="单位" width="80"><template slot-scope="scope">{{ scope.row.metric_unit || scope.row.metricUnit || scope.row.unit || '-' }}</template></el-table-column></el-table></el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never"><div slot="header">基础门禁</div><el-table :data="gateResults" size="small" border><el-table-column label="规则"><template slot-scope="scope">{{ scope.row.rule_name || scope.row.ruleName || scope.row.metric_name || scope.row.metricName || '-' }}</template></el-table-column><el-table-column label="结果" width="90"><template slot-scope="scope">{{ scope.row.result || scope.row.status || '-' }}</template></el-table-column><el-table-column prop="message" label="说明" /></el-table></el-card>
          </el-col>
        </el-row>
        <el-card v-if="aiAnalysis" shadow="never" style="margin-top:16px;"><div slot="header">AI 分析审计</div><pre class="analysis-pre">{{ aiAnalysis }}</pre></el-card>
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { createPerformanceAiAnalysis, getPerformanceGateResults, getPerformanceNativeReport, getPerformanceReport, getPerformanceReportMetrics } from '@/api/performanceApi'

export default {
  name: 'PerformanceReportList',
  components: { PageSection },
  data() { return { runId: this.$route.query.runId || '', loading: false, report: null, metrics: [], gateResults: [], aiAnalysis: '' } },
  computed: {
    nativeUrl() { return this.report && (this.report.native_report_url || this.report.nativeReportUrl || this.report.report_url || this.report.reportUrl) },
    summaryText() {
      if (!this.report) return '-'
      const summary = this.report.summary || this.report.result_summary || this.report.resultSummary || this.report.summary_json || this.report.summaryJson
      if (!summary) return '-'
      return typeof summary === 'string' ? summary : JSON.stringify(summary)
    }
  },
  created() { if (this.runId) this.fetchReport() },
  methods: {
    listOf(res) { const d = res && res.data ? res.data : res || {}; return d.items || d.list || d.data || [] },
    fetchReport() {
      if (!this.runId) return
      this.loading = true
      Promise.all([getPerformanceReport(this.runId), getPerformanceReportMetrics(this.runId), getPerformanceGateResults(this.runId), getPerformanceNativeReport(this.runId).catch(() => ({}))]).then(([r, m, g, n]) => {
        const report = (r && r.data) || r || {}
        const nativeInfo = (n && n.data) || n || {}
        this.report = Object.assign({}, report, nativeInfo)
        this.metrics = this.listOf(m)
        this.gateResults = this.listOf(g)
      }).finally(() => { this.loading = false })
    },
    createAiAnalysis() {
      createPerformanceAiAnalysis(this.runId, {}).then(res => { this.aiAnalysis = JSON.stringify((res && res.data) || res || {}, null, 2); this.$message.success('AI分析已生成') })
    }
  }
}
</script>

<style scoped>
.report-body { margin-top: 12px; }
.report-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); border: 1px solid #ebeef5; border-radius: 4px; overflow: hidden; }
.summary-item { display: flex; min-height: 42px; border-right: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5; }
.summary-item:nth-child(2n) { border-right: 0; }
.summary-item:nth-last-child(-n+2) { border-bottom: 0; }
.summary-item span { width: 110px; padding: 12px; color: #909399; background: #fafafa; }
.summary-item strong { flex: 1; padding: 12px; color: #303133; font-weight: 500; }
.analysis-pre { margin: 0; white-space: pre-wrap; color: #334155; }
</style>
