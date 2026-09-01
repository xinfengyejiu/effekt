<template>
  <div class="page-wrap">
    <page-section title="Bug 统计">
      <el-form :inline="true" size="small" class="filter-bar" @submit.native.prevent>
        <el-form-item label="产品">
          <el-select
            v-model="query.productId"
            filterable
            clearable
            placeholder="请选择产品"
            style="width: 220px;"
            @change="onProductChange"
            @focus="loadProductOptions">
            <el-option v-for="p in productOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select
            v-model="query.projectId"
            filterable
            clearable
            placeholder="请选择项目"
            style="width: 220px;"
            :disabled="!query.productId"
            @change="onProjectChange">
            <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
        </el-form-item>
      </el-form>

      <div v-loading="loading" class="stats-body">
        <el-row :gutter="16" class="stat-row">
          <el-col v-for="card in summaryCardsRow1" :key="card.key" :span="6">
            <div class="stat-card" :class="card.tone">
              <div class="stat-label">{{ card.label }}</div>
              <div class="stat-value">{{ card.value }}</div>
            </div>
          </el-col>
        </el-row>
        <el-row :gutter="16" class="stat-row">
          <el-col v-for="card in summaryCardsRow2" :key="card.key" :span="8">
            <div class="stat-card" :class="card.tone">
              <div class="stat-label">{{ card.label }}</div>
              <div class="stat-value">{{ card.value }}</div>
            </div>
          </el-col>
        </el-row>

        <div class="report-section">
          <el-row :gutter="16">
            <el-col :span="5" class="report-sidebar">
              <div class="sidebar-title">请选择报表类型</div>
              <el-checkbox-group v-model="selectedReportKeys" class="report-check-list">
                <div v-for="opt in reportTypeDefs" :key="opt.key" class="report-check-row">
                  <el-checkbox :label="opt.key">{{ opt.label }}</el-checkbox>
                </div>
              </el-checkbox-group>
              <div class="sidebar-actions">
                <el-button type="text" size="small" @click="selectAllReportTypes">全选</el-button>
                <el-button type="text" size="small" @click="clearReportTypes">清空</el-button>
              </div>
              <el-button type="primary" size="small" class="btn-generate" @click="applyReport">生成报表</el-button>
            </el-col>
            <el-col :span="19" class="report-main">
              <p class="report-hint">
                报表数据来自当前「产品 / 项目」下接口返回的统计；与 Bug 列表使用相同筛选维度。未返回的维度将显示「暂无数据」。
              </p>
              <el-radio-group v-model="chartType" size="small" class="chart-type-bar" @change="onChartTypeChange">
                <el-radio-button label="default">默认</el-radio-button>
                <el-radio-button label="pie">饼图</el-radio-button>
                <el-radio-button label="bar">柱状图</el-radio-button>
                <el-radio-button label="line">折线图</el-radio-button>
              </el-radio-group>

              <template v-if="appliedReportKeys.length">
                <el-tabs v-model="activeTabKey" class="report-tabs" @tab-click="onReportTabClick">
                  <el-tab-pane
                    v-for="key in appliedReportKeys"
                    :key="'tab-' + key"
                    :name="key"
                    :label="reportLabel(key)">
                  </el-tab-pane>
                </el-tabs>
                <div v-if="activeTabKey" class="report-pane-title">{{ reportLabel(activeTabKey) }}</div>
                <el-row :gutter="12" class="report-pane-body">
                  <template v-if="chartType === 'default'">
                    <el-col :span="24">
                      <p class="default-mode-tip">以下为明细数据；切换到饼图 / 柱状图 / 折线图可同时查看图表与表格。</p>
                      <el-table :data="activeDetailRows" border size="small" class="detail-table" max-height="420">
                        <el-table-column prop="name" label="条目" min-width="120" show-overflow-tooltip />
                        <el-table-column prop="value" label="值" width="90" align="right" />
                        <el-table-column prop="percent" label="百分比" width="100" align="right" />
                      </el-table>
                    </el-col>
                  </template>
                  <template v-else>
                    <el-col :span="14">
                      <div ref="chartRef" class="chart-box"></div>
                    </el-col>
                    <el-col :span="10">
                      <el-table :data="activeDetailRows" border size="small" class="detail-table" max-height="380">
                        <el-table-column prop="name" label="条目" min-width="120" show-overflow-tooltip />
                        <el-table-column prop="value" label="值" width="90" align="right" />
                        <el-table-column prop="percent" label="百分比" width="100" align="right" />
                      </el-table>
                    </el-col>
                  </template>
                </el-row>
              </template>
              <div v-else class="report-empty">请勾选报表类型后点击「生成报表」</div>
            </el-col>
          </el-row>
        </div>
      </div>
    </page-section>
  </div>
</template>

<script>
import echarts from 'echarts'
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getBugStats } from '@/api/bugApi'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  readLastProductProjectCache,
  saveLastProductProjectCache,
  pickIdFromOptions
} from '@/utils/lastProductProjectCache'
import { STATUS_MAP } from '@/utils/bugMaps'

const SOLUTION_LABEL_MAP = {
  by_design: '设计如此',
  duplicate_bug: '重复Bug',
  external_reason: '外部原因',
  solution_resolved: '已解决',
  cannot_reproduce: '无法重现',
  deferred: '延期处理',
  wont_fix: '不予解决'
}

/** 不含：按严重程度、按优先级、按类型 */
const REPORT_TYPE_DEFS = [
  { key: 'iteration', label: '迭代Bug数量' },
  { key: 'version', label: '版本Bug数量' },
  { key: 'module', label: '模块Bug数量' },
  { key: 'daily_new', label: '每天新增Bug数' },
  { key: 'daily_resolved', label: '每天解决Bug数' },
  { key: 'daily_closed', label: '每天关闭的Bug数' },
  { key: 'by_reporter', label: '每人提交的Bug数' },
  { key: 'by_resolver', label: '每人解决的Bug数' },
  { key: 'by_closer', label: '每人关闭的Bug数' },
  { key: 'solution', label: '按Bug解决方案统计' },
  { key: 'status', label: '按Bug状态统计' },
  { key: 'activation', label: '按Bug激活次数统计' },
  { key: 'by_assignee', label: '按指派给统计' }
]

function firstNonEmptyObject(stats, paths) {
  const s = stats || {}
  for (let i = 0; i < paths.length; i++) {
    const p = paths[i]
    const v = p.split('.').reduce((o, k) => (o != null && o[k] !== undefined ? o[k] : undefined), s)
    if (v && typeof v === 'object' && !Array.isArray(v) && Object.keys(v).length) return v
  }
  return null
}

function firstDefined(stats, paths) {
  const s = stats || {}
  for (let i = 0; i < paths.length; i++) {
    const p = paths[i]
    const v = p.split('.').reduce((o, k) => (o != null && o[k] !== undefined ? o[k] : undefined), s)
    if (v !== undefined && v !== null) return v
  }
  return null
}

function normalizeTimeSeries(raw) {
  if (!raw) return { categories: [], values: [] }
  if (Array.isArray(raw)) {
    const categories = raw.map(
      item => String(item.date || item.day || item.label || item.name || item.stat_date || '-')
    )
    const values = raw.map(item => {
      const v =
        item.count !== undefined && item.count !== null && item.count !== ''
          ? item.count
          : item.value !== undefined && item.value !== null && item.value !== ''
            ? item.value
            : item.total !== undefined && item.total !== null && item.total !== ''
              ? item.total
              : item.num
      return Number(v) || 0
    })
    return { categories, values }
  }
  if (typeof raw === 'object') {
    const keys = Object.keys(raw).sort()
    return {
      categories: keys,
      values: keys.map(k => Number(raw[k]) || 0)
    }
  }
  return { categories: [], values: [] }
}

function mapObjectRows(obj, labelResolver) {
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return { categories: [], values: [] }
  const keys = Object.keys(obj)
  const categories = keys.map(k => (labelResolver ? labelResolver(k, obj[k]) : String(k)))
  const values = keys.map(k => Number(obj[k]) || 0)
  return { categories, values }
}

export default {
  name: 'BugStats',
  components: { PageSection },
  data() {
    return {
      loading: false,
      productOptions: [],
      projectOptions: [],
      query: {
        productId: '',
        projectId: ''
      },
      stats: {},
      reportTypeDefs: REPORT_TYPE_DEFS,
      selectedReportKeys: ['by_resolver'],
      appliedReportKeys: [],
      activeTabKey: '',
      chartType: 'line',
      chartInstance: null,
      _resizeHandler: null
    }
  },
  computed: {
    summaryCardsRow1() {
      const s = this.stats || {}
      const pick = (a, b, def) => {
        const v = a !== undefined && a !== null ? a : b
        return v !== undefined && v !== null ? v : def
      }
      return [
        { key: 'total', label: '总数', value: pick(s.total, s.total_count, 0), tone: 'tone-default' },
        { key: 'new', label: '新建', value: pick(s.new, s.new_count, 0), tone: 'tone-info' },
        { key: 'pending', label: '待处理', value: pick(s.pending, s.pending_count, 0), tone: 'tone-warn' },
        { key: 'in_progress', label: '进行中', value: pick(s.in_progress, s.inProgress, 0), tone: 'tone-primary' }
      ]
    },
    summaryCardsRow2() {
      const s = this.stats || {}
      const pick = (a, b, def) => {
        const v = a !== undefined && a !== null ? a : b
        return v !== undefined && v !== null ? v : def
      }
      return [
        { key: 'resolved', label: '已解决', value: pick(s.resolved, s.resolved_count, 0), tone: 'tone-success' },
        { key: 'closed', label: '已关闭', value: pick(s.closed, s.closed_count, 0), tone: 'tone-muted' },
        { key: 'rejected', label: '已拒绝', value: pick(s.rejected, s.rejected_count, 0), tone: 'tone-danger' }
      ]
    },
    activeDetailRows() {
      const { categories, values } = this.getSeriesForKey(this.activeTabKey)
      return this.buildDetailRows(categories, values)
    }
  },
  watch: {
    stats() {
      if (this.appliedReportKeys.length) {
        this.$nextTick(() => this.renderChart())
      }
    }
  },
  beforeDestroy() {
    this.disposeChart()
    if (this._resizeHandler) {
      window.removeEventListener('resize', this._resizeHandler)
    }
  },
  methods: {
    reportLabel(key) {
      const row = this.reportTypeDefs.find(r => r.key === key)
      return row ? row.label : key
    },
    selectAllReportTypes() {
      this.selectedReportKeys = this.reportTypeDefs.map(r => r.key)
    },
    clearReportTypes() {
      this.selectedReportKeys = []
    },
    applyReport() {
      if (!this.selectedReportKeys.length) {
        this.$message.warning('请至少选择一种报表类型')
        return
      }
      this.appliedReportKeys = [...this.selectedReportKeys]
      this.activeTabKey = this.appliedReportKeys[0]
      this.$nextTick(() => this.renderChart())
    },
    onChartTypeChange() {
      this.$nextTick(() => this.renderChart())
    },
    onReportTabClick() {
      this.$nextTick(() => this.renderChart())
    },
    buildDetailRows(categories, values) {
      const total = (values || []).reduce((a, b) => a + (Number(b) || 0), 0)
      const t = total > 0 ? total : 1
      return (categories || []).map((name, i) => {
        const v = Number(values[i]) || 0
        return {
          name: name || '-',
          value: v,
          percent: `${((v / t) * 100).toFixed(2)}%`
        }
      })
    },
    getSeriesForKey(key) {
      const s = this.stats || {}
      switch (key) {
        case 'iteration': {
          const o = firstNonEmptyObject(s, [
            'by_iteration',
            'iteration_bugs',
            'iteration_stats',
            'iterationStats',
            'bugs_by_iteration'
          ])
          return mapObjectRows(o, k => k)
        }
        case 'version': {
          const o = firstNonEmptyObject(s, ['by_version', 'version_bugs', 'version_stats', 'bugs_by_version'])
          return mapObjectRows(o, k => k)
        }
        case 'module': {
          const o = firstNonEmptyObject(s, ['by_module', 'module_bugs', 'module_stats', 'bugs_by_module'])
          return mapObjectRows(o, k => k)
        }
        case 'daily_new': {
          const raw = firstDefined(s, ['daily_new', 'dailyNew', 'new_by_day', 'bugs_new_daily', 'newDaily'])
          return normalizeTimeSeries(raw)
        }
        case 'daily_resolved': {
          const raw = firstDefined(s, ['daily_resolved', 'dailyResolved', 'resolved_by_day', 'bugs_resolved_daily'])
          return normalizeTimeSeries(raw)
        }
        case 'daily_closed': {
          const raw = firstDefined(s, ['daily_closed', 'dailyClosed', 'closed_by_day', 'bugs_closed_daily'])
          return normalizeTimeSeries(raw)
        }
        case 'by_reporter': {
          const o = firstNonEmptyObject(s, [
            'by_reporter',
            'byReporter',
            'reporter_stats',
            'submit_by_user',
            'bugs_by_creator'
          ])
          return mapObjectRows(o, k => k)
        }
        case 'by_resolver': {
          const o = firstNonEmptyObject(s, [
            'by_resolver',
            'byResolver',
            'resolved_by_user',
            'resolver_stats',
            'bugs_by_resolver'
          ])
          return mapObjectRows(o, k => k)
        }
        case 'by_closer': {
          const o = firstNonEmptyObject(s, ['by_closer', 'byCloser', 'closed_by_user', 'closer_stats'])
          return mapObjectRows(o, k => k)
        }
        case 'solution': {
          const o = firstNonEmptyObject(s, ['by_solution', 'bySolution', 'solution_stats'])
          return mapObjectRows(o, k => SOLUTION_LABEL_MAP[k] || k)
        }
        case 'status': {
          const o = firstNonEmptyObject(s, ['by_status', 'byStatus', 'status_stats'])
          return mapObjectRows(o, k => STATUS_MAP[Number(k)] != null ? STATUS_MAP[Number(k)] : STATUS_MAP[k] || k)
        }
        case 'activation': {
          const o = firstNonEmptyObject(s, ['by_activation', 'byActivation', 'activation_stats'])
          return mapObjectRows(o, k => k)
        }
        case 'by_assignee': {
          const o = firstNonEmptyObject(s, ['by_assignee', 'byAssignee', 'assignee_stats', 'bugs_by_assignee'])
          return mapObjectRows(o, k => k)
        }
        default:
          return { categories: [], values: [] }
      }
    },
    disposeChart() {
      if (this.chartInstance) {
        try {
          this.chartInstance.dispose()
        } catch (e) {}
        this.chartInstance = null
      }
    },
    renderChart() {
      this.disposeChart()
      if (!this.appliedReportKeys.length || this.chartType === 'default') return
      const el = this.$refs.chartRef
      if (!el) return
      const { categories, values } = this.getSeriesForKey(this.activeTabKey)
      if (!categories.length) {
        this.chartInstance = echarts.init(el)
        this.chartInstance.setOption({
          title: {
            text: '暂无数据',
            left: 'center',
            top: 'middle',
            textStyle: { color: '#909399', fontSize: 14 }
          }
        })
        this.bindResize()
        return
      }
      this.chartInstance = echarts.init(el)
      const isLine = this.chartType === 'line'
      const baseSeries = {
        name: this.reportLabel(this.activeTabKey),
        data: values,
        type: this.chartType === 'pie' ? 'pie' : this.chartType === 'bar' ? 'bar' : 'line',
        smooth: isLine,
        areaStyle: isLine ? { opacity: 0.12 } : undefined
      }
      let option
      if (this.chartType === 'pie') {
        option = {
          color: ['#1e40af', '#67C23A', '#E6A23C', '#F56C6C', '#909399', '#9b59b6', '#3498db'],
          tooltip: { trigger: 'item' },
          legend: { bottom: 0, type: 'scroll' },
          series: [
            {
              type: 'pie',
              radius: ['36%', '62%'],
              center: ['50%', '46%'],
              data: categories.map((name, i) => ({ name, value: values[i] })),
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0,0,0,0.15)'
                }
              }
            }
          ]
        }
      } else {
        option = {
          color: ['#1e40af'],
          tooltip: { trigger: 'axis' },
          grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
          xAxis: {
            type: 'category',
            data: categories,
            axisLabel: { rotate: categories.some(c => String(c).length > 6) ? 35 : 0, interval: 0 }
          },
          yAxis: { type: 'value', minInterval: 1 },
          series: [Object.assign({}, baseSeries, this.chartType === 'bar' ? { barMaxWidth: 48 } : {})]
        }
      }
      this.chartInstance.setOption(option)
      this.bindResize()
    },
    bindResize() {
      if (!this._resizeHandler) {
        this._resizeHandler = () => {
          if (this.chartInstance) this.chartInstance.resize()
        }
        window.addEventListener('resize', this._resizeHandler)
      } else if (this.chartInstance) {
        this.chartInstance.resize()
      }
    },
    loadProductOptions() {
      if (this.productOptions.length) return Promise.resolve()
      return getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        const data = (res && res.data) || res || {}
        this.productOptions = data.items || data.list || data.data || []
      }).catch(() => {
        this.productOptions = []
      })
    },
    loadProjects(productId) {
      if (!productId) {
        this.projectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        const data = (res && res.data) || res || {}
        this.projectOptions = data.items || data.list || data.data || []
      }).catch(() => {
        this.projectOptions = []
      })
    },
    restoreSharedProductProjectCache() {
      const cached = readLastProductProjectCache()
      if (!cached) return Promise.resolve()
      const { productId: pid, projectId: projId } = cached
      if (pid === '' || pid === undefined || pid === null || projId === '' || projId === undefined || projId === null) {
        return Promise.resolve()
      }
      const hasProduct = (this.productOptions || []).some(p => String(p.id) === String(pid))
      if (!hasProduct) return Promise.resolve()
      this.query.productId = pickIdFromOptions(this.productOptions, pid)
      return this.loadProjects(this.query.productId).then(() => {
        const hasProject = (this.projectOptions || []).some(p => String(p.id) === String(projId))
        if (!hasProject) return
        this.query.projectId = pickIdFromOptions(this.projectOptions, projId)
      })
    },
    onProductChange(val) {
      this.query.projectId = ''
      this.projectOptions = []
      this.loadProjects(val)
    },
    onProjectChange(val) {
      if (val) {
        saveLastProductProjectCache(this.query.productId, val)
      }
    },
    handleSearch() {
      saveLastProductProjectCache(this.query.productId, this.query.projectId)
      this.fetchStats()
    },
    fetchStats() {
      this.loading = true
      const params = {}
      if (this.query.productId !== '' && this.query.productId != null) params.productId = this.query.productId
      if (this.query.projectId !== '' && this.query.projectId != null) params.projectId = this.query.projectId
      getBugStats(params)
        .then(res => {
          this.stats = (res && res.data) || res || {}
        })
        .catch(() => {
          this.stats = {}
        })
        .finally(() => {
          this.loading = false
        })
    }
  },
  created() {
    this.loadProductOptions()
      .then(() => this.restoreSharedProductProjectCache())
      .finally(() => this.fetchStats())
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}
.filter-bar {
  margin-bottom: 8px;
}
.stats-body {
  min-height: 120px;
}
.stat-row {
  margin-bottom: 8px;
}
.stat-card {
  border-radius: 10px;
  padding: 16px 18px;
  margin-bottom: 16px;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.stat-label {
  font-size: 13px;
  color: #909399;
}
.stat-value {
  margin-top: 8px;
  font-size: 26px;
  font-weight: 600;
  color: #303133;
}
.tone-primary .stat-value {
  color: #1e40af;
}
.tone-success .stat-value {
  color: #67c23a;
}
.tone-warn .stat-value {
  color: #e6a23c;
}
.tone-danger .stat-value {
  color: #f56c6c;
}
.tone-info .stat-value {
  color: #909399;
}
.tone-muted .stat-value {
  color: #606266;
}

.report-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}
.report-sidebar {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px 12px;
  background: #fafbfc;
}
.sidebar-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  margin-bottom: 10px;
}
.report-check-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 420px;
  overflow-y: auto;
}
.report-check-row {
  line-height: 1.5;
}
.sidebar-actions {
  margin-top: 10px;
  margin-bottom: 8px;
}
.btn-generate {
  width: 100%;
}
.report-main {
  min-height: 420px;
}
.report-hint {
  font-size: 12px;
  color: #909399;
  margin: 0 0 10px;
  line-height: 1.5;
}
.chart-type-bar {
  margin-bottom: 12px;
}
.report-tabs {
  margin-top: 4px;
}
.report-pane-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}
.default-mode-tip {
  font-size: 12px;
  color: #909399;
  margin: 0 0 8px;
}
.report-pane-body {
  align-items: stretch;
}
.chart-box {
  height: 380px;
  width: 100%;
}
.chart-placeholder {
  height: 380px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 13px;
  padding: 16px;
  text-align: center;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  background: #fafafa;
}
.detail-table {
  width: 100%;
}
.report-empty {
  padding: 48px 16px;
  text-align: center;
  color: #909399;
  font-size: 14px;
  border: 1px dashed #e4e7ed;
  border-radius: 8px;
}
</style>
