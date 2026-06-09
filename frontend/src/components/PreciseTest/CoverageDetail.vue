<template>
  <div class="page-wrap precise-page">
    <page-section title="精准测试-覆盖率明细">
      <template slot="extra">
        <el-button size="small" @click="$router.back()">返回</el-button>
        <el-button size="small" type="primary" :loading="loading" @click="loadDetail">刷新</el-button>
      </template>

      <el-alert
        v-if="detail.id"
        :title="'报告编号：' + (detail.report_no || detail.reportNo || detail.id)"
        type="info"
        :closable="false"
        style="margin-bottom:12px;"
      />

      <el-table v-loading="loading" :data="pagedRows" border>
        <el-table-column prop="file_path" label="文件" min-width="300" show-overflow-tooltip />
        <el-table-column prop="changed_line_count" label="变更行" width="90" />
        <el-table-column prop="covered_changed_line_count" label="已覆盖" width="90" />
        <el-table-column prop="uncovered_changed_line_count" label="未覆盖" width="90" />
        <el-table-column prop="incremental_line_rate" label="增量覆盖率" width="120" />
        <el-table-column label="代码明细" width="120" align="center">
          <template slot-scope="scope">
            <el-button type="text" :disabled="!hasCoverageCode(scope.row)" @click="openCoverageCodeDialog(scope.row)">查看代码</el-button>
          </template>
        </el-table-column>
        <el-table-column label="未覆盖行" min-width="180" show-overflow-tooltip>
          <template slot-scope="scope">{{ text(scope.row.uncovered_lines || scope.row.uncoveredLines) }}</template>
        </el-table-column>
        <el-table-column label="AI风险" min-width="220" show-overflow-tooltip>
          <template slot-scope="scope">{{ summaryText(scope.row.ai_risk_json || scope.row.aiRiskJson) }}</template>
        </el-table-column>
      </el-table>

      <div class="pager-wrap">
        <el-pagination
          background
          layout="total, sizes, prev, pager, next, jumper"
          :current-page="pageNo"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredRows.length"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </page-section>

    <el-dialog :title="coverageCodeDialog.title" :visible.sync="coverageCodeDialog.visible" width="92%" top="4vh" custom-class="code-dialog">
      <div class="code-dialog-meta">
        <span class="meta-file" :title="coverageCodeDialog.filePath || '-'">
          <span class="meta-label">文件：</span><span class="meta-value">{{ coverageCodeDialog.filePath || '-' }}</span>
        </span>
        <span class="meta-lines" :title="text(coverageCodeDialog.changedLines)">
          <span class="meta-label">变更行：</span><span class="meta-value">{{ text(coverageCodeDialog.changedLines) }}</span>
        </span>
        <span class="meta-lines" :title="text(coverageCodeDialog.uncoveredLines)">
          <span class="meta-label">未覆盖行：</span><span class="meta-value">{{ text(coverageCodeDialog.uncoveredLines) }}</span>
        </span>
      </div>
      <el-row :gutter="16">
        <el-col :span="12">
          <div class="code-panel-title">未覆盖代码</div>
          <el-empty v-if="!coverageCodeDialog.uncoveredSnippets.length" description="暂无未覆盖代码片段" />
          <div v-else class="snippet-list">
            <div v-for="(snippet, index) in coverageCodeDialog.uncoveredSnippets" :key="'u' + index" class="snippet-block">
              <div class="snippet-title">片段 {{ index + 1 }}：第 {{ snippet.start || snippet.line || '-' }} - {{ snippet.end || snippet.line || '-' }} 行</div>
              <div class="coverage-code">
                <div
                  v-for="line in snippetLines(snippet, coverageCodeDialog.changedLines, coverageCodeDialog.uncoveredLines)"
                  :key="'u' + index + '-' + line.no + '-' + line.index"
                  class="code-line"
                  :class="{ modified: line.modified && !line.uncovered, uncovered: line.uncovered }"
                >
                  <span class="line-no">{{ line.no }}.</span>
                  <span class="line-marker" :class="{ red: line.uncovered }">{{ line.uncovered ? '!' : (line.modified ? '+' : '') }}</span>
                  <code class="line-code">{{ line.text || ' ' }}</code>
                  <span v-if="line.uncovered" class="line-label uncovered-label">Uncovered</span>
                  <span v-else-if="line.modified" class="line-label modified-label">Modified</span>
                </div>
              </div>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="code-panel-title">完整变更代码</div>
          <el-empty v-if="!coverageCodeDialog.changedSnippets.length" description="暂无变更代码片段" />
          <div v-else class="snippet-list">
            <div v-for="(snippet, index) in coverageCodeDialog.changedSnippets" :key="'c' + index" class="snippet-block">
              <div class="snippet-title">片段 {{ index + 1 }}：第 {{ snippet.start || snippet.line || '-' }} - {{ snippet.end || snippet.line || '-' }} 行</div>
              <div class="coverage-code">
                <div
                  v-for="line in snippetLines(snippet, coverageCodeDialog.changedLines, coverageCodeDialog.uncoveredLines)"
                  :key="'c' + index + '-' + line.no + '-' + line.index"
                  class="code-line"
                  :class="{ modified: line.modified && !line.uncovered, uncovered: line.uncovered }"
                >
                  <span class="line-no">{{ line.no }}.</span>
                  <span class="line-marker" :class="{ red: line.uncovered }">{{ line.uncovered ? '!' : (line.modified ? '+' : '') }}</span>
                  <code class="line-code">{{ line.text || ' ' }}</code>
                  <span v-if="line.uncovered" class="line-label uncovered-label">Uncovered</span>
                  <span v-else-if="line.modified" class="line-label modified-label">Modified</span>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getPreciseCoverageDetail } from '@/api/preciseTestApi'

export default {
  name: 'PreciseCoverageDetail',
  components: { PageSection },
  data() {
    return {
      loading: false,
      detail: {},
      pageNo: 1,
      pageSize: 20,
      coverageCodeDialog: {
        visible: false,
        title: '覆盖率代码明细',
        filePath: '',
        changedLines: [],
        uncoveredLines: [],
        changedSnippets: [],
        uncoveredSnippets: []
      }
    }
  },
  computed: {
    coverageId() {
      return this.$route.query.coverageId || this.$route.query.id || ''
    },
    filteredRows() {
      const rows = this.detail.incrementalFiles || []
      return rows.filter(row => Number(row.changed_line_count || row.changedLineCount || 0) > 0 && !this.isSqlFile(row))
    },
    pagedRows() {
      const start = (this.pageNo - 1) * this.pageSize
      return this.filteredRows.slice(start, start + this.pageSize)
    }
  },
  watch: {
    '$route.query.coverageId': 'loadDetail',
    '$route.query.id': 'loadDetail'
  },
  created() {
    this.loadDetail()
  },
  methods: {
    loadDetail() {
      if (!this.coverageId) return
      this.loading = true
      return getPreciseCoverageDetail(this.coverageId)
        .then(res => {
          this.detail = (res && res.data) || res || {}
          this.ensurePage()
        })
        .finally(() => {
          this.loading = false
        })
    },
    handleSizeChange(size) {
      this.pageSize = size
      this.pageNo = 1
    },
    handlePageChange(page) {
      this.pageNo = page
    },
    ensurePage() {
      const maxPage = Math.max(1, Math.ceil(this.filteredRows.length / this.pageSize))
      if (this.pageNo > maxPage) this.pageNo = maxPage
      if (this.pageNo < 1) this.pageNo = 1
    },
    openCoverageCodeDialog(row) {
      const changedSnippets = this.snippets(row.changedCodeSnippets || row.changed_code_snippets)
      const uncoveredLines = this.lines(row.uncovered_lines || row.uncoveredLines)
      const uncoveredSnippets = this.snippets(row.uncoveredCodeSnippets || row.uncovered_code_snippets)
      const pickedUncovered = uncoveredSnippets.length ? uncoveredSnippets : this.pickUncoveredSnippets(changedSnippets, uncoveredLines)
      this.coverageCodeDialog = {
        visible: true,
        title: '覆盖率代码明细',
        filePath: row.file_path || row.filePath || '',
        changedLines: this.lines(row.changedLines || row.changed_lines),
        uncoveredLines,
        changedSnippets,
        uncoveredSnippets: pickedUncovered
      }
    },
    hasCoverageCode(row) {
      return this.snippets(row.changedCodeSnippets || row.changed_code_snippets).length ||
        this.snippets(row.uncoveredCodeSnippets || row.uncovered_code_snippets).length
    },
    snippetLines(snippet, changedLines, uncoveredLines) {
      const changedSet = new Set(this.lines(changedLines).map(item => Number(item)))
      const uncoveredSet = new Set(this.lines(uncoveredLines).map(item => Number(item)))
      const start = Number(snippet.start || snippet.line || 1)
      return String(snippet.content || '').split(/\r?\n/).map((text, index) => {
        const no = start + index
        return { index, no, text, modified: changedSet.has(no), uncovered: uncoveredSet.has(no) }
      })
    },
    snippets(value) {
      return Array.isArray(value) ? value : []
    },
    lines(value) {
      if (Array.isArray(value)) return value.map(item => Number(item)).filter(item => !Number.isNaN(item))
      if (typeof value === 'string') return value.split(',').map(item => Number(item.trim())).filter(item => !Number.isNaN(item))
      return []
    },
    pickUncoveredSnippets(snippets, uncoveredLines) {
      const uncoveredSet = new Set(this.lines(uncoveredLines))
      return (snippets || []).filter(snippet => {
        const start = Number(snippet.start || snippet.line || 1)
        const lineCount = String(snippet.content || '').split(/\r?\n/).length
        for (let index = 0; index < lineCount; index += 1) {
          if (uncoveredSet.has(start + index)) return true
        }
        return false
      })
    },
    isSqlFile(row) {
      const filePath = String(row.file_path || row.filePath || '').trim().replace(/^["']|["']$/g, '').toLowerCase()
      return filePath.endsWith('.sql')
    },
    summaryText(v) {
      try {
        const obj = typeof v === 'string' ? JSON.parse(v) : v
        if (!obj) return '-'
        if (obj.summary) return obj.summary
        if (obj.releaseAdvice) return obj.releaseAdvice
        return JSON.stringify(obj)
      } catch (e) {
        return v || '-'
      }
    },
    text(v) {
      if (Array.isArray(v)) return v.join(', ')
      if (v && typeof v === 'object') return JSON.stringify(v)
      return v || '-'
    }
  }
}
</script>

<style scoped>
.pager-wrap {
  margin-top: 16px;
  text-align: right;
}

.code-dialog-meta {
  display: flex;
  flex-wrap: nowrap;
  gap: 12px 24px;
  margin-bottom: 12px;
  color: #606266;
  font-size: 13px;
  min-width: 0;
}

.code-dialog-meta span {
  min-width: 0;
}

.code-dialog-meta > span {
  display: flex;
  align-items: center;
}

.meta-label {
  flex: 0 0 auto;
}

.meta-value {
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-file {
  flex: 1 1 33.333%;
  min-width: 160px;
}

.meta-lines {
  flex: 0 1 22%;
  min-width: 0;
}

.code-panel-title {
  padding: 8px 0;
  font-weight: 600;
  color: #303133;
}

.snippet-list {
  max-height: 70vh;
  overflow: auto;
  border: 1px solid #dcdfe6;
  background: #fff;
}

.snippet-block + .snippet-block {
  border-top: 1px solid #dcdfe6;
}

.snippet-title {
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  color: #303133;
  font-weight: 600;
}

.coverage-code {
  min-width: 980px;
  background: #fff;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.55;
}

.code-line {
  display: flex;
  min-height: 22px;
  white-space: pre;
}

.code-line.modified {
  background: #d9ffd2;
}

.code-line.uncovered {
  background: #f8b5b5;
}

.line-no {
  flex: 0 0 56px;
  padding-right: 8px;
  text-align: right;
  color: #909399;
  background: #f7f7f7;
  border-right: 1px solid #e4e7ed;
  user-select: none;
}

.line-marker {
  flex: 0 0 20px;
  text-align: center;
  color: #35a61d;
}

.line-marker.red {
  color: #d91e18;
}

.line-code {
  flex: 1;
  padding: 0 12px;
  color: #111;
  background: transparent;
  font-family: inherit;
}

.line-label {
  flex: 0 0 180px;
  margin-left: 10px;
  color: #ff2a1a;
  font-weight: 700;
  text-align: left;
}

.modified-label::before,
.uncovered-label::before {
  content: '';
  display: inline-block;
  width: 110px;
  margin-right: 6px;
  border-top: 2px solid #ff2a1a;
  vertical-align: middle;
}
</style>
