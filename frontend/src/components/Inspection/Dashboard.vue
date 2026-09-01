<template>
  <div class="page-wrap">
    <page-section title="巡检概览">
      <el-row :gutter="20" style="margin-bottom: 20px">
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_executions_today || 0 }}</div>
              <div class="stat-label">今日执行次数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-card">
              <div class="stat-value" :style="{color: passRate >= 80 ? '#67C23A' : passRate >= 50 ? '#E6A23C' : '#F56C6C'}">{{ passRate }}%</div>
              <div class="stat-label">今日通过率</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-card">
              <div class="stat-value" style="color: #F56C6C">{{ stats.fail_count_today || 0 }}</div>
              <div class="stat-label">今日失败数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <div class="stat-card">
              <div class="stat-value" style="color: #409EFF">{{ stats.active_tasks || 0 }}</div>
              <div class="stat-label">活跃任务数</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </page-section>

    <page-section title="最近执行记录">
      <el-table :data="recentExecutions" v-loading="loading" stripe border size="small">
        <el-table-column label="任务名称" prop="task_id" width="180">
          <template slot-scope="scope">
            任务 #{{ scope.row.task_id }}
          </template>
        </el-table-column>
        <el-table-column label="触发方式" prop="trigger_type" width="100">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.trigger_type === 'manual' ? 'primary' : 'success'">
              {{ scope.row.trigger_type === 'manual' ? '手动' : '定时' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" prop="status" width="100">
          <template slot-scope="scope">
            <el-tag size="mini" :type="statusType(scope.row.status)">{{ statusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通过/总数" width="120">
          <template slot-scope="scope">
            <span style="color: #67C23A">{{ scope.row.pass_count }}</span> / {{ scope.row.total_count }}
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template slot-scope="scope">
            {{ formatDuration(scope.row.duration_ms) }}
          </template>
        </el-table-column>
        <el-table-column label="执行时间" prop="created_time" min-width="160"></el-table-column>
        <el-table-column label="操作" width="80">
          <template slot-scope="scope">
            <el-button type="text" size="mini" @click="viewDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getInspectionDashboard, getInspectionExecutionList } from '@/api/inspectionApi'

export default {
  name: 'InspectionDashboard',
  components: { PageSection },
  data() {
    return {
      loading: false,
      stats: {},
      recentExecutions: []
    }
  },
  computed: {
    passRate() {
      var total = this.stats.total_executions_today || 0
      if (total === 0) return 0
      var passed = this.stats.pass_count_today || 0
      return Math.round(passed * 100 / total)
    }
  },
  created() {
    this.fetchDashboard()
    this.fetchRecentExecutions()
  },
  methods: {
    dataOf(res) { return (res && res.data) || res || {} },
    fetchDashboard() {
      getInspectionDashboard().then(res => {
        this.stats = this.dataOf(res)
      })
    },
    fetchRecentExecutions() {
      this.loading = true
      getInspectionExecutionList({ page_no: 1, page_size: 10 }).then(res => {
        this.recentExecutions = this.dataOf(res).items || []
      }).finally(() => { this.loading = false })
    },
    statusText(status) {
      var map = { 0: '待执行', 1: '执行中', 2: '全部通过', 3: '部分失败', 4: '全部失败', 5: '异常' }
      return map[status] || '未知'
    },
    statusType(status) {
      var map = { 0: 'info', 1: 'warning', 2: 'success', 3: 'warning', 4: 'danger', 5: 'danger' }
      return map[status] || 'info'
    },
    formatDuration(ms) {
      if (!ms) return '-'
      if (ms < 1000) return ms + 'ms'
      return (ms / 1000).toFixed(1) + 's'
    },
    viewDetail(row) {
      this.$router.push({ path: '/inspection/executions', query: { id: row.id } })
    }
  }
}
</script>

<style scoped>
.stat-card { text-align: center; padding: 10px 0; }
.stat-value { font-size: 32px; font-weight: bold; line-height: 1.2; }
.stat-label { font-size: 14px; color: #909399; margin-top: 8px; }
</style>
