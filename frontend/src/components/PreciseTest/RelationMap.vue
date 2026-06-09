<template>
  <div class="page-wrap precise-page">
    <page-section title="精准测试-关系图谱维护">
      <template slot="extra"><el-button size="small" type="primary" @click="openCreate">新增关系</el-button></template>
      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="产品名称">
          <el-select v-model="queryForm.productId" clearable filterable placeholder="请选择产品" style="width:180px;" @change="onQueryProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-select v-model="queryForm.projectId" clearable filterable :disabled="!queryForm.productId" placeholder="请先选择产品" style="width:180px;">
            <el-option v-for="item in queryProjectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="关系类型"><el-select v-model="queryForm.relationType" clearable style="width:170px;"><el-option v-for="item in relationTypes" :key="item" :label="item" :value="item" /></el-select></el-form-item>
        <el-form-item label="关键字"><el-input v-model.trim="queryForm.keyword" clearable style="width:180px;" /></el-form-item>
        <el-form-item><el-button type="primary" @click="fetchList">查询</el-button><el-button @click="resetQuery">重置</el-button></el-form-item>
      </el-form>
      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="产品名称" min-width="120" show-overflow-tooltip><template slot-scope="scope">{{ preciseProductName(scope.row) }}</template></el-table-column>
        <el-table-column label="项目名称" min-width="140" show-overflow-tooltip><template slot-scope="scope">{{ preciseProjectName(scope.row) }}</template></el-table-column>
        <el-table-column prop="relation_type" label="关系类型" width="130" />
        <el-table-column prop="source_type" label="源类型" width="110" />
        <el-table-column prop="source_key" label="源对象" min-width="220" show-overflow-tooltip />
        <el-table-column prop="target_type" label="目标类型" width="110" />
        <el-table-column prop="target_key" label="目标对象" min-width="220" show-overflow-tooltip />
        <el-table-column prop="confidence" label="置信度" width="90" />
        <el-table-column prop="source_origin" label="来源" width="100" />
        <el-table-column label="操作" width="130" fixed="right"><template slot-scope="scope"><el-button type="text" @click="openEdit(scope.row)">编辑</el-button><el-button type="text" style="color:#F56C6C" @click="remove(scope.row)">删除</el-button></template></el-table-column>
      </el-table>
      <div class="pager-wrap"><el-pagination background layout="total, sizes, prev, pager, next, jumper" :current-page="pageNo" :page-size="pageSize" :page-sizes="[10,20,50,100]" :total="total" @size-change="handleSizeChange" @current-change="handleCurrentChange" /></div>
    </page-section>
    <el-dialog :title="form.id ? '编辑关系' : '新增关系'" :visible.sync="dialogVisible" width="720px">
      <el-form :model="form" label-width="110px" size="small">
        <el-form-item label="产品名称">
          <el-select v-model="form.productId" clearable filterable placeholder="请选择产品" style="width:100%;" @change="onFormProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-select v-model="form.projectId" clearable filterable :disabled="!form.productId" placeholder="请先选择产品" style="width:100%;">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="关系类型"><el-select v-model="form.relationType" filterable allow-create style="width:100%;"><el-option v-for="item in relationTypes" :key="item" :label="item" :value="item" /></el-select></el-form-item>
        <el-form-item label="源类型"><el-input v-model.trim="form.sourceType" placeholder="file/api/module/case" /></el-form-item>
        <el-form-item label="源对象"><el-input v-model.trim="form.sourceKey" /></el-form-item>
        <el-form-item label="目标类型"><el-input v-model.trim="form.targetType" placeholder="api/module/case/script" /></el-form-item>
        <el-form-item label="目标对象"><el-input v-model.trim="form.targetKey" /></el-form-item>
        <el-form-item label="置信度"><el-input-number v-model="form.confidence" :min="0" :max="1" :step="0.1" /></el-form-item>
      </el-form>
      <span slot="footer"><el-button @click="dialogVisible=false">取消</el-button><el-button type="primary" @click="save">保存</el-button></span>
    </el-dialog>
  </div>
</template>
<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getPreciseRelationList, createPreciseRelation, updatePreciseRelation, deletePreciseRelation } from '@/api/preciseTestApi'
import productProjectSelectMixin from './productProjectSelectMixin'

export default {
  name: 'PreciseRelationMap',
  components: { PageSection },
  mixins: [productProjectSelectMixin],
  data() {
    return {
      loading: false,
      dialogVisible: false,
      rows: [],
      total: 0,
      pageNo: 1,
      pageSize: 20,
      queryForm: { productId: '', projectId: '', relationType: '', keyword: '' },
      form: {},
      relationTypes: ['file_api', 'api_module', 'module_case', 'case_script', 'api_performance', 'api_mock', 'api_contract']
    }
  },
  created() { this.fetchList() },
  methods: {
    listOf(res) {
      const d = res && res.data ? res.data : res || {}
      return { rows: d.items || d.list || d.data || [], total: d.total || d.totalCount || 0 }
    },
    fetchList() {
      this.loading = true
      getPreciseRelationList(Object.assign({}, this.queryForm, { pageNo: this.pageNo, pageSize: this.pageSize })).then(res => {
        const d = this.listOf(res)
        this.rows = d.rows
        this.total = d.total || this.rows.length
        this.fillPreciseProjectNames(this.rows)
      }).finally(() => { this.loading = false })
    },
    resetQuery() {
      this.queryForm = { productId: '', projectId: '', relationType: '', keyword: '' }
      this.queryProjectOptions = []
      this.pageNo = 1
      this.fetchList()
    },
    handleSizeChange(v) { this.pageSize = v; this.pageNo = 1; this.fetchList() },
    handleCurrentChange(v) { this.pageNo = v; this.fetchList() },
    onQueryProductChange(productId) {
      this.queryForm.projectId = ''
      this.loadProjectOptions(productId, 'queryProjectOptions')
    },
    onFormProductChange(productId) {
      this.form.projectId = ''
      this.loadProjectOptions(productId, 'projectOptions')
    },
    openCreate() {
      this.form = { productId: '', projectId: '', confidence: 1 }
      this.projectOptions = []
      this.dialogVisible = true
    },
    openEdit(row) {
      const productId = row.product_id || row.productId || ''
      const projectId = row.project_id || row.projectId || ''
      this.form = Object.assign({}, row, {
        productId: String(productId),
        projectId: String(projectId),
        relationType: row.relation_type || row.relationType,
        sourceType: row.source_type || row.sourceType,
        sourceKey: row.source_key || row.sourceKey,
        targetType: row.target_type || row.targetType,
        targetKey: row.target_key || row.targetKey
      })
      this.dialogVisible = true
      this.loadProjectOptions(productId, 'projectOptions')
    },
    save() {
      const payload = this.buildPreciseProjectPayload(this.form)
      const api = this.form.id ? updatePreciseRelation(this.form.id, payload) : createPreciseRelation(payload)
      api.then(() => { this.$message.success('保存成功'); this.dialogVisible = false; this.fetchList() })
    },
    remove(row) {
      this.$confirm('确认删除该关系？', '提示').then(() => deletePreciseRelation(row.id).then(() => {
        this.$message.success('删除成功')
        this.fetchList()
      })).catch(() => {})
    }
  }
}
</script>
<style scoped>.pager-wrap{margin-top:16px;text-align:right;}</style>
