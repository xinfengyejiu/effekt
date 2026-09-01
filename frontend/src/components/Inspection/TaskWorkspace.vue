<template>
  <div class="page-wrap task-workspace">
    <el-row :gutter="16">
      <!-- 左侧：任务组 -->
      <el-col :span="8">
        <div class="section-card">
          <div class="section-header">
            <span>任务组</span>
            <el-button type="primary" size="mini" icon="el-icon-plus" @click="openGroupDialog()">新增</el-button>
          </div>
          <el-form inline size="mini" class="filter-form" @submit.native.prevent>
            <el-form-item label="产品">
              <el-select v-model="filterProductId" clearable filterable placeholder="全部" style="width: 120px" @change="onFilterProductChange">
                <el-option v-for="p in products" :key="p.id" :label="p.name" :value="String(p.id)" />
              </el-select>
            </el-form-item>
            <el-form-item label="项目">
              <el-select v-model="filterProjectId" clearable filterable placeholder="全部" style="width: 130px" :disabled="!filterProductId" @change="fetchGroups">
                <el-option v-for="p in filterProjects" :key="p.id" :label="p.name" :value="String(p.id)" />
              </el-select>
            </el-form-item>
          </el-form>
          <div class="group-list" v-loading="groupsLoading">
            <div
              v-for="g in groups"
              :key="g.id"
              class="group-item"
              :class="{ active: selectedGroup && selectedGroup.id === g.id }"
              @click="selectGroup(g)"
            >
              <div class="group-info">
                <span class="group-name">{{ g.name }}</span>
                <div class="group-tags">
                  <el-tag size="mini" type="primary">数据巡检</el-tag>
                  <el-tag size="mini" type="info">{{ scheduleLabel(g) }}</el-tag>
                </div>
              </div>
              <div class="group-meta" @click.stop>
                <el-switch
                  v-model="g.enabled"
                  :active-value="1"
                  :inactive-value="0"
                  @change="toggleGroupEnabled(g)"
                />
                <el-button type="text" size="mini" :loading="g._running" @click="runGroup(g)">执行</el-button>
                <el-button type="text" size="mini" @click="openGroupDialog(g)">编辑</el-button>
                <el-button type="text" size="mini" style="color:#F56C6C" @click="removeGroup(g)">删除</el-button>
              </div>
            </div>
            <el-empty v-if="!groupsLoading && groups.length === 0" description="暂无任务组" :image-size="60" />
          </div>
        </div>
      </el-col>

      <!-- 右侧：任务 + 时间线 -->
      <el-col :span="16">
        <div class="section-card" v-if="selectedGroup">
          <div class="section-header">
            <span>
              任务列表 — {{ selectedGroup.name }}
              <el-tag size="mini" type="primary" style="margin-left:8px">数据巡检</el-tag>
            </span>
            <el-button type="primary" size="mini" icon="el-icon-plus" @click="openTaskDialog()">新增任务</el-button>
          </div>
          <el-table :data="tasks" v-loading="tasksLoading" size="small" stripe border>
            <el-table-column prop="name" label="任务名称" min-width="140" show-overflow-tooltip />
            <el-table-column label="类型" width="100">
              <template slot-scope="scope">
                <el-tag size="mini">{{ typeText(scope.row.task_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template slot-scope="scope">
                <el-switch
                  v-model="scope.row.enabled"
                  :active-value="1"
                  :inactive-value="0"
                  @change="toggleTaskEnabled(scope.row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template slot-scope="scope">
                <el-button type="text" size="mini" @click="openTaskDialog(scope.row)">编辑</el-button>
                <el-button type="text" size="mini" @click="goTaskItems(scope.row)">检查项</el-button>
                <el-button type="text" size="mini" style="color:#F56C6C" @click="removeTask(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="timeline-block">
            <h4>最近执行记录</h4>
            <el-timeline v-if="records.length">
              <el-timeline-item
                v-for="r in records"
                :key="r.id"
                :timestamp="r.start_time || r.created_time"
                placement="top"
                :type="statusTimelineType(r.status)"
              >
                <div class="record-item">
                  <span class="record-name">{{ r.task_name || selectedGroup.name }}</span>
                  <el-tag size="mini" :type="statusTagType(r.status)">{{ statusText(r.status) }}</el-tag>
                  <span class="record-meta">通过 {{ r.pass_count || 0 }}/{{ r.total_count || 0 }}</span>
                  <el-button type="text" size="mini" @click="goExecutionDetail(r)">详情</el-button>
                </div>
              </el-timeline-item>
            </el-timeline>
            <el-empty v-else description="暂无执行记录" :image-size="40" />
          </div>
        </div>
        <el-empty v-else description="请选择一个任务组" />
      </el-col>
    </el-row>

    <!-- 任务组弹窗 -->
    <el-dialog :title="groupForm.id ? '编辑任务组' : '新增任务组'" :visible.sync="groupDialogVisible" width="560px">
      <el-form ref="groupFormRef" :model="groupForm" :rules="groupRules" label-width="100px" size="small">
        <el-form-item label="名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="如：每日接口巡检" />
        </el-form-item>
        <el-form-item label="关联产品" prop="product_id">
          <el-select v-model="groupForm.product_id" filterable clearable placeholder="请选择产品" style="width:100%" @change="onFormProductChange">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="String(p.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联项目" prop="project_id">
          <el-select v-model="groupForm.project_id" filterable clearable :disabled="!groupForm.product_id" placeholder="请先选择产品" style="width:100%">
            <el-option v-for="p in formProjects" :key="p.id" :label="p.name" :value="String(p.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="调度方式">
          <el-radio-group v-model="groupForm.schedule_type">
            <el-radio label="manual">手动</el-radio>
            <el-radio label="cron">Cron</el-radio>
            <el-radio label="interval">间隔</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="groupForm.schedule_type === 'cron'" label="Cron" prop="cron_expression">
          <el-input v-model="groupForm.cron_expression" placeholder="例: 0 9 * * *（每天9点）" />
          <div class="form-hint">格式: 分 时 日 月 周。示例 */30 * * * * 每30分钟</div>
        </el-form-item>
        <el-form-item v-if="groupForm.schedule_type === 'interval'" label="间隔(秒)">
          <el-input-number v-model="groupForm.interval_seconds" :min="60" :step="60" style="width:100%" />
        </el-form-item>
        <el-form-item label="通知渠道">
          <el-checkbox-group v-model="notifyTypes">
            <el-checkbox label="wechat_work">企业微信</el-checkbox>
            <el-checkbox label="dingtalk">钉钉</el-checkbox>
            <el-checkbox label="feishu">飞书</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item v-if="notifyTypes.length" label="Webhook">
          <el-input v-model="groupForm.notify_webhook" placeholder="失败汇总推送地址" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="groupForm.enabled" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="groupDialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="saving" @click="saveGroup">保存</el-button>
      </div>
    </el-dialog>

    <!-- 任务弹窗 -->
    <el-dialog :title="taskForm.id ? '编辑任务' : '新增任务'" :visible.sync="taskDialogVisible" width="520px">
      <el-form ref="taskFormRef" :model="taskForm" :rules="taskRules" label-width="90px" size="small">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" placeholder="如：健康检查接口" />
        </el-form-item>
        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="taskForm.task_type" style="width:100%">
            <el-option label="混合类型" value="mixed" />
            <el-option label="接口巡检" value="api" />
            <el-option label="SQL 巡检" value="sql" />
            <el-option label="脚本巡检" value="script" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="taskForm.enabled" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <div class="form-hint">保存后可在「检查项」中配置采集方式，并用自然语言期望做 AI 判定。</div>
      </el-form>
      <div slot="footer">
        <el-button size="small" @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="saving" @click="saveTask">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  getInspectionGroupList,
  createInspectionGroup,
  updateInspectionGroup,
  deleteInspectionGroup,
  runInspectionGroup,
  getInspectionTaskList,
  createInspectionTask,
  updateInspectionTask,
  deleteInspectionTask,
  getInspectionExecutionList
} from '@/api/inspectionApi'

export default {
  name: 'InspectionTaskWorkspace',
  data () {
    return {
      products: [],
      filterProductId: '',
      filterProjectId: '',
      filterProjects: [],
      formProjects: [],
      groups: [],
      groupsLoading: false,
      selectedGroup: null,
      tasks: [],
      tasksLoading: false,
      records: [],
      saving: false,
      groupDialogVisible: false,
      taskDialogVisible: false,
      notifyTypes: [],
      groupForm: this.emptyGroupForm(),
      taskForm: this.emptyTaskForm(),
      groupRules: {
        name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
        product_id: [{ required: true, message: '请选择产品', trigger: 'change' }],
        project_id: [{ required: true, message: '请选择项目', trigger: 'change' }]
      },
      taskRules: {
        name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
        task_type: [{ required: true, message: '请选择类型', trigger: 'change' }]
      }
    }
  },
  created () {
    this.loadProducts()
    this.fetchGroups()
  },
  methods: {
    emptyGroupForm () {
      return {
        id: null,
        name: '',
        product_id: '',
        project_id: '',
        description: '',
        enabled: 1,
        schedule_type: 'manual',
        cron_expression: '0 9 * * *',
        interval_seconds: 3600,
        notify_webhook: ''
      }
    },
    emptyTaskForm () {
      return {
        id: null,
        name: '',
        task_type: 'api',
        enabled: 1
      }
    },
    dataOf (res) {
      return (res && res.data) || res || {}
    },
    listOf (res) {
      const d = this.dataOf(res)
      return d.list || d.items || d.data || []
    },
    scheduleLabel (g) {
      if (!g) return '手动'
      if (g.schedule_type === 'cron') return g.cron_expression || 'cron'
      if (g.schedule_type === 'interval') return (g.interval_seconds || 0) + 's'
      return '手动'
    },
    typeText (t) {
      return ({ mixed: '混合', api: '接口', sql: 'SQL', script: '脚本', auto_case: '用例' })[t] || t
    },
    statusText (s) {
      return ({ 0: '待执行', 1: '执行中', 2: '全部通过', 3: '部分失败', 4: '全部失败', 5: '异常' })[s] || String(s)
    },
    statusTagType (s) {
      if (s === 2) return 'success'
      if (s === 3) return 'warning'
      if (s === 4 || s === 5) return 'danger'
      return 'info'
    },
    statusTimelineType (s) {
      if (s === 2) return 'success'
      if (s === 3) return 'warning'
      if (s === 4 || s === 5) return 'danger'
      return 'primary'
    },
    loadProducts () {
      return getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        this.products = this.listOf(res)
      })
    },
    loadProjectsByProduct (productId) {
      if (!productId) return Promise.resolve([])
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => this.listOf(res))
    },
    onFilterProductChange (productId) {
      this.filterProjectId = ''
      this.filterProjects = []
      if (!productId) {
        this.fetchGroups()
        return
      }
      this.loadProjectsByProduct(productId).then(rows => {
        this.filterProjects = rows
        this.fetchGroups()
      })
    },
    onFormProductChange (productId) {
      this.groupForm.project_id = ''
      this.formProjects = []
      if (!productId) return
      this.loadProjectsByProduct(productId).then(rows => {
        this.formProjects = rows
      })
    },
    fetchGroups () {
      this.groupsLoading = true
      const params = { page_no: 1, page_size: 200 }
      if (this.filterProjectId) params.project_id = this.filterProjectId
      getInspectionGroupList(params).then(res => {
        const data = this.dataOf(res)
        this.groups = data.items || data.list || []
        if (this.selectedGroup) {
          const found = this.groups.find(g => g.id === this.selectedGroup.id)
          if (found) this.selectedGroup = found
          else {
            this.selectedGroup = null
            this.tasks = []
            this.records = []
          }
        }
      }).finally(() => {
        this.groupsLoading = false
      })
    },
    selectGroup (g) {
      this.selectedGroup = g
      this.fetchTasks()
      this.fetchRecords()
    },
    fetchTasks () {
      if (!this.selectedGroup) return
      this.tasksLoading = true
      getInspectionTaskList({
        group_id: this.selectedGroup.id,
        page_no: 1,
        page_size: 100
      }).then(res => {
        const data = this.dataOf(res)
        this.tasks = data.items || data.list || []
      }).finally(() => {
        this.tasksLoading = false
      })
    },
    fetchRecords () {
      if (!this.selectedGroup) return
      getInspectionExecutionList({
        group_id: this.selectedGroup.id,
        page_no: 1,
        page_size: 15
      }).then(res => {
        const data = this.dataOf(res)
        this.records = data.items || data.list || []
      })
    },
    openGroupDialog (row) {
      this.notifyTypes = []
      this.formProjects = []
      if (row) {
        this.groupForm = {
          id: row.id,
          name: row.name,
          product_id: '',
          project_id: row.project_id != null ? String(row.project_id) : '',
          description: row.description || '',
          enabled: row.enabled == null ? 1 : row.enabled,
          schedule_type: row.schedule_type || 'manual',
          cron_expression: row.cron_expression || '0 9 * * *',
          interval_seconds: row.interval_seconds || 3600,
          notify_webhook: row.notify_webhook || ''
        }
        this.notifyTypes = (row.notify_type || '').split(',').map(s => s.trim()).filter(Boolean)
        getProjectList({ pageNo: 1, pageSize: 1000 }).then(res => {
          const all = this.listOf(res)
          const proj = all.find(item => String(item.id) === String(row.project_id))
          if (!proj) return
          this.groupForm.product_id = String(proj.product_id || proj.productId || '')
          return this.loadProjectsByProduct(this.groupForm.product_id).then(rows => {
            this.formProjects = rows
          })
        })
      } else {
        this.groupForm = this.emptyGroupForm()
      }
      this.groupDialogVisible = true
      this.$nextTick(() => {
        this.$refs.groupFormRef && this.$refs.groupFormRef.clearValidate()
      })
    },
    saveGroup () {
      this.$refs.groupFormRef.validate(valid => {
        if (!valid) return
        this.saving = true
        const payload = Object.assign({}, this.groupForm, {
          project_id: Number(this.groupForm.project_id) || this.groupForm.project_id,
          notify_type: this.notifyTypes.join(','),
          notify_webhook: this.notifyTypes.length ? this.groupForm.notify_webhook : ''
        })
        delete payload.product_id
        const action = payload.id ? updateInspectionGroup(payload) : createInspectionGroup(payload)
        action.then(() => {
          this.$message.success('保存成功')
          this.groupDialogVisible = false
          this.fetchGroups()
        }).catch(err => {
          this.$message.error((err && err.message) || '保存失败')
        }).finally(() => {
          this.saving = false
        })
      })
    },
    toggleGroupEnabled (g) {
      updateInspectionGroup({ id: g.id, enabled: g.enabled }).then(() => {
        this.$message.success(g.enabled === 1 ? '已启用' : '已停用')
      }).catch(() => {
        g.enabled = g.enabled === 1 ? 0 : 1
        this.$message.error('更新失败')
      })
    },
    runGroup (g) {
      this.$set(g, '_running', true)
      runInspectionGroup(g.id).then(() => {
        this.$message.success('已触发组执行')
        if (this.selectedGroup && this.selectedGroup.id === g.id) {
          setTimeout(() => this.fetchRecords(), 1500)
        }
      }).catch(err => {
        this.$message.error((err && err.message) || '执行失败')
      }).finally(() => {
        this.$set(g, '_running', false)
      })
    },
    removeGroup (g) {
      this.$confirm('确定删除任务组「' + g.name + '」？', '提示', { type: 'warning' }).then(() => {
        deleteInspectionGroup(g.id).then(() => {
          this.$message.success('删除成功')
          if (this.selectedGroup && this.selectedGroup.id === g.id) {
            this.selectedGroup = null
            this.tasks = []
            this.records = []
          }
          this.fetchGroups()
        })
      }).catch(() => {})
    },
    openTaskDialog (row) {
      if (!this.selectedGroup) return
      if (row) {
        this.taskForm = {
          id: row.id,
          name: row.name,
          task_type: row.task_type || 'api',
          enabled: row.enabled == null ? 1 : row.enabled
        }
      } else {
        this.taskForm = this.emptyTaskForm()
      }
      this.taskDialogVisible = true
      this.$nextTick(() => {
        this.$refs.taskFormRef && this.$refs.taskFormRef.clearValidate()
      })
    },
    saveTask () {
      this.$refs.taskFormRef.validate(valid => {
        if (!valid) return
        this.saving = true
        const payload = {
          id: this.taskForm.id,
          name: this.taskForm.name,
          task_type: this.taskForm.task_type,
          enabled: this.taskForm.enabled,
          group_id: this.selectedGroup.id,
          project_id: this.selectedGroup.project_id,
          schedule_type: 'manual'
        }
        const action = payload.id ? updateInspectionTask(payload) : createInspectionTask(payload)
        action.then(() => {
          this.$message.success('保存成功')
          this.taskDialogVisible = false
          this.fetchTasks()
        }).catch(err => {
          this.$message.error((err && err.message) || '保存失败')
        }).finally(() => {
          this.saving = false
        })
      })
    },
    toggleTaskEnabled (row) {
      updateInspectionTask({ id: row.id, enabled: row.enabled }).catch(() => {
        row.enabled = row.enabled === 1 ? 0 : 1
        this.$message.error('更新失败')
      })
    },
    removeTask (row) {
      this.$confirm('确定删除任务「' + row.name + '」？', '提示', { type: 'warning' }).then(() => {
        deleteInspectionTask(row.id).then(() => {
          this.$message.success('删除成功')
          this.fetchTasks()
        })
      }).catch(() => {})
    },
    goTaskItems (row) {
      this.$router.push({ path: '/inspection/task/edit', query: { id: row.id } })
    },
    goExecutionDetail (r) {
      this.$router.push({ path: '/inspection/execution/detail', query: { id: r.id } })
    }
  }
}
</script>

<style scoped>
.task-workspace {
  padding: 4px;
}
.section-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px 14px;
  min-height: 560px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  font-weight: 600;
}
.filter-form {
  margin-bottom: 8px;
}
.group-list {
  max-height: 480px;
  overflow-y: auto;
}
.group-item {
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: border-color .15s, background .15s;
}
.group-item:hover,
.group-item.active {
  border-color: #409EFF;
  background: #f5f9ff;
}
.group-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.group-name {
  font-weight: 600;
  color: #303133;
}
.group-tags {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}
.group-meta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.timeline-block {
  margin-top: 20px;
}
.timeline-block h4 {
  margin: 0 0 10px;
  font-size: 14px;
}
.record-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.record-name {
  font-weight: 500;
}
.record-meta {
  color: #909399;
  font-size: 12px;
}
.form-hint {
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
  margin-top: 4px;
}
</style>
