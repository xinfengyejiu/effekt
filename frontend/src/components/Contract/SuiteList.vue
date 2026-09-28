<template>
  <div class="page-wrap">
    <page-section title="契约套件">
      <template slot="extra">
        <el-button type="primary" size="small" @click="goEdit()">新建套件</el-button>
        <el-button size="small" @click="fetchList">刷新</el-button>
      </template>

      <el-form :inline="true" size="small">
        <el-form-item label="产品">
          <el-select v-model="filterProductId" clearable filterable placeholder="产品" style="width:180px;" @change="onFilterProductChange">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="query.project_id" clearable filterable :disabled="!filterProductId" placeholder="项目" style="width:200px;" @change="fetchList">
            <el-option v-for="p in filterProjects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="套件名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="base_url" label="Base URL" min-width="200" show-overflow-tooltip />
        <el-table-column prop="item_count" label="接口数" width="80" />
        <el-table-column label="调度" width="120">
          <template slot-scope="scope">{{ scope.row.schedule_type || 'manual' }}</template>
        </el-table-column>
        <el-table-column label="启用" width="90">
          <template slot-scope="scope">
            <el-switch :value="scope.row.enabled === 1" @change="onToggle(scope.row)" />
          </template>
        </el-table-column>
        <el-table-column prop="last_run_at" label="最近执行" width="170" />
        <el-table-column label="操作" width="260" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="goEdit(scope.row.id)">编辑</el-button>
            <el-button type="text" :loading="runningId === scope.row.id" @click="onRun(scope.row)">执行</el-button>
            <el-button type="text" @click="goRuns(scope.row.id)">记录</el-button>
            <el-button type="text" style="color:#f56c6c;" @click="onDelete(scope.row)">删除</el-button>
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
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  getContractSuiteList,
  toggleContractSuite,
  deleteContractSuite,
  runContractSuite
} from '@/api/contractApi'

export default {
  name: 'ContractSuiteList',
  components: { PageSection },
  data () {
    return {
      loading: false,
      runningId: null,
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      products: [],
      filterProjects: [],
      filterProductId: '',
      query: { project_id: '' }
    }
  },
  created () {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    dataOf (res) { return (res && res.data) || res || {} },
    listOf (res) {
      const d = this.dataOf(res)
      return d.list || d.items || d.data || []
    },
    loadProducts () {
      getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        this.products = this.listOf(res)
      })
    },
    onFilterProductChange (productId) {
      this.query.project_id = ''
      this.filterProjects = []
      if (!productId) {
        this.fetchList()
        return
      }
      getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        this.filterProjects = this.listOf(res)
        this.fetchList()
      })
    },
    fetchList () {
      this.loading = true
      const params = {
        page_no: this.pageNo,
        page_size: this.pageSize
      }
      if (this.filterProductId) params.product_id = this.filterProductId
      if (this.query.project_id) params.project_id = this.query.project_id
      getContractSuiteList(params).then(res => {
        const data = this.dataOf(res)
        this.rows = data.items || []
        this.total = data.total || 0
      }).finally(() => { this.loading = false })
    },
    goEdit (id) {
      this.$router.push({ path: '/contract/suite/edit', query: id ? { id } : {} })
    },
    goRuns (suiteId) {
      this.$router.push({ path: '/contract/runs', query: { suite_id: suiteId } })
    },
    onToggle (row) {
      toggleContractSuite(row.id).then(() => {
        this.$message.success('已更新')
        this.fetchList()
      })
    },
    onRun (row) {
      this.runningId = row.id
      runContractSuite(row.id).then(res => {
        const data = this.dataOf(res)
        this.$message.success('执行完成')
        if (data && data.id) {
          this.$router.push({ path: '/contract/run/detail', query: { id: data.id } })
        } else {
          this.fetchList()
        }
      }).finally(() => { this.runningId = null })
    },
    onDelete (row) {
      this.$confirm('确认删除该套件？', '提示', { type: 'warning' }).then(() => {
        return deleteContractSuite(row.id)
      }).then(() => {
        this.$message.success('已删除')
        this.fetchList()
      }).catch(() => {})
    }
  }
}
</script>

<style scoped>
.pager { margin-top: 16px; text-align: right; }
</style>
