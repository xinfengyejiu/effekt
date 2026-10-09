<template>
  <div class="page-wrap ai-probe-conn-page">
    <page-section title="AI智能问数 · 连接管理">
      <template slot="extra">
        <el-button size="small" @click="$router.push('/ai-data-probe')">返回工作台</el-button>
        <el-button size="small" @click="openImport">从项目导入</el-button>
        <el-button size="small" type="primary" icon="el-icon-plus" @click="openCreate">新建连接</el-button>
      </template>

      <el-form :inline="true" :model="queryForm" size="small" @submit.native.prevent>
        <el-form-item label="产品">
          <el-select v-model="queryForm.productId" clearable filterable placeholder="全部" style="width:160px;" @change="onQueryProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select v-model="queryForm.projectId" clearable filterable :disabled="!queryForm.productId" placeholder="全部" style="width:160px;">
            <el-option v-for="item in queryProjectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model.trim="queryForm.keyword" clearable style="width:180px;" @keyup.enter.native="fetchList" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="el-icon-search" :loading="loading" @click="fetchList">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table v-loading="loading" :data="rows" border style="width:100%; margin-top:12px;">
        <el-table-column label="名称" min-width="140" prop="name" show-overflow-tooltip />
        <el-table-column label="产品" min-width="120" prop="productName" show-overflow-tooltip />
        <el-table-column label="项目" min-width="120" prop="projectName" show-overflow-tooltip />
        <el-table-column label="Host" min-width="140" prop="host" show-overflow-tooltip />
        <el-table-column label="库名" min-width="120" prop="databaseName" show-overflow-tooltip />
        <el-table-column label="环境" width="90" prop="env" />
        <el-table-column label="启用" width="80">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.enabled ? 'success' : 'info'">{{ scope.row.enabled ? '是' : '否' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="更新时间" min-width="160" prop="updatedTime" />
        <el-table-column label="操作" width="220" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="testRow(scope.row)">测试</el-button>
            <el-button type="text" @click="openEdit(scope.row)">编辑</el-button>
            <el-button type="text" @click="useInWorkspace(scope.row)">去查数</el-button>
            <el-button type="text" style="color:#F56C6C;" @click="removeRow(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </page-section>

    <el-dialog :title="form.id ? '编辑连接' : '新建连接'" :visible.sync="dialogVisible" width="560px" :close-on-click-modal="false">
      <el-form ref="form" :model="form" :rules="rules" label-width="100px" size="small">
        <el-form-item label="名称" prop="name">
          <el-input v-model.trim="form.name" maxlength="128" />
        </el-form-item>
        <el-form-item label="类型" prop="dbType">
          <el-select v-model="form.dbType" style="width:100%;">
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="MySQL（预留）" value="mysql" />
          </el-select>
        </el-form-item>
        <el-form-item label="Host" prop="host">
          <el-input v-model.trim="form.host" />
        </el-form-item>
        <el-form-item label="Port" prop="port">
          <el-input v-model.number="form.port" />
        </el-form-item>
        <el-form-item label="Database" prop="databaseName">
          <el-input v-model.trim="form.databaseName" />
        </el-form-item>
        <el-form-item label="Username" prop="username">
          <el-input v-model.trim="form.username" />
        </el-form-item>
        <el-form-item label="Password" prop="password">
          <el-input v-model="form.password" type="password" show-password :placeholder="form.id ? '不改请留空或保持 ******' : ''" />
        </el-form-item>
        <el-form-item label="环境" prop="env">
          <el-input v-model.trim="form.env" placeholder="test / sit / uat（禁 prod）" />
        </el-form-item>
        <el-form-item label="产品" prop="productId">
          <el-select v-model="form.productId" filterable clearable placeholder="选择产品" style="width:100%;" @change="onFormProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" prop="projectId">
          <el-select v-model="form.projectId" filterable clearable :disabled="!form.productId" placeholder="选择项目" style="width:100%;" @change="onFormProjectChange">
            <el-option v-for="item in formProjectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button size="small" @click="dialogVisible = false">取消</el-button>
        <el-button size="small" :loading="testing" @click="testForm">测试连通</el-button>
        <el-button size="small" type="primary" :loading="saving" @click="save">保存</el-button>
      </span>
    </el-dialog>

    <el-dialog title="从项目环境导入" :visible.sync="importVisible" width="480px" :close-on-click-modal="false">
      <el-form :model="importForm" label-width="90px" size="small">
        <el-form-item label="产品" required>
          <el-select v-model="importForm.productId" filterable placeholder="选择产品" style="width:100%;" @change="onImportProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" required>
          <el-select v-model="importForm.projectId" filterable :disabled="!importForm.productId" placeholder="选择项目" style="width:100%;" @change="onImportProjectChange">
            <el-option v-for="item in importProjectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境" required>
          <el-input v-model.trim="importForm.env" placeholder="test" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model.trim="importForm.name" placeholder="可空，默认 项目-环境" />
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button size="small" @click="importVisible = false">取消</el-button>
        <el-button size="small" type="primary" :loading="importing" @click="doImport">导入</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  createAiDataProbeConnection,
  deleteAiDataProbeConnection,
  getAiDataProbeConnections,
  importAiDataProbeConnection,
  testAiDataProbeConnection,
  updateAiDataProbeConnection
} from '@/api/aiDataProbeApi'

export default {
  name: 'AiDataProbeConnectionList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      saving: false,
      testing: false,
      importing: false,
      rows: [],
      productOptions: [],
      queryProjectOptions: [],
      formProjectOptions: [],
      importProjectOptions: [],
      queryForm: { productId: '', projectId: '', keyword: '' },
      dialogVisible: false,
      importVisible: false,
      form: this.emptyForm(),
      importForm: { productId: '', projectId: '', productName: '', projectName: '', env: 'test', name: '' },
      rules: {
        name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
        host: [{ required: true, message: '请输入 host', trigger: 'blur' }],
        port: [{ required: true, message: '请输入 port', trigger: 'blur' }],
        databaseName: [{ required: true, message: '请输入 database', trigger: 'blur' }],
        username: [{ required: true, message: '请输入 username', trigger: 'blur' }],
        env: [{ required: true, message: '请输入环境', trigger: 'blur' }],
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }]
      }
    }
  },
  created() {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    emptyForm() {
      return {
        id: null,
        name: '',
        dbType: 'postgresql',
        host: '',
        port: 5432,
        databaseName: '',
        username: '',
        password: '',
        env: 'test',
        productId: '',
        productName: '',
        projectId: '',
        projectName: '',
        remark: '',
        enabled: 1
      }
    },
    productNameById(id) {
      const item = this.productOptions.find(p => String(p.id) === String(id))
      return item ? item.name : ''
    },
    projectNameById(id, list) {
      const item = (list || []).find(p => String(p.id) === String(id))
      return item ? item.name : ''
    },
    loadProducts() {
      getProductList({ pageNo: 1, pageSize: 200 }).then(res => {
        this.productOptions = this.apiData(res).list || this.apiData(res).items || []
      })
    },
    loadProjects(productId, target) {
      if (!productId) {
        this[target] = []
        return Promise.resolve([])
      }
      return getProjectList({ productId, pageNo: 1, pageSize: 200 }).then(res => {
        this[target] = this.apiData(res).list || this.apiData(res).items || []
        return this[target]
      })
    },
    onQueryProductChange(v) {
      this.queryForm.projectId = ''
      this.loadProjects(v, 'queryProjectOptions')
    },
    onFormProductChange(v) {
      this.form.projectId = ''
      this.form.projectName = ''
      this.form.productName = this.productNameById(v)
      this.loadProjects(v, 'formProjectOptions')
    },
    onFormProjectChange(v) {
      this.form.projectName = this.projectNameById(v, this.formProjectOptions)
    },
    onImportProductChange(v) {
      this.importForm.projectId = ''
      this.importForm.projectName = ''
      this.importForm.productName = this.productNameById(v)
      this.loadProjects(v, 'importProjectOptions')
    },
    onImportProjectChange(v) {
      this.importForm.projectName = this.projectNameById(v, this.importProjectOptions)
    },
    fetchList() {
      this.loading = true
      getAiDataProbeConnections({
        productId: this.queryForm.productId || undefined,
        projectId: this.queryForm.projectId || undefined,
        keyword: this.queryForm.keyword,
        pageNo: 1,
        pageSize: 50
      })
        .then(res => {
          const data = (res && res.data) || {}
          this.rows = data.list || []
        })
        .catch(() => { this.rows = [] })
        .finally(() => { this.loading = false })
    },
    openCreate() {
      this.form = this.emptyForm()
      this.formProjectOptions = []
      this.dialogVisible = true
    },
    openEdit(row) {
      this.form = Object.assign(this.emptyForm(), {
        id: row.id,
        name: row.name,
        dbType: row.dbType || 'postgresql',
        host: row.host,
        port: row.port,
        databaseName: row.databaseName,
        username: row.username,
        password: row.password || '******',
        env: row.env,
        productId: row.productId != null ? String(row.productId) : '',
        productName: row.productName || '',
        projectId: row.projectId != null ? String(row.projectId) : '',
        projectName: row.projectName || '',
        remark: row.remark || '',
        enabled: row.enabled
      })
      this.formProjectOptions = []
      const load = this.form.productId
        ? this.loadProjects(this.form.productId, 'formProjectOptions')
        : Promise.resolve([])
      load.finally(() => { this.dialogVisible = true })
    },
    openImport() {
      this.importForm = { productId: '', projectId: '', productName: '', projectName: '', env: 'test', name: '' }
      this.importProjectOptions = []
      this.importVisible = true
    },
    payloadFromForm() {
      const data = {
        name: this.form.name,
        dbType: this.form.dbType,
        host: this.form.host,
        port: this.form.port,
        databaseName: this.form.databaseName,
        username: this.form.username,
        password: this.form.password,
        env: this.form.env,
        productId: this.form.productId || null,
        productName: this.form.productName || this.productNameById(this.form.productId),
        projectId: this.form.projectId || null,
        projectName: this.form.projectName || this.projectNameById(this.form.projectId, this.formProjectOptions),
        remark: this.form.remark,
        enabled: this.form.enabled
      }
      if (this.form.id) data.id = this.form.id
      return data
    },
    save() {
      this.$refs.form.validate(valid => {
        if (!valid) return
        if (!this.form.id && !this.form.password) {
          this.$message.warning('请填写密码')
          return
        }
        this.saving = true
        const req = this.form.id ? updateAiDataProbeConnection(this.payloadFromForm()) : createAiDataProbeConnection(this.payloadFromForm())
        req.then(() => {
          this.$message.success('已保存')
          this.dialogVisible = false
          this.fetchList()
        }).finally(() => { this.saving = false })
      })
    },
    testForm() {
      this.testing = true
      testAiDataProbeConnection(this.payloadFromForm())
        .then(res => {
          const data = (res && res.data) || {}
          this.$message.success('连通成功' + (data.latencyMs != null ? `（${data.latencyMs}ms）` : ''))
        })
        .finally(() => { this.testing = false })
    },
    testRow(row) {
      testAiDataProbeConnection({ id: row.id }).then(res => {
        const data = (res && res.data) || {}
        this.$message.success('连通成功' + (data.latencyMs != null ? `（${data.latencyMs}ms）` : ''))
      })
    },
    removeRow(row) {
      this.$confirm('确认删除该连接？', '提示', { type: 'warning' }).then(() => {
        return deleteAiDataProbeConnection({ id: row.id })
      }).then(() => {
        this.$message.success('已删除')
        this.fetchList()
      }).catch(() => {})
    },
    doImport() {
      if (!this.importForm.productId || !this.importForm.projectId || !this.importForm.env) {
        this.$message.warning('请选择产品、项目并填写环境')
        return
      }
      this.importing = true
      importAiDataProbeConnection({
        productId: this.importForm.productId,
        productName: this.importForm.productName || this.productNameById(this.importForm.productId),
        projectId: this.importForm.projectId,
        projectName: this.importForm.projectName || this.projectNameById(this.importForm.projectId, this.importProjectOptions),
        env: this.importForm.env,
        name: this.importForm.name
      })
        .then(() => {
          this.$message.success('导入成功')
          this.importVisible = false
          this.fetchList()
        })
        .finally(() => { this.importing = false })
    },
    useInWorkspace(row) {
      this.$router.push({ path: '/ai-data-probe', query: { connectionId: row.id } })
    }
  }
}
</script>
