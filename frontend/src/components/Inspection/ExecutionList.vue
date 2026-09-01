<template>
  <div class="page-wrap">
    <page-section title="执行记录">
      <el-form inline size="small">
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部" @change="fetchList" style="width: 130px">
            <el-option label="待执行" :value="0"></el-option>
            <el-option label="执行中" :value="1"></el-option>
            <el-option label="全部通过" :value="2"></el-option>
            <el-option label="部分失败" :value="3"></el-option>
            <el-option label="全部失败" :value="4"></el-option>
            <el-option label="异常" :value="5"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button size="small" icon="el-icon-search" @click="fetchList">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="rows" v-loading="loading" stripe border size="small">
        <el-table-column label="ID" prop="id" width="70"></el-table-column>
        <el-table-column label="任务ID" prop="task_id" width="80"></el-table-column>
        <el-table-column label="触发方式" width="90">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.trigger_type === 'manual' ? 'primary' : 'success'">
              {{ scope.row.trigger_type === 'manual' ? '手动' : '定时' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template slot-scope="scope">
            <el-tag size="mini" :type="statusType(scope.row.status)">{{ statusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通过/总数" width="110">
          <template slot-scope="scope">
            <span style="color: #67C23A">{{ scope.row.pass_count }}</span> / {{ scope.row.total_count }}
          </template>
        </el-table-column>
        <el-table-column label="失败" width="70">
          <template slot-scope="scope">
            <span :style="{color: scope.row.fail_count > 0 ? '#F56C6C' : ''}">{{ scope.row.fail_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="异常" width="70">
          <template slot-scope="scope">
            <span :style="{color: scope.row.error_count > 0 ? '#E6A23C' : ''}">{{ scope.row.error_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="100">
          <template slot-scope="scope">{{ formatDuration(scope.row.duration_ms) }}</template>
        </el-table-column>
        <el-table-column label="开始时间" prop="start_time" width="160"></el-table-column>
        <el-table-column label="通知" width="80">
          <template slot-scope="scope">
            <el-tag size="mini" v-if="scope.row.notify_status === 1" type="success">已通知</el-tag>
            <el-tag size="mini" v-else-if="scope.row.notify_status === 2" type="danger">失败</el-tag>
            <span v-else style="color: #C0C4CC">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80">
          <template slot-scope="scope">
            <el-button type="text" size="mini" @click="viewDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top: 12px; text-align: right" background layout="total, prev, pager, next"
        :total="total" :page-size="query.page_size" :current-page.sync="query.page_no" @current-change="fetchList">
      </el-pagination>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getInspectionExecutionList } from '@/api/inspectionApi'

export default {
  name: 'InspectionExecutionList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      rows: [],
      total: 0,
      query: { page_no: 1, page_size: 20, status: '' }
    }
  },
  created() {
    this.fetchList()
  },
  methods: {
    dataOf(res) { return (res && res.data) || res || {} },
    fetchList() {
      this.loading = true
      getInspectionExecutionList(this.query).then(res => {
        var data = this.dataOf(res)
        this.rows = data.items || []
        this.total = data.total || 0
      }).finally(() => { this.loading = false })
    },
    statusText(s) {
      return { 0: '待执行', 1: '执行中', 2: '全部通过', 3: '部分失败', 4: '全部失败', 5: '异常' }[s] || '未知'
    },
    statusType(s) {
      return { 0: 'info', 1: 'warning', 2: 'success', 3: 'warning', 4: 'danger', 5: 'danger' }[s] || 'info'
    },
    formatDuration(ms) {
      if (!ms) return '-'
      return ms < 1000 ? ms + 'ms' : (ms / 1000).toFixed(1) + 's'
    },
    viewDetail(row) {
      this.$router.push({ path: '/inspection/executions', query: { detail_id: row.id } })
    }
  }
}
</script>
