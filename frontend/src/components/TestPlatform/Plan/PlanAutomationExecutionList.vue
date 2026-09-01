<template>
  <div class="page-wrap">
    <page-section title="自动化执行结果">
      <div class="filter-toolbar">
        <el-form :inline="true" size="small" class="filter-toolbar-form" @submit.native.prevent>
          <el-form-item label="产品">
            <el-input :value="productName" disabled style="width: 200px;" />
          </el-form-item>
          <el-form-item label="项目">
            <el-input :value="projectName" disabled style="width: 200px;" />
          </el-form-item>
          <el-form-item label="计划">
            <el-input :value="planNameDisplay" disabled style="width: 220px;" />
          </el-form-item>
        </el-form>
        <div class="filter-toolbar-actions">
          <el-button size="small" @click="goBackToRun">返回执行</el-button>
          <el-button size="small" @click="goPlanList">返回计划</el-button>
        </div>
      </div>

      <el-table v-loading="loading" :data="rows" border style="margin-top: 12px;">
        <el-table-column label="执行单号" min-width="180" show-overflow-tooltip>
          <template slot-scope="scope">{{ scope.row.execution_no || scope.row.executionNo || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template slot-scope="scope">
            <el-tag size="mini" :type="mainStatusTag(scope.row.status)">{{ mainStatusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="环境" width="100">
          <template slot-scope="scope">{{ scope.row.env_code || scope.row.envCode || '-' }}</template>
        </el-table-column>
        <el-table-column label="总数" width="72">
          <template slot-scope="scope">{{ scope.row.total_count != null ? scope.row.total_count : scope.row.totalCount }}</template>
        </el-table-column>
        <el-table-column label="通过" width="72">
          <template slot-scope="scope">{{ scope.row.passed_count != null ? scope.row.passed_count : scope.row.passedCount }}</template>
        </el-table-column>
        <el-table-column label="失败" width="72">
          <template slot-scope="scope">{{ scope.row.failed_count != null ? scope.row.failed_count : scope.row.failedCount }}</template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template slot-scope="scope">{{ scope.row.created_time || scope.row.createdTime || '-' }}</template>
        </el-table-column>
        <el-table-column label="执行详情" width="100" align="center">
          <template slot-scope="scope">
            <el-button type="text" size="small" @click="goToExecutionDetail(scope.row)">查看详情</el-button>
          </template>
        </el-table-column>
        <el-table-column label="报告" width="100" align="center">
          <template slot-scope="scope">
            <el-link
              v-if="getReportUrl(scope.row)"
              :href="getReportUrl(scope.row)"
              target="_blank"
              type="primary">
              打开
            </el-link>
            <span v-else-if="isReportLoading(scope.row)" class="report-loading">
              <i class="el-icon-loading"></i>
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="pageNo"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handlePageChange" />
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getAutomationExecutionList, postAutomationExecutionPoll } from '@/api/automationApi'

const MAIN_STATUS_LABELS = {
  0: '待触发',
  1: '触发中',
  2: '排队中',
  3: '执行中',
  4: '成功',
  5: '失败',
  6: '已取消',
  7: '触发失败',
  8: '回调异常'
}

/** 终态：一般不再有报告 URL 更新 */
const TERMINAL = new Set([4, 5, 6, 7, 8])
/** 无报告也可停止加载 */
const TERMINAL_NO_REPORT_EXPECTED = new Set([6, 7, 8])

const POLL_MS = 5000

export default {
  name: 'PlanAutomationExecutionList',
  components: { PageSection },
  data() {
    return {
      projectId: this.$route.query.projectId || '',
      planId: this.$route.query.planId || '',
      loading: false,
      rows: [],
      pageNo: 1,
      pageSize: 20,
      total: 0,
      pollTimer: null,
      /** executionId -> 本轮 poll 请求中 */
      pollInflight: {}
    }
  },
  computed: {
    productName() {
      return this.$route.query.productName || ''
    },
    projectName() {
      return this.$route.query.projectName || ''
    },
    planNameDisplay() {
      return this.$route.query.planName || ''
    }
  },
  watch: {
    '$route.query': {
      handler() {
        this.projectId = this.$route.query.projectId || ''
        this.planId = this.$route.query.planId || ''
        this.pageNo = 1
        this.stopPoll()
        this.fetchList()
      },
      deep: true
    }
  },
  created() {
    this.fetchList()
  },
  beforeDestroy() {
    this.stopPoll()
  },
  methods: {
    getReportUrl(row) {
      if (!row) return ''
      const u = row.report_url || row.reportUrl
      return u && String(u).trim() ? String(u).trim() : ''
    },
    rowExecutionId(row) {
      if (!row) return null
      const id = row.id != null ? row.id : row.execution_id || row.executionId
      return id != null && id !== '' ? Number(id) : null
    },
    rowStatusNum(row) {
      const s = row && row.status
      const n = Number(s)
      return Number.isFinite(n) ? n : -1
    },
    /** 仍可能通过 poll 拿到报告地址 */
    needsReportPoll(row) {
      if (this.getReportUrl(row)) return false
      const st = this.rowStatusNum(row)
      if (TERMINAL_NO_REPORT_EXPECTED.has(st)) return false
      return true
    },
    /** 轮询未停且该行仍可能出报告时，报告列持续显示加载（含两次 poll 间隔） */
    isReportLoading(row) {
      if (this.getReportUrl(row)) return false
      if (!this.needsReportPoll(row)) return false
      return this.pollTimer != null || !!this.pollInflight[this.rowExecutionId(row)]
    },
    mainStatusLabel(s) {
      return MAIN_STATUS_LABELS[s] != null ? MAIN_STATUS_LABELS[s] : s == null ? '-' : String(s)
    },
    mainStatusTag(s) {
      const map = { 0: 'info', 1: 'warning', 2: 'warning', 3: 'primary', 4: 'success', 5: 'danger', 6: 'info', 7: 'danger', 8: 'danger' }
      return map[s] || 'info'
    },
    mergePollIntoRow(executionId, d) {
      if (!d || typeof d !== 'object') return
      const idx = this.rows.findIndex(r => this.rowExecutionId(r) === executionId)
      if (idx < 0) return
      const row = this.rows[idx]
      const next = Object.assign({}, row)
      const pick = (snake, camel) => {
        if (d[snake] !== undefined && d[snake] !== null && d[snake] !== '') next[snake] = d[snake]
        if (d[camel] !== undefined && d[camel] !== null && d[camel] !== '') next[camel] = d[camel]
      }
      if (d.status !== undefined && d.status !== null) next.status = d.status
      pick('report_url', 'reportUrl')
      pick('console_url', 'consoleUrl')
      pick('jenkins_build_url', 'jenkinsBuildUrl')
      pick('jenkins_build_number', 'jenkinsBuildNumber')
      pick('end_time', 'endTime')
      if (d.duration_seconds != null || d.durationSeconds != null) {
        next.duration_seconds = d.duration_seconds != null ? d.duration_seconds : d.durationSeconds
      }
      this.$set(this.rows, idx, next)
    },
    pollOne(executionId) {
      if (executionId == null || Number.isNaN(executionId)) return Promise.resolve()
      this.$set(this.pollInflight, executionId, true)
      return postAutomationExecutionPoll({ executionId })
        .then(res => {
          if (!res || res.code !== 20000) return
          const d = res.data
          if (!d || typeof d !== 'object') return
          const rid = d.id != null ? Number(d.id) : executionId
          this.mergePollIntoRow(rid, d)
        })
        .catch(() => {})
        .finally(() => {
          this.$delete(this.pollInflight, executionId)
        })
    },
    runPollTick() {
      const targets = this.rows
        .map(r => this.rowExecutionId(r))
        .filter(id => id != null && !Number.isNaN(id))
        .filter(id => {
          const row = this.rows.find(x => this.rowExecutionId(x) === id)
          return row && this.needsReportPoll(row)
        })
      if (!targets.length) {
        this.stopPoll()
        return
      }
      targets.forEach(id => {
        if (this.pollInflight[id]) return
        this.pollOne(id)
      })
    },
    startPoll() {
      this.stopPoll()
      this.runPollTick()
      this.pollTimer = window.setInterval(() => this.runPollTick(), POLL_MS)
    },
    stopPoll() {
      if (this.pollTimer != null) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
    },
    fetchList() {
      const pid = this.planId
      const projId = this.projectId
      if (!pid || !projId) {
        this.rows = []
        this.total = 0
        this.stopPoll()
        return
      }
      this.stopPoll()
      this.loading = true
      getAutomationExecutionList({
        planId: Number(pid),
        projectId: Number(projId),
        pageNo: this.pageNo,
        pageSize: this.pageSize
      })
        .then(res => {
          const data = (res && res.data) || res || {}
          const list = data.list || data.items || []
          this.rows = Array.isArray(list) ? list.map(x => Object.assign({}, x)) : []
          this.total = Number(data.total != null ? data.total : this.rows.length)
          this.$nextTick(() => {
            const any = this.rows.some(r => this.needsReportPoll(r))
            if (any) this.startPoll()
          })
        })
        .catch(() => {
          this.rows = []
          this.total = 0
        })
        .finally(() => {
          this.loading = false
        })
    },
    handleSizeChange(size) {
      this.pageSize = size
      this.pageNo = 1
      this.fetchList()
    },
    handlePageChange(page) {
      this.pageNo = page
      this.fetchList()
    },
    automationRunQuery() {
      const q = this.$route.query || {}
      return {
        productId: q.productId || undefined,
        productName: q.productName || '',
        projectId: this.projectId || undefined,
        projectName: q.projectName || '',
        planId: this.planId || undefined,
        planName: q.planName || '',
        environmentId: q.environmentId || undefined,
        jenkinsUrl: q.jenkinsUrl || undefined
      }
    },
    goBackToRun() {
      this.stopPoll()
      this.$router.push({
        path: '/test-platform/plan/automation',
        query: this.automationRunQuery()
      })
    },
    /** 进入与执行后相同的计划自动化执行详情页（主单 + 执行明细） */
    goToExecutionDetail(row) {
      const id = this.rowExecutionId(row)
      if (id == null || Number.isNaN(id)) {
        this.$message.warning('缺少执行单 ID')
        return
      }
      this.stopPoll()
      this.$router.push({
        path: '/test-platform/plan/automation',
        query: Object.assign({}, this.automationRunQuery(), { executionId: id })
      })
    },
    goPlanList() {
      this.stopPoll()
      this.$router.push({
        path: '/test-platform/plan',
        query: {
          productId: this.$route.query.productId || undefined,
          projectId: this.projectId || undefined
        }
      })
    }
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}

.filter-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.filter-toolbar-form {
  flex: 1;
  min-width: 0;
}

.filter-toolbar-actions {
  flex-shrink: 0;
  padding-top: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pager {
  margin-top: 16px;
  text-align: right;
}

.report-loading {
  color: #1e40af;
  font-size: 16px;
}
</style>
