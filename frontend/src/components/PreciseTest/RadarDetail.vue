<template>
  <div class="page-wrap precise-page" v-loading="loading">
    <page-section title="变更影响雷达详情">
      <template slot="extra">
        <el-button size="small" @click="$router.push('/precise/radar')">返回列表</el-button>
        <el-button size="small" :loading="lineageLoading" @click="recomputeLineage">重算血缘</el-button>
        <el-button size="small" type="primary" @click="goPrecise">打开精准分析</el-button>
      </template>

      <el-descriptions v-if="run" :column="3" border size="small" style="margin-bottom:16px;">
        <el-descriptions-item label="分析编号">{{ run.analysis_no || run.analysisNo || '-' }}</el-descriptions-item>
        <el-descriptions-item label="标题">{{ run.title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="来源">{{ run.source_type || run.sourceType || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Commit ID">
          <span class="mono">{{ run.commit_id || run.commitId || run.target_commit || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ run.commit_date || run.commitDate || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交人">{{ run.commit_author || run.commitAuthor || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Base">{{ run.base_commit || run.baseCommit || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(run.status) }}</el-descriptions-item>
        <el-descriptions-item label="说明">{{ run.commit_remark || run.commitRemark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="仓库" :span="3">{{ run.repository_url || run.repositoryUrl || '-' }}</el-descriptions-item>
        <el-descriptions-item label="原始链接" :span="3">{{ run.source_ref || run.sourceRef || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="变更面" name="diff">
          <el-table :data="pagedDiff" border size="small">
            <el-table-column label="文件" prop="path" min-width="280" show-overflow-tooltip>
              <template slot-scope="scope">{{ scope.row.path || scope.row.file_path || '-' }}</template>
            </el-table-column>
            <el-table-column label="新增行" width="90">
              <template slot-scope="scope">{{ scope.row.added != null ? scope.row.added : '-' }}</template>
            </el-table-column>
            <el-table-column label="删除行" width="90">
              <template slot-scope="scope">{{ scope.row.deleted != null ? scope.row.deleted : '-' }}</template>
            </el-table-column>
            <el-table-column label="类型" width="100">
              <template slot-scope="scope">{{ scope.row.change_type || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template slot-scope="scope">
                <el-button type="text" @click="fillTraceFromFile(scope.row)">追溯此文件</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!changedFiles.length" class="empty-tip">暂无变更文件</div>
          <div v-else class="pager-wrap">
            <el-pagination background layout="total, sizes, prev, pager, next"
              :current-page="pager.diff.pageNo" :page-size="pager.diff.pageSize" :page-sizes="pageSizes"
              :total="changedFiles.length"
              @size-change="v => onSizeChange('diff', v)" @current-change="v => onPageChange('diff', v)" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="行级血缘" name="lineage">
          <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px;"
            title="每行展示：该代码片段命中的最近 Git Commit ID 与提交时间；展开可看完整历史。" />
          <el-table :data="pagedLineage" border size="small" row-key="id">
            <el-table-column type="expand">
              <template slot-scope="scope">
                <el-timeline v-if="(scope.row.histories || []).length">
                  <el-timeline-item v-for="(h, idx) in scope.row.histories" :key="idx" :timestamp="h.date || ''" placement="top">
                    <div class="hist-card">
                      <div>
                        <strong class="mono">{{ h.commit_id || '-' }}</strong>
                        · {{ h.author || '-' }} · {{ h.branch_name || '-' }}
                      </div>
                      <div class="hist-remark">{{ h.remark || '-' }}</div>
                      <div class="hist-date">时间：{{ h.date || '-' }}</div>
                      <pre v-if="h.change_detail" class="hist-snippet">{{ h.change_detail }}</pre>
                    </div>
                  </el-timeline-item>
                </el-timeline>
                <div v-else class="empty-tip">无 pickaxe 历史命中</div>
              </template>
            </el-table-column>
            <el-table-column label="文件" prop="file_path" min-width="180" show-overflow-tooltip />
            <el-table-column label="代码片段" prop="modified_row" min-width="220" show-overflow-tooltip />
            <el-table-column label="Git Commit ID" min-width="200">
              <template slot-scope="scope">
                <span class="mono">{{ scope.row.latest_commit_id || latestCommit(scope.row) || '-' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="提交时间" min-width="170">
              <template slot-scope="scope">{{ scope.row.latest_date || latestDate(scope.row) || '-' }}</template>
            </el-table-column>
            <el-table-column label="作者" width="100" show-overflow-tooltip>
              <template slot-scope="scope">{{ scope.row.latest_author || latestAuthor(scope.row) || '-' }}</template>
            </el-table-column>
            <el-table-column label="历史数" width="80">
              <template slot-scope="scope">{{ (scope.row.histories || []).length }}</template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template slot-scope="scope">
                <el-button type="text" @click="fillTraceFromLineage(scope.row)">再追溯</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!lineage.length" class="empty-tip">暂无血缘数据，可点「重算血缘」或到「代码追溯」手动查</div>
          <div v-else class="pager-wrap">
            <el-pagination background layout="total, sizes, prev, pager, next"
              :current-page="pager.lineage.pageNo" :page-size="pager.lineage.pageSize" :page-sizes="pageSizes"
              :total="lineage.length"
              @size-change="v => onSizeChange('lineage', v)" @current-change="v => onPageChange('lineage', v)" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="代码追溯" name="trace">
          <el-alert type="success" :closable="false" show-icon style="margin-bottom:12px;"
            title="输入变更文件路径 + 代码片段，查出对应 Git Commit ID 与提交时间。" />
          <el-form :model="traceForm" label-width="100px" size="small" style="max-width:900px;">
            <el-form-item label="Git仓库">
              <el-input v-model.trim="traceForm.repositoryUrl" placeholder="默认用当前分析仓库" />
            </el-form-item>
            <el-form-item label="文件路径">
              <el-input v-model.trim="traceForm.filePath" placeholder="如 app/api/controller/caseController.py（建议填写，结果更准）" />
            </el-form-item>
            <el-form-item label="代码片段" required>
              <el-input v-model="traceForm.code" type="textarea" :rows="4"
                placeholder="粘贴变更相关的一行或一段有效代码（不要只贴注释）" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="traceLoading" @click="doTrace">查询 Commit / 时间</el-button>
            </el-form-item>
          </el-form>
          <el-table v-if="traceRows.length" :data="pagedTrace" border size="small">
            <el-table-column label="Git Commit ID" min-width="280">
              <template slot-scope="scope"><span class="mono">{{ scope.row.commit_id || '-' }}</span></template>
            </el-table-column>
            <el-table-column label="提交时间" min-width="180" prop="date" />
            <el-table-column label="作者" width="120" prop="author" show-overflow-tooltip />
            <el-table-column label="分支" width="140" prop="branch_name" show-overflow-tooltip />
            <el-table-column label="说明" min-width="200" prop="remark" show-overflow-tooltip />
          </el-table>
          <div v-if="traceRows.length" class="pager-wrap">
            <el-pagination background layout="total, sizes, prev, pager, next"
              :current-page="pager.trace.pageNo" :page-size="pager.trace.pageSize" :page-sizes="pageSizes"
              :total="traceRows.length"
              @size-change="v => onSizeChange('trace', v)" @current-change="v => onPageChange('trace', v)" />
          </div>
          <div v-else-if="traceSearched" class="empty-tip">未命中历史提交，可换更长/更独特的代码行再试</div>
        </el-tab-pane>

        <el-tab-pane label="必测清单" name="must">
          <el-alert v-if="mustAiPending" type="warning" :closable="false" show-icon style="margin-bottom:12px;"
            title="AI 推荐用例正在后台生成，不影响其它功能使用；稍后刷新本页即可看到结果。" />
          <el-alert v-else-if="mustAiFailed" type="error" :closable="false" show-icon style="margin-bottom:12px;"
            :title="'AI 推荐失败：' + (mustTest.ai_error || '请重试或查看后端日志')" />
          <h4>测试用例</h4>
          <el-table :data="pagedCases" border size="small">
            <el-table-column label="用例/模块" min-width="180" show-overflow-tooltip>
              <template slot-scope="scope">{{ scope.row.title || scope.row.module_name || '-' }}</template>
            </el-table-column>
            <el-table-column label="接口" prop="api_path" min-width="160" show-overflow-tooltip />
            <el-table-column label="优先级" width="90" prop="priority" />
            <el-table-column label="风险" width="90" prop="risk_level" />
            <el-table-column label="原因" prop="reason" min-width="200" show-overflow-tooltip />
            <el-table-column label="操作" width="100">
              <template slot-scope="scope">
                <el-button v-if="scope.row.route" type="text" @click="goRoute(scope.row.route)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="(mustTest.cases || []).length" class="pager-wrap">
            <el-pagination background layout="total, sizes, prev, pager, next"
              :current-page="pager.cases.pageNo" :page-size="pager.cases.pageSize" :page-sizes="pageSizes"
              :total="(mustTest.cases || []).length"
              @size-change="v => onSizeChange('cases', v)" @current-change="v => onPageChange('cases', v)" />
          </div>

          <h4>契约套件</h4>
          <el-table :data="pagedContracts" border size="small">
            <el-table-column label="套件" prop="name" min-width="200" />
            <el-table-column label="操作" width="100">
              <template slot-scope="scope">
                <el-button type="text" @click="goRoute(scope.row.route)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="(mustTest.contracts || []).length" class="pager-wrap">
            <el-pagination background layout="total, sizes, prev, pager, next"
              :current-page="pager.contracts.pageNo" :page-size="pager.contracts.pageSize" :page-sizes="pageSizes"
              :total="(mustTest.contracts || []).length"
              @size-change="v => onSizeChange('contracts', v)" @current-change="v => onPageChange('contracts', v)" />
          </div>

          <h4>巡检组</h4>
          <el-table :data="pagedInspections" border size="small">
            <el-table-column label="巡检组" prop="name" min-width="200" />
            <el-table-column label="操作" width="100">
              <template slot-scope="scope">
                <el-button type="text" @click="goRoute(scope.row.route)">打开</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="(mustTest.inspections || []).length" class="pager-wrap">
            <el-pagination background layout="total, sizes, prev, pager, next"
              :current-page="pager.inspections.pageNo" :page-size="pager.inspections.pageSize" :page-sizes="pageSizes"
              :total="(mustTest.inspections || []).length"
              @size-change="v => onSizeChange('inspections', v)" @current-change="v => onPageChange('inspections', v)" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getImpactRadarDetail, recomputeImpactRadarLineage, traceImpactRadarCode } from '@/api/impactRadarApi'

const STATUS = { 1: '待解析', 2: '已解析', 3: 'AI已分析', 4: '已推荐', 5: '执行中', 6: '已完成', 7: '失败' }

function makePager() {
  return { pageNo: 1, pageSize: 10 }
}

export default {
  name: 'ImpactRadarDetail',
  components: { PageSection },
  data() {
    return {
      loading: false,
      lineageLoading: false,
      traceLoading: false,
      traceSearched: false,
      activeTab: 'lineage',
      pageSizes: [10, 20, 50, 100],
      pager: {
        diff: makePager(),
        lineage: makePager(),
        trace: makePager(),
        cases: makePager(),
        contracts: makePager(),
        inspections: makePager()
      },
      run: null,
      changedFiles: [],
      lineage: [],
      mustTest: { cases: [], contracts: [], inspections: [] },
      traceForm: { repositoryUrl: '', filePath: '', code: '' },
      traceRows: []
    }
  },
  computed: {
    pagedDiff() { return this.slicePage(this.changedFiles, 'diff') },
    pagedLineage() { return this.slicePage(this.lineage, 'lineage') },
    pagedTrace() { return this.slicePage(this.traceRows, 'trace') },
    pagedCases() { return this.slicePage(this.mustTest.cases || [], 'cases') },
    pagedContracts() { return this.slicePage(this.mustTest.contracts || [], 'contracts') },
    pagedInspections() { return this.slicePage(this.mustTest.inspections || [], 'inspections') },
    mustAiPending() {
      const s = (this.mustTest && this.mustTest.ai_status) || ''
      return s === 'pending' || s === 'running'
    },
    mustAiFailed() {
      return ((this.mustTest && this.mustTest.ai_status) || '') === 'failed'
    }
  },
  created() { this.fetchDetail() },
  methods: {
    slicePage(list, key) {
      const rows = list || []
      const p = this.pager[key] || makePager()
      const start = (p.pageNo - 1) * p.pageSize
      return rows.slice(start, start + p.pageSize)
    },
    onPageChange(key, pageNo) {
      this.pager[key].pageNo = pageNo
    },
    onSizeChange(key, pageSize) {
      this.pager[key].pageSize = pageSize
      this.pager[key].pageNo = 1
    },
    resetPagers() {
      Object.keys(this.pager).forEach(key => {
        this.pager[key].pageNo = 1
      })
    },
    fetchDetail() {
      const id = this.$route.query.id
      if (!id) return
      this.loading = true
      getImpactRadarDetail({ id }).then(res => {
        const d = (res && res.data) || res || {}
        this.run = d.run || null
        this.changedFiles = d.changed_files || d.changedFiles || []
        this.lineage = d.lineage || []
        this.mustTest = d.must_test || d.mustTest || { cases: [], contracts: [], inspections: [] }
        this.traceForm.repositoryUrl = (this.run && (this.run.repository_url || this.run.repositoryUrl)) || ''
        this.resetPagers()
      }).finally(() => { this.loading = false })
    },
    recomputeLineage() {
      const id = this.$route.query.id
      if (!id) return
      this.lineageLoading = true
      recomputeImpactRadarLineage({ analysis_id: Number(id) }).then(() => {
        this.$message.success('血缘已重算')
        this.activeTab = 'lineage'
        this.fetchDetail()
      }).finally(() => { this.lineageLoading = false })
    },
    fillTraceFromFile(row) {
      this.traceForm.filePath = row.path || row.file_path || ''
      this.traceForm.code = ''
      this.activeTab = 'trace'
      this.$message.info('已填入文件路径，请再粘贴一段变更代码后查询')
    },
    fillTraceFromLineage(row) {
      this.traceForm.filePath = row.file_path || ''
      this.traceForm.code = row.modified_row || ''
      this.activeTab = 'trace'
      this.doTrace()
    },
    doTrace() {
      if (!(this.traceForm.code || '').trim()) {
        this.$message.warning('请输入代码片段')
        return
      }
      if (!(this.traceForm.repositoryUrl || '').trim()) {
        this.$message.warning('请填写 Git 仓库')
        return
      }
      this.traceLoading = true
      this.traceSearched = false
      traceImpactRadarCode({
        repository_url: this.traceForm.repositoryUrl,
        file_path: this.traceForm.filePath,
        code: this.traceForm.code,
        branch_name: (this.run && (this.run.branch_name || this.run.branchName)) || ''
      }).then(res => {
        const d = (res && res.data) || res || {}
        this.traceRows = d.commits || []
        this.pager.trace.pageNo = 1
        this.traceSearched = true
        if (!this.traceRows.length) this.$message.warning('未命中历史提交')
        else this.$message.success('找到 ' + this.traceRows.length + ' 条相关提交')
      }).finally(() => { this.traceLoading = false })
    },
    latestCommit(row) {
      const h = (row.histories || [])[0]
      return h ? h.commit_id : ''
    },
    latestDate(row) {
      const h = (row.histories || [])[0]
      return h ? h.date : ''
    },
    latestAuthor(row) {
      const h = (row.histories || [])[0]
      return h ? h.author : ''
    },
    goPrecise() {
      const id = this.$route.query.id
      if (id) this.$router.push({ path: '/precise/analysis/detail', query: { id } })
    },
    goRoute(route) {
      if (!route) return
      if (route.indexOf('http') === 0) window.open(route, '_blank')
      else this.$router.push(route)
    },
    statusLabel(s) { return STATUS[s] || (s == null ? '-' : String(s)) }
  }
}
</script>

<style scoped>
.empty-tip { color: #909399; padding: 16px 0; }
.pager-wrap { margin-top: 12px; text-align: right; }
.hist-card { font-size: 13px; }
.hist-remark { margin-top: 4px; color: #606266; }
.hist-date { margin-top: 2px; color: #909399; font-size: 12px; }
.hist-snippet {
  margin: 8px 0 0;
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 12px;
  max-height: 160px;
  overflow: auto;
}
.mono { font-family: Consolas, Monaco, monospace; word-break: break-all; }
h4 { margin: 16px 0 10px; font-size: 14px; color: #303133; }
h4:first-child { margin-top: 8px; }
</style>
