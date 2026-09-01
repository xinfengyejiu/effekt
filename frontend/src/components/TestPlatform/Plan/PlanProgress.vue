<template>
  <div class="page-wrap">
    <page-section title="计划进度">
      <el-form :inline="true" size="small" @submit.native.prevent>
        <el-form-item label="产品名称">
          <el-input :value="productName" disabled style="width: 220px;"></el-input>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-input :value="projectName" disabled style="width: 220px;"></el-input>
        </el-form-item>
        <el-form-item label="计划名称">
          <el-input :value="planNameDisplay" disabled style="width: 240px;"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchProgressBoard">刷新看板</el-button>
        </el-form-item>
        <el-form-item>
          <el-button @click="goBack">返回</el-button>
        </el-form-item>
      </el-form>

      <el-row :gutter="16" class="metric-row">
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-label">总用例数</div>
            <div class="metric-value">{{ summary.total }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-label">待执行</div>
            <div class="metric-value warning">{{ summary.pending }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-label">已执行</div>
            <div class="metric-value success">{{ summary.executed }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card">
            <div class="metric-label">完成率</div>
            <div class="metric-value primary">{{ summary.progressPercent }}%</div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="8">
          <div class="board-card">
            <div class="board-title">执行完成度</div>
            <div class="dashboard-wrap">
              <el-progress
                type="dashboard"
                :percentage="summary.progressPercent"
                :color="progressColor">
              </el-progress>
              <div class="dashboard-desc">已执行 {{ summary.executed }} / {{ summary.total }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="16">
          <div class="board-card">
            <div class="board-title">状态分布</div>
            <div v-for="item in statusBarData" :key="item.key" class="status-bar-row">
              <div class="status-label">
                <el-tag size="mini" :type="item.tag">{{ item.label }}</el-tag>
              </div>
              <div class="status-bar-track">
                <div class="status-bar-fill" :style="{ width: item.percent + '%', background: item.color }"></div>
              </div>
              <div class="status-value">{{ item.count }}（{{ item.percent }}%）</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <div class="board-card" style="margin-top: 16px;">
        <div class="board-title">用例状态看板明细</div>
        <el-table v-loading="loading" :data="displayRows" border style="margin-top: 10px;">
          <el-table-column label="模块" min-width="160">
            <template slot-scope="scope">{{ formatModuleName(scope.row) }}</template>
          </el-table-column>
          <el-table-column prop="caseKey" label="用例编号" min-width="120"></el-table-column>
          <el-table-column prop="caseTitle" label="用例名称" min-width="220"></el-table-column>
          <el-table-column label="自动化执行 Jenkins URL" min-width="180" show-overflow-tooltip>
            <template slot-scope="scope">
              <el-link v-if="scope.row.jenkinsUrl" :href="scope.row.jenkinsUrl" target="_blank" type="primary">打开</el-link>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template slot-scope="scope">
              <el-tag size="mini" :type="statusTagType(scope.row.statusCode)">{{ statusLabel(scope.row.statusCode) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="actualResult" label="执行结果" min-width="180"></el-table-column>
        </el-table>
        <el-pagination
          style="margin-top: 12px; text-align: right;"
          background
          layout="total, sizes, prev, pager, next, jumper"
          :current-page="pageNo"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          :total="caseListTotal"
          @size-change="handleCaseListSizeChange"
          @current-change="handleCaseListPageChange">
        </el-pagination>
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getPlanCaseList, getPlanProgress } from '@/api/planApi'

export default {
  name: 'PlanProgress',
  components: { PageSection },
  data() {
    return {
      loading: false,
      projectId: this.$route.query.projectId || '',
      planId: this.$route.query.planId || '',
      progress: {},
      planCaseTableData: [],
      caseListTotal: 0,
      pageNo: 1,
      pageSize: 10
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
    },
    summary() {
      const statusCount = this.statusCountMap
      const progressTotal = this.toNumber(this.progress.total_cases || this.progress.total || 0)
      const total = progressTotal || this.caseListTotal || 0
      const pending = this.toNumber(statusCount[0])
      const executed = Math.max(0, total - pending)
      const progressPercent = total > 0 ? Math.round((executed / total) * 100) : 0
      return { total, pending, executed, progressPercent }
    },
    /** 顶部看板统计以 getPlanProgress 为准，不能按当前页用例行数聚合 */
    statusCountMap() {
      const map = {}
      const fromProgress = this.progress.status_count || this.progress.statusCount || {}
      if (fromProgress && typeof fromProgress === 'object' && Object.keys(fromProgress).length > 0) {
        Object.keys(fromProgress).forEach(key => {
          map[this.toNumber(key)] = this.toNumber(fromProgress[key])
        })
        return map
      }
      this.planCaseTableData.forEach(item => {
        const key = this.toNumber(item.statusCode)
        map[key] = (map[key] || 0) + 1
      })
      return map
    },
    statusBarData() {
      const total = this.summary.total || 1
      const statuses = [
        { key: 0, label: '待执行', tag: 'info', color: '#909399' },
        { key: 1, label: '通过', tag: 'success', color: '#67c23a' },
        { key: 2, label: '失败', tag: 'danger', color: '#f56c6c' },
        { key: 3, label: '阻塞', tag: 'warning', color: '#e6a23c' }
      ]
      return statuses.map(item => {
        const count = this.toNumber(this.statusCountMap[item.key] || 0)
        const percent = Math.round((count / total) * 100)
        return Object.assign({}, item, { count, percent })
      })
    },
    progressColor() {
      const value = this.summary.progressPercent
      if (value >= 80) return '#67c23a'
      if (value >= 50) return '#1e40af'
      if (value >= 30) return '#e6a23c'
      return '#f56c6c'
    },
    displayRows() {
      return this.planCaseTableData
    }
  },
  methods: {
    handleCaseListSizeChange(size) {
      this.pageSize = size
      this.pageNo = 1
      this.fetchProgressBoard()
    },
    handleCaseListPageChange(page) {
      this.pageNo = page
      this.fetchProgressBoard()
    },
    fetchProgressBoard() {
      if (!this.planId || !this.projectId) {
        this.progress = {}
        this.planCaseTableData = []
        this.caseListTotal = 0
        return
      }
      this.loading = true
      Promise.all([
        getPlanProgress(this.projectId, this.planId),
        getPlanCaseList(this.projectId, this.planId, { pageNo: this.pageNo, pageSize: this.pageSize })
      ])
        .then(([progressRes, listRes]) => {
          this.progress = (progressRes && progressRes.data) || progressRes || {}
          const listData = (listRes && listRes.data) || listRes || {}
          const list = listData.list || listData.items || listData.data || []
          this.caseListTotal = Number(
            listData.total != null ? listData.total : Array.isArray(list) ? list.length : 0
          )
          this.planCaseTableData = (Array.isArray(list) ? list : []).map(item => ({
            id: item.id,
            caseId: item.case_id || item.caseId,
            moduleName: item.module_name || item.moduleName || '',
            moduleId: item.module_id || item.moduleId || '',
            caseKey: item.case_key || item.caseKey || '',
            caseTitle: item.case_title || item.caseTitle || item.title || '',
            title: item.title || item.case_title || item.caseTitle || '',
            statusCode: this.toNumber(item.status),
            actualResult: item.actual_result || item.actualResult || '',
            jenkinsUrl: item.jenkins_url || item.jenkinsUrl || ''
          }))
        })
        .catch(() => {
          this.progress = {}
          this.planCaseTableData = []
          this.caseListTotal = 0
        })
        .finally(() => {
          this.loading = false
        })
    },
    toNumber(value) {
      const num = Number(value)
      return Number.isFinite(num) ? num : 0
    },
    statusLabel(status) {
      const map = { 0: '待执行', 1: '通过', 2: '失败', 3: '阻塞' }
      return map[this.toNumber(status)] || '未知'
    },
    statusTagType(status) {
      const map = { 0: 'info', 1: 'success', 2: 'danger', 3: 'warning' }
      return map[this.toNumber(status)] || 'info'
    },
    formatModuleName(row) {
      if (!row) return '-'
      if (row.moduleName) return row.moduleName
      return '-'
    },
    goBack() {
      this.$router.push({
        path: '/test-platform/plan',
        query: {
          productId: this.$route.query.productId || undefined,
          projectId: this.projectId || undefined
        }
      })
    },
    normalizeRouteQuery() {
      if (!this.projectId && this.$route.query.project_id) {
        this.projectId = this.$route.query.project_id
      }
      if (!this.planId && this.$route.query.id) {
        this.planId = this.$route.query.id
      }
    }
  },
  created() {
    this.normalizeRouteQuery()
    this.fetchProgressBoard()
  },
  watch: {
    '$route.query.planId'(val) {
      if (val !== undefined) {
        this.planId = val
        this.fetchProgressBoard()
      }
    },
    '$route.query.projectId'(val) {
      if (val !== undefined) {
        this.projectId = val
        this.fetchProgressBoard()
      }
    }
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
  background: #f7f8fa;
}

.metric-row {
  margin-bottom: 16px;
}

.metric-card {
  background: linear-gradient(135deg, #ffffff 0%, #f7fbff 100%);
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px 16px;
  min-height: 84px;
  box-shadow: 0 4px 10px rgba(31, 45, 61, 0.06);
}

.metric-label {
  color: #909399;
  font-size: 13px;
}

.metric-value {
  margin-top: 8px;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
  line-height: 1;
}

.metric-value.success {
  color: #67c23a;
}

.metric-value.warning {
  color: #e6a23c;
}

.metric-value.primary {
  color: #1e40af;
}

.board-card {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #ebeef5;
  padding: 16px;
  box-shadow: 0 6px 14px rgba(31, 45, 61, 0.08);
}

.board-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.dashboard-wrap {
  margin-top: 10px;
  text-align: center;
}

.dashboard-desc {
  color: #606266;
  margin-top: 8px;
}

.status-bar-row {
  display: flex;
  align-items: center;
  margin-top: 14px;
}

.status-label {
  width: 72px;
}

.status-bar-track {
  flex: 1;
  height: 10px;
  border-radius: 10px;
  background: #f1f2f4;
  overflow: hidden;
}

.status-bar-fill {
  height: 100%;
  border-radius: 10px;
  transition: width 0.3s ease;
}

.status-value {
  width: 110px;
  text-align: right;
  color: #606266;
  font-size: 12px;
}
</style>
