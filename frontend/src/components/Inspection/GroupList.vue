<template>
  <div class="page-wrap">
    <page-section title="巡检组管理">
      <template slot="extra">
        <el-button type="primary" size="small" icon="el-icon-plus" @click="openCreate">新建巡检组</el-button>
      </template>

      <el-form inline size="small" @submit.native.prevent>
        <el-form-item label="产品">
          <el-select
            v-model="filterProductId"
            clearable
            filterable
            placeholder="全部产品"
            style="width: 180px"
            @change="onFilterProductChange"
          >
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="String(p.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select
            v-model="query.project_id"
            clearable
            filterable
            placeholder="全部项目"
            style="width: 200px"
            :disabled="!filterProductId"
            @change="fetchList"
          >
            <el-option v-for="p in filterProjects" :key="p.id" :label="p.name" :value="String(p.id)" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="fetchList">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="rows" v-loading="loading" stripe border size="small" style="margin-top: 8px">
        <el-table-column label="组名称" prop="name" min-width="160" />
        <el-table-column label="关联项目" width="160">
          <template slot-scope="scope">{{ projectName(scope.row.project_id) }}</template>
        </el-table-column>
        <el-table-column label="描述" prop="description" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="80">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.enabled === 1 ? 'success' : 'info'">
              {{ scope.row.enabled === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="created_time" width="160" />
        <el-table-column label="操作" width="140">
          <template slot-scope="scope">
            <el-button type="text" size="mini" @click="openEdit(scope.row)">编辑</el-button>
            <el-button type="text" size="mini" style="color: #F56C6C" @click="remove(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        style="margin-top: 12px; text-align: right"
        background
        layout="total, prev, pager, next"
        :total="total"
        :page-size="query.page_size"
        :current-page.sync="query.page_no"
        @current-change="fetchList"
      />
    </page-section>

    <el-dialog :title="formData.id ? '编辑巡检组' : '新建巡检组'" :visible.sync="dialogVisible" width="520px">
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="90px" size="small">
        <el-form-item label="组名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入巡检组名称" />
        </el-form-item>
        <el-form-item label="关联产品" prop="product_id">
          <el-select
            v-model="formData.product_id"
            clearable
            filterable
            placeholder="请选择产品"
            style="width: 100%"
            @change="onFormProductChange"
          >
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="String(p.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联项目" prop="project_id">
          <el-select
            v-model="formData.project_id"
            clearable
            filterable
            :disabled="!formData.product_id"
            placeholder="请先选择产品"
            style="width: 100%"
          >
            <el-option v-for="p in formProjects" :key="p.id" :label="p.name" :value="String(p.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="巡检组描述（选填）" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="saving" @click="save">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProjectList } from '@/api/projectApi'
import { getProductList } from '@/api/productApi'
import {
  getInspectionGroupList,
  createInspectionGroup,
  updateInspectionGroup,
  deleteInspectionGroup
} from '@/api/inspectionApi'

export default {
  name: 'InspectionGroupList',
  components: { PageSection },
  data () {
    return {
      loading: false,
      saving: false,
      rows: [],
      total: 0,
      products: [],
      projectNameMap: {},
      filterProductId: '',
      filterProjects: [],
      formProjects: [],
      query: { page_no: 1, page_size: 20, project_id: '' },
      dialogVisible: false,
      formData: { name: '', product_id: '', project_id: '', description: '' },
      rules: {
        name: [{ required: true, message: '请输入巡检组名称', trigger: 'blur' }],
        product_id: [{ required: true, message: '请选择关联产品', trigger: 'change' }],
        project_id: [{ required: true, message: '请选择关联项目', trigger: 'change' }]
      }
    }
  },
  created () {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    dataOf (res) {
      return (res && res.data) || res || {}
    },
    listOf (res) {
      const d = this.dataOf(res)
      return d.list || d.items || d.data || []
    },
    rememberProjects (rows) {
      ;(rows || []).forEach(item => {
        if (item && item.id != null) {
          this.$set(this.projectNameMap, String(item.id), item.name || String(item.id))
        }
      })
    },
    loadProducts () {
      return getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        this.products = this.listOf(res)
      })
    },
    loadProjectsByProduct (productId) {
      if (!productId) return Promise.resolve([])
      return getProjectList({
        pageNo: 1,
        pageSize: 1000,
        status: 1,
        productId
      }).then(res => {
        const rows = this.listOf(res)
        this.rememberProjects(rows)
        return rows
      })
    },
    onFilterProductChange (productId) {
      this.query.project_id = ''
      this.filterProjects = []
      if (!productId) {
        this.fetchList()
        return
      }
      this.loadProjectsByProduct(productId).then(rows => {
        this.filterProjects = rows
        this.fetchList()
      })
    },
    onFormProductChange (productId) {
      this.formData.project_id = ''
      this.formProjects = []
      if (!productId) return
      this.loadProjectsByProduct(productId).then(rows => {
        this.formProjects = rows
      })
    },
    projectName (id) {
      if (id == null || id === '') return '-'
      return this.projectNameMap[String(id)] || id
    },
    fetchList () {
      this.loading = true
      const params = Object.assign({}, this.query)
      if (this.filterProductId) params.product_id = this.filterProductId
      if (this.query.project_id) params.project_id = this.query.project_id
      getInspectionGroupList(params).then(res => {
        const data = this.dataOf(res)
        this.rows = data.items || data.list || []
        this.total = data.total || 0
        // 补齐列表里项目名
        const missing = this.rows
          .map(row => row.project_id)
          .filter(id => id != null && !this.projectNameMap[String(id)])
        if (missing.length) {
          getProjectList({ pageNo: 1, pageSize: 1000 }).then(projectRes => {
            this.rememberProjects(this.listOf(projectRes))
          })
        }
      }).finally(() => {
        this.loading = false
      })
    },
    openCreate () {
      this.formData = { name: '', product_id: '', project_id: '', description: '' }
      this.formProjects = []
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.formRef && this.$refs.formRef.clearValidate()
      })
    },
    openEdit (row) {
      this.formData = {
        id: row.id,
        name: row.name,
        product_id: '',
        project_id: row.project_id != null ? String(row.project_id) : '',
        description: row.description || ''
      }
      this.formProjects = []
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.formRef && this.$refs.formRef.clearValidate()
      })
      // 先查项目列表反推产品，再加载该产品下项目
      getProjectList({ pageNo: 1, pageSize: 1000 }).then(res => {
        const all = this.listOf(res)
        this.rememberProjects(all)
        const proj = all.find(item => String(item.id) === String(row.project_id))
        if (!proj) return
        this.formData.product_id = String(proj.product_id || proj.productId || '')
        return this.loadProjectsByProduct(this.formData.product_id).then(rows => {
          this.formProjects = rows
        })
      })
    },
    save () {
      this.$refs.formRef.validate(valid => {
        if (!valid) return
        this.saving = true
        const payload = Object.assign({}, this.formData, {
          product_id: this.formData.product_id ? Number(this.formData.product_id) || this.formData.product_id : '',
          project_id: this.formData.project_id ? Number(this.formData.project_id) || this.formData.project_id : ''
        })
        const action = this.formData.id ? updateInspectionGroup(payload) : createInspectionGroup(payload)
        action.then(() => {
          this.$message.success('保存成功')
          this.dialogVisible = false
          this.fetchList()
        }).catch(err => {
          const msg = (err && err.message) || '保存失败'
          this.$message.error(msg)
        }).finally(() => {
          this.saving = false
        })
      })
    },
    remove (row) {
      this.$confirm('确定删除巡检组「' + row.name + '」？', '提示', { type: 'warning' }).then(() => {
        deleteInspectionGroup(row.id).then(() => {
          this.$message.success('删除成功')
          this.fetchList()
        })
      }).catch(() => {})
    }
  }
}
</script>
