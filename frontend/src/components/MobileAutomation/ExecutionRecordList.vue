<template>
  <div class="page-wrap">
    <page-section title="移动执行记录">
      <template slot="extra">
        <el-button size="small" @click="fetchList">刷新</el-button>
      </template>
      <el-form :inline="true" size="small" @submit.native.prevent>
        <el-form-item label="项目">
          <el-select v-model="projectId" clearable filterable placeholder="全部项目" style="width:220px">
            <el-option v-for="item in projects" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" border style="width:100%">
        <el-table-column prop="execution_no" label="执行单号" min-width="190" show-overflow-tooltip />
        <el-table-column label="状态" width="110">
          <template slot-scope="scope">
            <el-tag size="mini" :type="statusTag(scope.row.status)">{{ statusLabel(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="项目" min-width="130">
          <template slot-scope="scope">{{ projectName(scope.row.project_id) }}</template>
        </el-table-column>
        <el-table-column label="应用" min-width="160" show-overflow-tooltip>
          <template slot-scope="scope">{{ rowExt(scope.row).app_package || '-' }}</template>
        </el-table-column>
        <el-table-column label="设备" min-width="150" show-overflow-tooltip>
          <template slot-scope="scope">{{ rowExt(scope.row).device_serial || '-' }}</template>
        </el-table-column>
        <el-table-column prop="env_code" label="环境" width="100" />
        <el-table-column label="通过/总数" width="100">
          <template slot-scope="scope">{{ scope.row.passed_count || 0 }}/{{ scope.row.total_count || 0 }}</template>
        </el-table-column>
        <el-table-column prop="created_time" label="创建时间" min-width="165" />
        <el-table-column label="操作" width="180" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="goDetail(scope.row)">查看详情</el-button>
            <el-button
              v-if="canRetry(scope.row)"
              type="text"
              :loading="retryingId === scope.row.id"
              @click="retry(scope.row)"
            >再次执行</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :current-page="pageNo"
          :page-size="pageSize"
          :total="total"
          @current-change="page => { pageNo = page; fetchList() }"
        />
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProjectList } from '@/api/projectApi'
import { getMobileExecutionList, retryMobileExecution } from '@/api/mobileAutomationApi'

const STATUS_LABELS = {
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

const RETRYABLE = new Set([4, 5, 6, 7])

export default {
  name: 'MobileAutomationExecutionRecordList',
  components: { PageSection },
  data () {
    return {
      loading: false,
      retryingId: null,
      rows: [],
      projects: [],
      projectId: '',
      pageNo: 1,
      pageSize: 20,
      total: 0
    }
  },
  created () {
    getProjectList({ pageNo: 1, pageSize: 500 }).then(res => {
      const d = this.dataOf(res)
      this.projects = d.list || d.items || []
    })
    this.fetchList()
  },
  methods: {
    dataOf (res) {
      return (res && res.data) || res || {}
    },
    rowExt (row) {
      return (row && row.ext) || {}
    },
    statusLabel (status) {
      return STATUS_LABELS[Number(status)] || status || '-'
    },
    statusTag (status) {
      const s = Number(status)
      if (s === 4) return 'success'
      if (s === 5 || s === 7 || s === 8) return 'danger'
      if (s === 6) return 'info'
      if (s === 3 || s === 1 || s === 2) return 'warning'
      return ''
    },
    canRetry (row) {
      return RETRYABLE.has(Number(row && row.status))
    },
    projectName (id) {
      const item = this.projects.find(v => String(v.id) === String(id))
      return item ? item.name : (id || '-')
    },
    search () {
      this.pageNo = 1
      this.fetchList()
    },
    fetchList () {
      this.loading = true
      getMobileExecutionList(Object.assign(
        { page_no: this.pageNo, page_size: this.pageSize },
        this.projectId ? { project_id: this.projectId } : {}
      )).then(res => {
        const d = this.dataOf(res)
        this.rows = d.list || []
        this.total = Number(d.total || 0)
      }).finally(() => {
        this.loading = false
      })
    },
    goDetail (row) {
      this.$router.push({
        path: '/mobile-automation/execution/detail',
        query: { execution_id: row.id }
      })
    },
    retry (row) {
      this.$confirm('将按原配置创建新的移动执行，是否继续？', '再次执行', { type: 'warning' }).then(() => {
        this.retryingId = row.id
        return retryMobileExecution(row.id)
      }).then(res => {
        const d = this.dataOf(res)
        this.$message.success('已创建新的执行')
        this.$router.push({
          path: '/mobile-automation/execution/detail',
          query: { execution_id: d.id }
        })
      }).catch(() => {}).finally(() => {
        this.retryingId = null
      })
    }
  }
}
</script>

<style scoped>
.pager { margin-top: 16px; text-align: right; }
</style>
