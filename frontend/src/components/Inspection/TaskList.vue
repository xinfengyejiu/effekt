<template>
  <div class="page-wrap">
    <el-row :gutter="16">
      <!-- 左侧：巡检组导航 -->
      <el-col :span="5">
        <el-card style="min-height: 500px">
          <div slot="header"><span style="font-weight: bold">巡检组</span></div>
          <el-menu :default-active="String(query.group_id || '')" @select="onGroupSelect">
            <el-menu-item index="">全部</el-menu-item>
            <el-menu-item v-for="g in groups" :key="g.id" :index="String(g.id)">
              <i class="el-icon-folder"></i> {{ g.name }}
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 右侧：任务列表 -->
      <el-col :span="19">
        <page-section :title="currentGroupName + ' - 巡检任务'">
          <template slot="extra">
            <el-button type="primary" size="small" icon="el-icon-plus" @click="openCreate">新建任务</el-button>
          </template>

          <el-table :data="rows" v-loading="loading" stripe border size="small">
            <el-table-column label="任务名称" prop="name" min-width="160"></el-table-column>
            <el-table-column label="类型" width="100">
              <template slot-scope="scope">
                <el-tag size="mini" :type="typeTagColor(scope.row.task_type)">{{ typeText(scope.row.task_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="调度方式" width="100">
              <template slot-scope="scope">
                {{ scope.row.schedule_type === 'cron' ? '定时(Cron)' : scope.row.schedule_type === 'interval' ? '间隔' : '手动' }}
              </template>
            </el-table-column>
            <el-table-column label="Cron/间隔" prop="cron_expression" width="140" show-overflow-tooltip></el-table-column>
            <el-table-column label="状态" width="80">
              <template slot-scope="scope">
                <el-switch v-model="scope.row.enabled" :active-value="1" :inactive-value="0" @change="onToggle(scope.row)" style="margin: 0"></el-switch>
              </template>
            </el-table-column>
            <el-table-column label="通知" width="100">
              <template slot-scope="scope">
                <span v-if="scope.row.notify_type">{{ scope.row.notify_type }}</span>
                <span v-else style="color: #C0C4CC">未配置</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template slot-scope="scope">
                <el-button type="text" size="mini" @click="openEdit(scope.row)">编辑</el-button>
                <el-button type="text" size="mini" style="color: #67C23A" @click="executeTask(scope.row)">执行</el-button>
                <el-button type="text" size="mini" style="color: #F56C6C" @click="remove(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination style="margin-top: 12px; text-align: right" background layout="total, prev, pager, next"
            :total="total" :page-size="query.page_size" :current-page.sync="query.page_no" @current-change="fetchList">
          </el-pagination>
        </page-section>
      </el-col>
    </el-row>

    <!-- 创建/编辑任务弹窗 -->
    <el-dialog :title="form.id ? '编辑巡检任务' : '新建巡检任务'" :visible.sync="dialogVisible" width="700px" top="5vh">
      <el-form :model="form" :rules="rules" ref="form" label-width="100px" size="small">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称"></el-input>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="巡检组" prop="group_id">
              <el-select v-model="form.group_id" filterable placeholder="选择巡检组" style="width: 100%">
                <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联项目">
              <el-select v-model="form.project_id" filterable placeholder="选择项目" style="width: 100%">
                <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="form.task_type" style="width: 100%">
            <el-option label="混合类型" value="mixed"></el-option>
            <el-option label="自动化用例" value="auto_case"></el-option>
            <el-option label="接口巡检" value="api"></el-option>
            <el-option label="SQL 巡检" value="sql"></el-option>
            <el-option label="脚本巡检" value="script"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="调度方式">
          <el-radio-group v-model="form.schedule_type">
            <el-radio label="manual">手动</el-radio>
            <el-radio label="cron">定时(Cron)</el-radio>
            <el-radio label="interval">间隔</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.schedule_type === 'cron'" label="Cron 表达式">
          <el-input v-model="form.cron_expression" placeholder="例: 0 9 * * * (每天9点)">
            <template slot="append">
              <el-popover placement="bottom" width="300" trigger="click">
                <div>
                  <p>常用表达式:</p>
                  <p><code>0 9 * * *</code> 每天9:00</p>
                  <p><code>0 */2 * * *</code> 每2小时</p>
                  <p><code>*/30 * * * *</code> 每30分钟</p>
                  <p><code>0 9 * * 1-5</code> 工作日9:00</p>
                </div>
                <el-button slot="reference" size="mini" icon="el-icon-question"></el-button>
              </el-popover>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item v-if="form.schedule_type === 'interval'" label="间隔(秒)">
          <el-input-number v-model="form.interval_seconds" :min="60" :step="60" style="width: 100%"></el-input-number>
        </el-form-item>
        <el-divider content-position="left">通知配置</el-divider>
        <el-form-item label="通知渠道">
          <el-checkbox-group v-model="notifyTypes">
            <el-checkbox label="wechat_work">企业微信</el-checkbox>
            <el-checkbox label="dingtalk">钉钉</el-checkbox>
            <el-checkbox label="feishu">飞书</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item v-if="notifyTypes.length > 0" label="Webhook URL">
          <el-input v-model="form.notify_webhook" placeholder="请输入 Webhook 地址"></el-input>
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
import {
  getInspectionGroupList, getInspectionTaskList, createInspectionTask,
  updateInspectionTask, deleteInspectionTask, toggleInspectionTask, executeInspectionTask
} from '@/api/inspectionApi'

export default {
  name: 'InspectionTaskList',
  components: { PageSection },
  data() {
    return {
      loading: false,
      saving: false,
      rows: [],
      total: 0,
      groups: [],
      projects: [],
      query: { page_no: 1, page_size: 20, group_id: '' },
      dialogVisible: false,
      form: {},
      notifyTypes: [],
      rules: {
        name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
        group_id: [{ required: true, message: '请选择巡检组', trigger: 'change' }],
        task_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }]
      }
    }
  },
  computed: {
    currentGroupName() {
      if (!this.query.group_id) return '全部任务'
      var g = this.groups.find(function(x) { return x.id === Number(this.query.group_id) }.bind(this))
      return g ? g.name : '全部任务'
    }
  },
  created() {
    this.loadProjects()
    this.loadGroups()
    this.fetchList()
  },
  methods: {
    dataOf(res) { return (res && res.data) || res || {} },
    loadProjects() {
      getProjectList({ pageNo: 1, pageSize: 200 }).then(res => {
        this.projects = this.dataOf(res).list || []
      })
    },
    loadGroups() {
      getInspectionGroupList({ page_size: 200 }).then(res => {
        this.groups = this.dataOf(res).items || []
      })
    },
    onGroupSelect(index) {
      this.query.group_id = index || ''
      this.query.page_no = 1
      this.fetchList()
    },
    fetchList() {
      this.loading = true
      getInspectionTaskList(this.query).then(res => {
        var data = this.dataOf(res)
        this.rows = data.items || []
        this.total = data.total || 0
      }).finally(() => { this.loading = false })
    },
    typeText(type) {
      var map = { auto_case: '自动化', api: '接口', sql: 'SQL', script: '脚本', mixed: '混合' }
      return map[type] || type
    },
    typeTagColor(type) {
      var map = { auto_case: '', api: 'success', sql: 'warning', script: 'info', mixed: 'danger' }
      return map[type] || ''
    },
    openCreate() {
      this.form = { name: '', group_id: this.query.group_id ? Number(this.query.group_id) : '', project_id: '', task_type: 'mixed', schedule_type: 'manual', cron_expression: '', interval_seconds: 3600, notify_webhook: '' }
      this.notifyTypes = []
      this.dialogVisible = true
      this.$nextTick(() => { this.$refs.form && this.$refs.form.clearValidate() })
    },
    openEdit(row) {
      this.form = Object.assign({}, row)
      this.notifyTypes = (row.notify_type || '').split(',').filter(Boolean)
      this.dialogVisible = true
      this.$nextTick(() => { this.$refs.form && this.$refs.form.clearValidate() })
    },
    save() {
      this.$refs.form.validate((valid) => {
        if (!valid) return
        this.form.notify_type = this.notifyTypes.join(',')
        this.saving = true
        var action = this.form.id ? updateInspectionTask(this.form) : createInspectionTask(this.form)
        action.then(() => {
          this.$message.success('保存成功')
          this.dialogVisible = false
          this.fetchList()
        }).finally(() => { this.saving = false })
      })
    },
    onToggle(row) {
      toggleInspectionTask(row.id).then(() => {
        this.$message.success(row.enabled ? '已启用' : '已禁用')
      }).catch(() => { row.enabled = row.enabled ? 0 : 1 })
    },
    executeTask(row) {
      this.$confirm('确定手动执行巡检任务「' + row.name + '」？', '提示', { type: 'info' }).then(() => {
        executeInspectionTask(row.id).then(() => {
          this.$message.success('已提交执行')
        })
      }).catch(() => {})
    },
    remove(row) {
      this.$confirm('确定删除巡检任务「' + row.name + '」？', '提示', { type: 'warning' }).then(() => {
        deleteInspectionTask(row.id).then(() => {
          this.$message.success('删除成功')
          this.fetchList()
        })
      }).catch(() => {})
    }
  }
}
</script>
