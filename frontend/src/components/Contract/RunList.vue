<template>
  <div class="page-wrap">
    <page-section title="契约执行记录">
      <template slot="extra">
        <el-button size="small" @click="fetchList">刷新</el-button>
        <el-button size="small" @click="$router.push('/contract/suites')">套件列表</el-button>
      </template>
      <el-form :inline="true" size="small">
        <el-form-item label="项目ID">
          <el-input v-model="query.project_id" clearable style="width:140px;" placeholder="可选" />
        </el-form-item>
        <el-form-item label="套件ID">
          <el-input v-model="query.suite_id" clearable style="width:140px;" placeholder="可选" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
        </el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" border>
        <el-table-column prop="run_no" label="执行号" min-width="180" show-overflow-tooltip />
        <el-table-column prop="suite_name" label="套件" min-width="140" show-overflow-tooltip />
        <el-table-column prop="trigger_type" label="触发" width="100" />
        <el-table-column label="结果" width="280">
          <template slot-scope="scope">
            pass {{ scope.row.pass_count }} / drift {{ scope.row.drift_count }} / err {{ scope.row.error_count }} / breaking {{ scope.row.breaking_count }}
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时ms" width="90" />
        <el-table-column prop="created_time" label="时间" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="goDetail(scope.row.id)">详情</el-button>
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
          @current-change="v => { pageNo = v; fetchList() }"
        />
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getContractRunList } from '@/api/contractApi'

export default {
  name: 'ContractRunList',
  components: { PageSection },
  data () {
    return {
      loading: false,
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      query: {
        project_id: this.$route.query.project_id || '',
        suite_id: this.$route.query.suite_id || ''
      }
    }
  },
  created () { this.fetchList() },
  methods: {
    dataOf (res) { return (res && res.data) || res || {} },
    fetchList () {
      this.loading = true
      const params = { page_no: this.pageNo, page_size: this.pageSize }
      if (this.query.project_id) params.project_id = this.query.project_id
      if (this.query.suite_id) params.suite_id = this.query.suite_id
      getContractRunList(params).then(res => {
        const data = this.dataOf(res)
        this.rows = data.items || []
        this.total = data.total || 0
      }).finally(() => { this.loading = false })
    },
    goDetail (id) {
      this.$router.push({ path: '/contract/run/detail', query: { id } })
    }
  }
}
</script>

<style scoped>
.pager { margin-top: 16px; text-align: right; }
</style>
