<template>
  <div class="page-wrap">
    <page-section title="数据库连接管理">
      <template slot="extra">
        <el-button type="primary" size="small" icon="el-icon-plus" @click="openCreate">新建连接</el-button>
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
        <el-table-column label="名称" prop="name" min-width="140" />
        <el-table-column label="关联项目" width="160">
          <template slot-scope="scope">{{ projectName(scope.row.project_id) }}</template>
        </el-table-column>
        <el-table-column label="类型" width="100">
          <template slot-scope="scope">
            <el-tag size="mini">{{ scope.row.db_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="主机" width="200">
          <template slot-scope="scope">{{ scope.row.host }}:{{ scope.row.port }}</template>
        </el-table-column>
        <el-table-column label="数据库" prop="database_name" width="140" />
        <el-table-column label="用户名" prop="username" width="120" />
        <el-table-column label="状态" width="80">
          <template slot-scope="scope">
            <el-tag size="mini" :type="scope.row.enabled === 1 ? 'success' : 'info'">
              {{ scope.row.enabled === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template slot-scope="scope">
            <el-button type="text" size="mini" @click="openEdit(scope.row)">编辑</el-button>
            <el-button type="text" size="mini" style="color: #67C23A" @click="testConnection(scope.row)">测试</el-button>
            <el-button type="text" size="mini" style="color: #F56C6C" @click="remove(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </page-section>

    <el-dialog :title="form.id ? '编辑连接' : '新建连接'" :visible.sync="dialogVisible" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" size="small">
        <el-form-item label="连接名称" prop="name">
          <el-input v-model="form.name" placeholder="如: 生产只读库" />
        </el-form-item>
        <el-form-item label="关联产品" prop="product_id">
          <el-select
            v-model="form.product_id"
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
            v-model="form.project_id"
            clearable
            filterable
            :disabled="!form.product_id"
            placeholder="请先选择产品"
            style="width: 100%"
          >
            <el-option v-for="p in formProjects" :key="p.id" :label="p.name" :value="String(p.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据库类型" prop="db_type">
          <el-select v-model="form.db_type" style="width: 100%" @change="onDbTypeChange">
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="MySQL" value="mysql" />
            <el-option label="SQL Server" value="sqlserver" />
            <el-option label="Oracle" value="oracle" />
          </el-select>
        </el-form-item>
        <el-form-item label="主机" prop="host">
          <el-input v-model="form.host" placeholder="如: 192.168.1.100" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input v-model.number="form.port" type="number" min="1" max="65535" placeholder="如: 5432" style="width: 160px" />
          <div class="form-hint">须为效能平台服务器可访问的对外端口；容器内 5432 常需填映射端口（如 8366）</div>
        </el-form-item>
        <el-form-item label="数据库名" prop="database_name">
          <el-input v-model="form.database_name" placeholder="如: mydb" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="数据库用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password :placeholder="form.id ? '不修改请留空' : '密码'" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" :loading="testing" @click="testCreate">测试连接</el-button>
        <el-button size="small" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="saving" @click="save">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  getInspectionDbConfigList,
  createInspectionDbConfig,
  updateInspectionDbConfig,
  deleteInspectionDbConfig,
  testInspectionDbConnection
} from '@/api/inspectionApi'

const DEFAULT_PORTS = {
  postgresql: 5432,
  mysql: 3306,
  sqlserver: 1433,
  oracle: 1521
}

export default {
  name: 'InspectionDbConfigList',
  components: { PageSection },
  data () {
    return {
      loading: false,
      saving: false,
      testing: false,
      rows: [],
      products: [],
      projectNameMap: {},
      filterProductId: '',
      filterProjects: [],
      formProjects: [],
      query: { project_id: '' },
      dialogVisible: false,
      form: this.emptyForm(),
      rules: {
        name: [{ required: true, message: '请输入连接名称', trigger: 'blur' }],
        product_id: [{ required: true, message: '请选择关联产品', trigger: 'change' }],
        project_id: [{ required: true, message: '请选择关联项目', trigger: 'change' }],
        db_type: [{ required: true, message: '请选择数据库类型', trigger: 'change' }],
        host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
        port: [
          { required: true, message: '请输入端口', trigger: 'blur' },
          {
            validator: (rule, value, callback) => {
              const n = Number(value)
              if (!n || n < 1 || n > 65535) callback(new Error('端口需为 1-65535'))
              else callback()
            },
            trigger: 'blur'
          }
        ],
        database_name: [{ required: true, message: '请输入数据库名', trigger: 'blur' }],
        username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
        password: [{
          validator: (rule, value, callback) => {
            if (!this.form.id && !value) callback(new Error('请输入密码'))
            else callback()
          },
          trigger: 'blur'
        }]
      }
    }
  },
  created () {
    this.loadProducts()
    this.fetchList()
  },
  methods: {
    emptyForm () {
      return {
        name: '',
        product_id: '',
        project_id: '',
        db_type: 'postgresql',
        host: '',
        port: 5432,
        database_name: '',
        username: '',
        password: ''
      }
    },
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
    projectName (id) {
      if (id == null || id === '') return '-'
      return this.projectNameMap[String(id)] || id
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
      this.form.project_id = ''
      this.formProjects = []
      if (!productId) return
      this.loadProjectsByProduct(productId).then(rows => {
        this.formProjects = rows
      })
    },
    onDbTypeChange (dbType) {
      if (!this.form.id || !this.form.port) {
        this.form.port = DEFAULT_PORTS[dbType] || 5432
      }
    },
    fetchList () {
      this.loading = true
      const params = { page_no: 1, page_size: 200 }
      if (this.query.project_id) params.project_id = this.query.project_id
      getInspectionDbConfigList(params).then(res => {
        this.rows = this.dataOf(res).items || []
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
      this.form = this.emptyForm()
      this.formProjects = []
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.formRef && this.$refs.formRef.clearValidate()
      })
    },
    openEdit (row) {
      this.form = {
        id: row.id,
        name: row.name,
        product_id: '',
        project_id: row.project_id != null ? String(row.project_id) : '',
        db_type: row.db_type || 'postgresql',
        host: row.host || '',
        port: row.port || DEFAULT_PORTS[row.db_type] || 5432,
        database_name: row.database_name || '',
        username: row.username || '',
        password: ''
      }
      this.formProjects = []
      this.dialogVisible = true
      this.$nextTick(() => {
        this.$refs.formRef && this.$refs.formRef.clearValidate()
      })
      getProjectList({ pageNo: 1, pageSize: 1000 }).then(res => {
        const all = this.listOf(res)
        this.rememberProjects(all)
        const proj = all.find(item => String(item.id) === String(row.project_id))
        if (!proj) return
        this.form.product_id = String(proj.product_id || proj.productId || '')
        return this.loadProjectsByProduct(this.form.product_id).then(rows => {
          this.formProjects = rows
        })
      })
    },
    buildPayload () {
      return {
        id: this.form.id,
        name: this.form.name,
        project_id: Number(this.form.project_id) || this.form.project_id,
        db_type: this.form.db_type,
        host: this.form.host,
        port: Number(this.form.port),
        database_name: this.form.database_name,
        username: this.form.username,
        password: this.form.password
      }
    },
    save () {
      this.$refs.formRef.validate(valid => {
        if (!valid) return
        this.saving = true
        const payload = this.buildPayload()
        if (payload.id && !payload.password) delete payload.password
        const action = payload.id ? updateInspectionDbConfig(payload) : createInspectionDbConfig(payload)
        action.then(() => {
          this.$message.success('保存成功')
          this.dialogVisible = false
          this.fetchList()
        }).catch(err => {
          this.$message.error((err && err.message) || '保存失败')
        }).finally(() => {
          this.saving = false
        })
      })
    },
    testCreate () {
      if (!this.form.host || !this.form.port || !this.form.database_name || !this.form.username) {
        this.$message.warning('请先填写主机、端口、数据库名和用户名')
        return
      }
      if (!this.form.id && !this.form.password) {
        this.$message.warning('请先填写密码')
        return
      }
      this.testing = true
      testInspectionDbConnection(this.buildPayload()).then(() => {
        this.$message.success('连接成功')
      }).catch(err => {
        // 全局 request 拦截器已弹过后端 msg，这里避免再弹一层「连接失败」
        if (!(err && err.message)) this.$message.error('连接失败')
      }).finally(() => {
        this.testing = false
      })
    },
    testConnection (row) {
      testInspectionDbConnection(row).then(() => {
        this.$message.success('连接成功')
      }).catch(err => {
        if (!(err && err.message)) this.$message.error('连接失败')
      })
    },
    remove (row) {
      this.$confirm('确定删除连接「' + row.name + '」？', '提示', { type: 'warning' }).then(() => {
        deleteInspectionDbConfig(row.id).then(() => {
          this.$message.success('删除成功')
          this.fetchList()
        })
      }).catch(() => {})
    }
  }
}
</script>

<style scoped>
.form-hint {
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
  margin-top: 4px;
}
</style>
