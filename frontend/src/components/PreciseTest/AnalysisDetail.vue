<template>
  <div class="page-wrap precise-page">
    <page-section title="变更分析详情">
      <template slot="extra">
        <el-button size="small" @click="$router.back()">返回</el-button>
        <el-button size="small" type="primary" :loading="loading" @click="reload">刷新</el-button>
      </template>

      <el-alert
        v-if="missingDetail"
        title="暂无变更分析详情，请先在变更分析列表中创建或选择一条记录"
        type="info"
        show-icon
        :closable="false"
        style="margin-bottom:12px;"
      />

      <el-descriptions v-if="detail.id" :column="2" border size="small">
        <el-descriptions-item label="分析编号">{{ detail.analysis_no || detail.analysisNo || detail.id }}</el-descriptions-item>
        <el-descriptions-item label="标题">{{ detail.title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="产品名称">{{ detail.product_name || detail.productName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="项目名称">{{ detail.project_name || detail.projectName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="仓库">{{ detail.repository_url || detail.repositoryUrl || '-' }}</el-descriptions-item>
        <el-descriptions-item label="分支">{{ detail.branch_name || detail.branchName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Base Commit">{{ detail.base_commit || detail.baseCommit || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Target Commit">{{ detail.target_commit || detail.targetCommit || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-tabs v-loading="loading" v-model="activeTab" style="margin-top:16px;">
        <el-tab-pane label="变更文件" name="files">
          <el-table :data="pagedChangedFiles" border>
            <el-table-column prop="file_path" label="文件路径" min-width="300" show-overflow-tooltip />
            <el-table-column prop="change_type" label="变更类型" width="110" />
            <el-table-column label="变更行" min-width="180" show-overflow-tooltip>
              <template slot-scope="scope">{{ text(scope.row.changed_lines || scope.row.changedLines) }}</template>
            </el-table-column>
            <el-table-column label="代码片段" width="140" align="center">
              <template slot-scope="scope">
                <el-button type="text" :disabled="!snippetsOf(scope.row).length" @click="openSnippetDialog(scope.row)">查看代码片段</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pager-wrap">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next, jumper"
              :current-page="changedFilePageNo"
              :page-size="changedFilePageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="changedFiles.length"
              @size-change="handleChangedFileSizeChange"
              @current-change="handleChangedFilePageChange"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="AI影响分析" name="ai">
          <div class="impact-summary">
            <div class="summary-title">综合结论</div>
            <div class="summary-text">{{ aiImpact.summary || '-' }}</div>
            <div class="summary-meta">
              <el-tag size="mini" type="warning">置信度 {{ percent(aiImpact.confidence) }}</el-tag>
              <el-tag size="mini" type="danger">高风险 {{ highRiskCount }} 项</el-tag>
              <el-tag size="mini" type="info">模块 {{ affectedModules.length }} 个</el-tag>
              <el-tag size="mini" type="info">接口 {{ affectedApis.length }} 个</el-tag>
            </div>
          </div>

          <div class="impact-section-title">受影响模块</div>
          <el-table :data="affectedModules" border>
            <el-table-column prop="moduleName" label="模块" min-width="150" show-overflow-tooltip />
            <el-table-column label="风险" width="90">
              <template slot-scope="scope"><el-tag size="mini" :type="riskTag(scope.row.riskLevel)">{{ scope.row.riskLevel || '-' }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="changeFileCount" label="文件数" width="90" />
            <el-table-column prop="changeLineCount" label="变更行" width="90" />
            <el-table-column prop="impact" label="影响说明" min-width="260" show-overflow-tooltip />
          </el-table>

          <div class="impact-section-title">受影响接口/链路</div>
          <el-table :data="affectedApis" border>
            <el-table-column prop="apiPath" label="接口/链路" min-width="220" show-overflow-tooltip />
            <el-table-column label="风险" width="90">
              <template slot-scope="scope"><el-tag size="mini" :type="riskTag(scope.row.riskLevel)">{{ scope.row.riskLevel || '-' }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="impact" label="验证重点" min-width="260" show-overflow-tooltip />
          </el-table>

          <el-row :gutter="16" style="margin-top:16px;">
            <el-col :span="8">
              <div class="list-panel">
                <div class="impact-section-title compact">风险点</div>
                <ul><li v-for="(item, index) in aiImpact.riskPoints || []" :key="'r' + index">{{ item }}</li></ul>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="list-panel">
                <div class="impact-section-title compact">测试关注点</div>
                <ul><li v-for="(item, index) in aiImpact.suggestedTestFocus || []" :key="'f' + index">{{ item }}</li></ul>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="list-panel">
                <div class="impact-section-title compact">推荐策略</div>
                <ul><li v-for="(item, index) in aiImpact.recommendationStrategy || []" :key="'s' + index">{{ item }}</li></ul>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="推荐用例" name="recommendations">
          <el-table :data="recommendations" border>
            <el-table-column prop="recommend_level" label="等级" width="90" />
            <el-table-column prop="case_id" label="用例ID" width="90" />
            <el-table-column prop="case_key" label="用例编号" width="150" show-overflow-tooltip />
            <el-table-column prop="case_title" label="用例标题" min-width="220" show-overflow-tooltip />
            <el-table-column prop="module_name" label="模块" min-width="150" show-overflow-tooltip />
            <el-table-column prop="api_path" label="接口" min-width="180" show-overflow-tooltip />
            <el-table-column prop="reason" label="推荐原因" min-width="240" show-overflow-tooltip />
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="覆盖率与门禁" name="coverage">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-card shadow="never">
                <div slot="header">覆盖率报告</div>
                <el-table :data="coverages" border>
                  <el-table-column prop="report_no" label="报告编号" min-width="140" />
                  <el-table-column prop="coverage_type" label="类型" width="100" />
                  <el-table-column label="操作" width="100">
                    <template slot-scope="scope">
                      <el-button type="text" @click="$router.push({ path: '/precise/coverage/detail', query: { analysisId: detail.id, coverageId: scope.row.id } })">查看</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card shadow="never">
                <div slot="header">质量门禁</div>
                <pre class="json-box">{{ pretty(detail.qualityGate || {}) }}</pre>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </page-section>

    <el-dialog :title="snippetDialog.title" :visible.sync="snippetDialog.visible" width="86%" top="4vh" custom-class="code-dialog">
      <div class="code-dialog-meta">
        <span class="meta-file" :title="snippetDialog.filePath || '-'">
          <span class="meta-label">文件：</span><span class="meta-value">{{ snippetDialog.filePath || '-' }}</span>
        </span>
        <span class="meta-lines" :title="text(snippetDialog.changedLines)">
          <span class="meta-label">变更行：</span><span class="meta-value">{{ text(snippetDialog.changedLines) }}</span>
        </span>
      </div>
      <el-empty v-if="!snippetDialog.snippets.length" description="暂无代码片段" />
      <div v-else class="snippet-list">
        <div v-for="(snippet, index) in snippetDialog.snippets" :key="index" class="snippet-block">
          <div class="snippet-title">片段 {{ index + 1 }}：第 {{ snippet.start || snippet.line || '-' }} - {{ snippet.end || snippet.line || '-' }} 行</div>
          <div class="coverage-code">
            <div v-for="line in snippetLines(snippet, snippetDialog.changedLines)" :key="index + '-' + line.no + '-' + line.index" class="code-line" :class="{ modified: line.modified }">
              <span class="line-no">{{ line.no }}.</span>
              <span class="line-marker">{{ line.modified ? '+' : '' }}</span>
              <code class="line-code">{{ line.text || ' ' }}</code>
              <span v-if="line.modified" class="line-label modified-label">Modified</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getPreciseAnalysisDetail, getPreciseAnalysisList } from '@/api/preciseTestApi'

export default {
  name: 'PreciseAnalysisDetail',
  components: { PageSection },
  data() {
    return {
      loading: false,
      activeTab: 'files',
      detail: {},
      changedFilePageNo: 1,
      changedFilePageSize: 20,
      snippetDialog: { visible: false, title: '代码片段', filePath: '', changedLines: [], snippets: [] }
    }
  },
  computed: {
    analysisId() { return this.$route.query.id || this.$route.query.analysisId || this.$route.params.id || '' },
    changedFiles() { return this.arrayOf(this.detail.changedFiles || this.detail.changed_files) },
    pagedChangedFiles() { const start = (this.changedFilePageNo - 1) * this.changedFilePageSize; return this.changedFiles.slice(start, start + this.changedFilePageSize) },
    recommendations() { return this.arrayOf(this.detail.recommendations || this.detail.recommendationList) },
    coverages() { return this.arrayOf(this.detail.coverages || this.detail.coverageList) },
    missingDetail() { return !this.loading && !this.detail.id },
    aiImpact() { return this.objectOf(this.detail.ai_impact_json || this.detail.aiImpactJson) },
    affectedModules() { return this.arrayOf(this.aiImpact.affectedModules) },
    affectedApis() { return this.arrayOf(this.aiImpact.affectedApis) },
    highRiskCount() { return this.affectedModules.concat(this.affectedApis).filter(item => item.riskLevel === 'high').length }
  },
  watch: { '$route.query.id': 'reload', '$route.query.analysisId': 'reload', '$route.params.id': 'reload' },
  created() { this.reload() },
  methods: {
    reload() {
      const id = this.analysisId
      if (!id) return this.loadLatestAnalysis()
      this.loading = true
      return getPreciseAnalysisDetail(id).then(res => {
        this.detail = (res && res.data) || res || {}
        this.ensureChangedFilePage()
      }).finally(() => { this.loading = false })
    },
    loadLatestAnalysis() {
      this.loading = true
      return getPreciseAnalysisList({ pageNo: 1, pageSize: 20 }).then(res => {
        const d = (res && res.data) || res || {}
        const rows = d.items || d.list || d.data || []
        const latest = Array.isArray(rows) && rows.length ? rows.slice().sort((a, b) => Number(b.id || 0) - Number(a.id || 0))[0] : null
        if (latest && latest.id) this.$router.replace({ path: this.$route.path, query: { id: latest.id } })
        else this.detail = {}
      }).finally(() => { this.loading = false })
    },
    openSnippetDialog(row) {
      this.snippetDialog = { visible: true, title: '变更代码片段', filePath: row.file_path || row.filePath || '', changedLines: row.changed_lines || row.changedLines || [], snippets: this.snippetsOf(row) }
    },
    snippetsOf(row) { const snippets = row.code_snippets || row.codeSnippets || []; return Array.isArray(snippets) ? snippets : [] },
    handleChangedFileSizeChange(size) { this.changedFilePageSize = size; this.changedFilePageNo = 1 },
    handleChangedFilePageChange(page) { this.changedFilePageNo = page },
    ensureChangedFilePage() { const maxPage = Math.max(1, Math.ceil(this.changedFiles.length / this.changedFilePageSize)); if (this.changedFilePageNo > maxPage) this.changedFilePageNo = maxPage; if (this.changedFilePageNo < 1) this.changedFilePageNo = 1 },
    arrayOf(v) { return Array.isArray(v) ? v : [] },
    objectOf(v) { try { return typeof v === 'string' ? JSON.parse(v) : (v || {}) } catch (e) { return {} } },
    snippetLines(snippet, changedLines) {
      const changedSet = new Set((changedLines || []).map(item => Number(item)))
      const start = Number(snippet.start || snippet.line || 1)
      return String(snippet.content || '').split(/\r?\n/).map((text, index) => ({ index, no: start + index, text, modified: changedSet.has(start + index) }))
    },
    pretty(v) { try { return JSON.stringify(typeof v === 'string' ? JSON.parse(v) : v, null, 2) } catch (e) { return String(v || '') } },
    text(v) { if (Array.isArray(v)) return v.join(', '); if (v && typeof v === 'object') return JSON.stringify(v); return v || '-' },
    percent(v) { const n = Number(v || 0); return (n > 1 ? n : n * 100).toFixed(0) + '%' },
    riskTag(v) { return v === 'high' ? 'danger' : (v === 'medium' ? 'warning' : 'success') }
  }
}
</script>

<style scoped>
.json-box { background: #f7f8fa; border: 1px solid #ebeef5; padding: 12px; min-height: 120px; white-space: pre-wrap; word-break: break-all; }
.impact-summary { border: 1px solid #dcdfe6; border-radius: 4px; padding: 14px 16px; margin-bottom: 16px; background: #fff; }
.summary-title { font-weight: 600; color: #303133; margin-bottom: 8px; }
.summary-text { color: #303133; line-height: 1.7; white-space: normal; word-break: break-word; overflow-wrap: anywhere; }
.summary-meta { margin-top: 10px; display: flex; gap: 8px; }
.impact-section-title { margin: 16px 0 8px; font-weight: 600; color: #303133; }
.impact-section-title.compact { margin-top: 0; }
.list-panel { border: 1px solid #dcdfe6; border-radius: 4px; padding: 12px 14px; min-height: 220px; background: #fff; }
.list-panel ul { margin: 0; padding-left: 18px; color: #303133; line-height: 1.7; }`r`n.list-panel li { white-space: normal; word-break: break-all; overflow-wrap: anywhere; }
.code-dialog-meta { display: flex; flex-wrap: nowrap; gap: 12px 24px; margin-bottom: 12px; color: #606266; font-size: 13px; min-width: 0; }
.code-dialog-meta span { min-width: 0; }
.code-dialog-meta > span { display: flex; align-items: center; }
.meta-label { flex: 0 0 auto; }
.meta-value { flex: 1 1 auto; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta-file { flex: 1 1 33.333%; min-width: 160px; }
.meta-lines { flex: 0 1 66.667%; min-width: 0; }
.snippet-list { max-height: 72vh; overflow: auto; border: 1px solid #dcdfe6; background: #fff; }
.snippet-block + .snippet-block { border-top: 1px solid #dcdfe6; }
.snippet-title { padding: 8px 12px; background: #f5f7fa; border-bottom: 1px solid #dcdfe6; color: #303133; font-weight: 600; }
.coverage-code { min-width: 980px; background: #fff; font-family: Consolas, Monaco, 'Courier New', monospace; font-size: 13px; line-height: 1.55; }
.code-line { position: relative; display: flex; min-height: 22px; white-space: pre; }
.code-line.modified { background: #d9ffd2; }
.line-no { flex: 0 0 56px; padding-right: 8px; text-align: right; color: #909399; background: #f7f7f7; border-right: 1px solid #e4e7ed; user-select: none; }
.line-marker { flex: 0 0 20px; text-align: center; color: #35a61d; }
.line-code { flex: 1; padding: 0 12px; color: #111; background: transparent; font-family: inherit; }
.line-label { flex: 0 0 180px; margin-left: 10px; color: #ff2a1a; font-weight: 700; text-align: left; }
.modified-label::before { content: ''; display: inline-block; width: 110px; margin-right: 6px; border-top: 2px solid #ff2a1a; vertical-align: middle; }
.pager-wrap { margin-top: 16px; text-align: right; }
</style>

