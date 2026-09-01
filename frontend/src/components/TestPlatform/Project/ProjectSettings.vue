<template>
  <div class="page-wrap">
    <page-section title="项目设置">
      <template slot="extra">
        <el-button size="small" @click="goBackToList">返回</el-button>
      </template>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="项目成员" name="members">
          <div class="toolbar-wrap">
            <el-button type="primary" size="small" @click="openMemberDialog">新增成员</el-button>
          </div>
          <el-table :data="members" border>
            <el-table-column prop="project_name" label="项目名称"></el-table-column>
            <el-table-column prop="username" label="用户名"></el-table-column>
            <el-table-column prop="role_name" label="角色"></el-table-column>
            <el-table-column prop="joined_time" label="加入时间"></el-table-column>
          </el-table>
          <div style="margin-top: 16px; text-align: right;">
            <el-pagination
              :current-page="memberPageNo"
              :page-size="memberPageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="memberTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleMemberSizeChange"
              @current-change="handleMemberCurrentChange">
            </el-pagination>
          </div>
        </el-tab-pane>
        <el-tab-pane label="环境配置" name="environments">
          <div class="toolbar-wrap">
            <el-button type="primary" size="small" @click="openEnvironmentDialog">新增环境</el-button>
          </div>
          <el-table :data="environments" border>
            <el-table-column prop="name" label="环境"></el-table-column>
            <el-table-column prop="variables" label="变量">
              <template slot-scope="scope">
                <json-viewer :value="scope.row.variables"></json-viewer>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 16px; text-align: right;">
            <el-pagination
              :current-page="environmentPageNo"
              :page-size="environmentPageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="environmentTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleEnvironmentSizeChange"
              @current-change="handleEnvironmentCurrentChange">
            </el-pagination>
          </div>
        </el-tab-pane>
        <el-tab-pane label="Hook 配置" name="hooks">
          <div class="toolbar-wrap hook-toolbar">
            <div class="hook-toolbar-left">
              <el-select
                v-model="hookTypeFilter"
                clearable
                placeholder="Hook 类型"
                size="small"
                style="width: 140px;"
                @change="onHookTypeFilterChange">
                <el-option label="飞书" :value="1" />
                <el-option label="钉钉" :value="2" />
                <el-option label="企微" :value="3" />
              </el-select>
            </div>
            <el-button type="primary" size="small" @click="openHookDialog('create')">新增 Hook</el-button>
          </div>
          <el-table v-loading="hookLoading" :data="hooks" border>
            <el-table-column prop="hook_type_name" label="类型" width="100">
              <template slot-scope="scope">{{ scope.row.hook_type_name || hookTypeLabel(scope.row.hook_type) }}</template>
            </el-table-column>
            <el-table-column label="Webhook" min-width="220" show-overflow-tooltip>
              <template slot-scope="scope">{{ scope.row.webhook_url || scope.row.webhookUrl || '-' }}</template>
            </el-table-column>
            <el-table-column label="启用" width="80">
              <template slot-scope="scope">
                <el-tag size="mini" :type="(scope.row.enabled === 1 || scope.row.enabled === true) ? 'success' : 'info'">
                  {{ (scope.row.enabled === 1 || scope.row.enabled === true) ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="140" show-overflow-tooltip />
            <el-table-column label="创建时间" width="170">
              <template slot-scope="scope">{{ scope.row.created_time || scope.row.createdTime || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template slot-scope="scope">
                <el-button type="text" size="small" @click="openHookDialog('edit', scope.row)">编辑</el-button>
                <el-button type="text" size="small" style="color: #f56c6c;" @click="handleHookDelete(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 16px; text-align: right;">
            <el-pagination
              :current-page="hookPageNo"
              :page-size="hookPageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="hookTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleHookSizeChange"
              @current-change="handleHookCurrentChange">
            </el-pagination>
          </div>
        </el-tab-pane>
        <el-tab-pane label="代码转 PRD" name="codePrd">
          <div class="code-prd-config">
            <el-form ref="codePrdConfigForm" :model="codePrdConfig" :rules="codePrdRules" label-width="110px" size="small" class="code-prd-form">
              <el-form-item label="Git仓库地址" prop="repoUrl">
                <el-input v-model.trim="codePrdConfig.repoUrl" placeholder="https://example.com/group/repo.git 或 git@example.com:group/repo.git" />
              </el-form-item>
              <el-form-item label="默认分支" prop="defaultBranch">
                <el-select v-model="codePrdConfig.defaultBranch" filterable allow-create default-first-option placeholder="请选择或输入分支" style="width: 100%;" @focus="loadCodePrdBranches">
                  <el-option v-for="branch in codePrdBranches" :key="branch" :label="branch" :value="branch" />
                </el-select>
              </el-form-item>
              <el-form-item>
                <el-button size="small" :loading="codePrdBranchLoading" @click="loadCodePrdBranches">获取分支</el-button>
                <el-button type="primary" size="small" :loading="codePrdConfigSaving" @click="saveCodePrdConfig">保存配置</el-button>
              </el-form-item>
            </el-form>
          </div>
          <div class="code-prd-prompt-wrap">
            <el-input
              v-model="codePrdPromptAppend"
              type="textarea"
              :rows="3"
              maxlength="2000"
              show-word-limit
              placeholder="请输入本次生成 PRD 的补充提示词，例如重点分析某个业务流程、补充特定角色视角或输出格式要求" />
          </div>
          <div class="toolbar-wrap hook-toolbar">
            <div class="hook-toolbar-left">
              <el-select v-model="codePrdGenerateBranch" filterable placeholder="选择生成分支" size="small" style="width: 220px;" @focus="loadCodePrdBranches">
                <el-option v-for="branch in codePrdBranches" :key="branch" :label="branch" :value="branch" />
              </el-select>
            </div>
            <el-button type="primary" size="small" :loading="codePrdGenerating" @click="generateCodePrd">生成 PRD</el-button>
          </div>
          <div v-if="codePrdProgressVisible" class="code-prd-progress-wrap">
            <div class="code-prd-progress-head">
              <span>{{ codePrdProgressTitle }}</span>
              <span class="code-prd-progress-status">{{ codePrdProgressText }}</span>
            </div>
            <el-progress
              :percentage="codePrdProgressPercent"
              :status="codePrdProgressStatus"
              :stroke-width="8" />
          </div>
          <el-table v-loading="codePrdLoading" :data="codePrdRecords" border>
            <el-table-column prop="title" label="文档标题" min-width="180" show-overflow-tooltip />
            <el-table-column prop="repo_url" label="仓库地址" min-width="220" show-overflow-tooltip />
            <el-table-column prop="branch" label="分支" width="140" show-overflow-tooltip />
            <el-table-column label="状态" width="100">
              <template slot-scope="scope">
                <el-tag size="mini" :type="codePrdStatusType(scope.row.status)">{{ codePrdStatusLabel(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="创建时间" width="170">
              <template slot-scope="scope">{{ scope.row.created_time || scope.row.createdTime || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template slot-scope="scope">
                <el-button type="text" size="small" @click="openCodePrdDetail(scope.row)">{{ Number(scope.row.status) === 3 ? '查看错误' : '查看' }}</el-button>
                <el-button type="text" size="small" :disabled="Number(scope.row.status) !== 2" @click="downloadCodePrdDocx(scope.row)">导出docx</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 16px; text-align: right;">
            <el-pagination
              :current-page="codePrdPageNo"
              :page-size="codePrdPageSize"
              :page-sizes="[10, 20, 50]"
              :total="codePrdTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleCodePrdSizeChange"
              @current-change="handleCodePrdCurrentChange">
            </el-pagination>
          </div>
        </el-tab-pane>
      </el-tabs>
    </page-section>

    <el-dialog title="新增成员" :visible.sync="memberDialogVisible" width="520px" @close="resetMemberForm">
      <el-form ref="memberForm" :model="memberForm" :rules="memberRules" label-width="94px" size="small">
        <el-form-item label="选择用户" prop="user_ids">
          <el-select
            v-model="memberForm.user_ids"
            multiple
            filterable
            placeholder="请选择用户"
            style="width: 100%;"
            @focus="loadUserOptions">
            <el-option
              v-for="item in userOptions"
              :key="item.id"
              :label="item.username + (item.real_name ? ' (' + item.real_name + ')' : '')"
              :value="item.id">
            </el-option>
            <el-option v-if="userHasMore" disabled style="text-align: center;">
              <span v-if="userLoading">加载中...</span>
              <span v-else @click.stop="loadMoreUsers">加载更多</span>
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button size="small" @click="memberDialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="memberSubmitting" @click="submitMember">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="新增环境" :visible.sync="environmentDialogVisible" width="520px" @close="resetEnvironmentForm">
      <el-form ref="environmentForm" :model="environmentForm" :rules="environmentRules" label-width="94px" size="small">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model.trim="environmentForm.name" maxlength="64" placeholder="请输入环境名称"></el-input>
        </el-form-item>
        <el-form-item label="变量JSON" prop="variablesText">
          <el-input v-model.trim="environmentForm.variablesText" type="textarea" :rows="6" placeholder='请输入 JSON，例如 {"baseUrl":"https://test.com"}'></el-input>
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button size="small" @click="environmentDialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="environmentSubmitting" @click="submitEnvironment">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog
      :title="hookDialogMode === 'create' ? '新增 Hook' : '编辑 Hook'"
      :visible.sync="hookDialogVisible"
      width="560px"
      @close="resetHookForm">
      <el-form ref="hookFormRef" :model="hookForm" :rules="hookRules" label-width="100px" size="small">
        <el-form-item label="Hook 类型" prop="hookType">
          <el-select v-model="hookForm.hookType" placeholder="请选择" style="width: 100%;" :disabled="hookDialogMode === 'edit'">
            <el-option label="飞书" :value="1" />
            <el-option label="钉钉" :value="2" />
            <el-option label="企微" :value="3" />
          </el-select>
        </el-form-item>
        <el-form-item label="Webhook" prop="webhookUrl">
          <el-input v-model.trim="hookForm.webhookUrl" type="textarea" :rows="2" placeholder="Webhook 地址" />
        </el-form-item>
        <el-form-item label="签名密钥" prop="secret">
          <el-input v-model.trim="hookForm.secret" show-password placeholder="可选，飞书/钉钉等签名校验用" />
        </el-form-item>
        <el-form-item label="启用" prop="enabled">
          <el-switch v-model="hookForm.enabled" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model.trim="hookForm.description" maxlength="200" show-word-limit placeholder="说明用途" />
        </el-form-item>
        <el-form-item label="扩展配置" prop="configText">
          <el-input v-model.trim="hookForm.configText" type="textarea" :rows="4" placeholder='JSON，默认 {}' />
        </el-form-item>
      </el-form>
      <span slot="footer">
        <el-button size="small" @click="hookDialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="hookSubmitting" @click="submitHook">确定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="代码转 PRD" :visible.sync="codePrdDetailVisible" width="780px" class="code-prd-detail-dialog">
      <div v-loading="codePrdDetailLoading">
        <div v-if="codePrdDetail.error_message" class="code-prd-error">{{ codePrdDetail.error_message }}</div>
        <pre class="code-prd-markdown">{{ codePrdDetail.prd_markdown || codePrdDetail.prdMarkdown || '暂无PRD内容' }}</pre>
      </div>
      <span slot="footer">
        <el-button size="small" @click="codePrdDetailVisible = false">关闭</el-button>
        <el-button type="primary" size="small" :disabled="Number(codePrdDetail.status) !== 2" @click="downloadCodePrdDocx(codePrdDetail)">导出docx</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import JsonViewer from '@/components/TestPlatform/common/JsonViewer'
import {
  createEnvironment,
  createProjectMember,
  createProjectHook,
  deleteProjectHook,
  getProjectEnvironments,
  getProjectHookDetail,
  getProjectHookList,
  getProjectMembers,
  getProjectCodePrdBranches,
  getProjectCodePrdConfig,
  getProjectCodePrdDetail,
  getProjectCodePrdList,
  generateProjectCodePrd,
  exportProjectCodePrdDocx,
  saveProjectCodePrdConfig,
  updateProjectHook
} from '@/api/projectApi'
import { getUserList } from '@/api/rbacApi'

const getDefaultMemberForm = () => ({
  user_ids: []
})

const getDefaultEnvironmentForm = () => ({
  name: '',
  variablesText: '{}'
})

const getDefaultHookForm = () => ({
  hookId: null,
  hookType: 1,
  webhookUrl: '',
  secret: '',
  enabled: 1,
  description: '',
  configText: '{}'
})

const getDefaultCodePrdConfig = () => ({
  repoUrl: '',
  defaultBranch: ''
})

export default {
  name: 'ProjectSettings',
  components: { PageSection, JsonViewer },
  data() {
    return {
      activeTab: 'members',
      memberPageNo: 1,
      memberPageSize: 10,
      memberTotal: 0,
      environmentPageNo: 1,
      environmentPageSize: 10,
      environmentTotal: 0,
      members: [],
      environments: [],
      memberDialogVisible: false,
      environmentDialogVisible: false,
      memberSubmitting: false,
      environmentSubmitting: false,
      memberForm: getDefaultMemberForm(),
      environmentForm: getDefaultEnvironmentForm(),
      memberRules: {
        user_ids: [{ required: true, message: '请选择用户', trigger: 'change' }]
      },
      environmentRules: {
        name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }],
        variablesText: [{ required: true, message: '请输入变量JSON', trigger: 'blur' }]
      },
      userOptions: [],
      userLoading: false,
      userPageNo: 1,
      userPageSize: 10,
      userTotal: 0,
      userHasMore: false,
      hooks: [],
      hookPageNo: 1,
      hookPageSize: 10,
      hookTotal: 0,
      hookLoading: false,
      hookTypeFilter: '',
      hookDialogVisible: false,
      hookDialogMode: 'create',
      hookSubmitting: false,
      hookForm: getDefaultHookForm(),
      hookRules: {
        hookType: [{ required: true, message: '请选择类型', trigger: 'change' }],
        webhookUrl: [{ required: true, message: '请输入 Webhook 地址', trigger: 'blur' }],
        configText: [
          {
            validator: (rule, value, callback) => {
              const s = (value || '').trim()
              if (!s) {
                callback()
                return
              }
              try {
                JSON.parse(s)
                callback()
              } catch (e) {
                callback(new Error('扩展配置须为合法 JSON'))
              }
            },
            trigger: 'blur'
          }
        ]
      },
      codePrdConfig: getDefaultCodePrdConfig(),
      codePrdRules: {
        repoUrl: [{ required: true, message: '请输入Git仓库地址', trigger: 'blur' }],
        defaultBranch: [{ required: true, message: '请选择默认分支', trigger: 'change' }]
      },
      codePrdBranches: [],
      codePrdBranchLoading: false,
      codePrdConfigSaving: false,
      codePrdGenerating: false,
      codePrdLoading: false,
      codePrdRecords: [],
      codePrdPageNo: 1,
      codePrdPageSize: 10,
      codePrdTotal: 0,
      codePrdGenerateBranch: '',
      codePrdPromptAppend: '',
      codePrdRefreshTimer: null,
      codePrdActiveRecordId: null,
      codePrdProgressVisible: false,
      codePrdProgressPercent: 0,
      codePrdProgressText: '',
      codePrdProgressTitle: 'PRD生成进度',
      codePrdProgressStatus: null,
      codePrdDetailVisible: false,
      codePrdDetailLoading: false,
      codePrdDetail: {}
    }
  },
  methods: {
    goBackToList() {
      this.$router.push({ path: '/test-platform/project' })
    },
    getProjectId() {
      return this.$route.query.projectId || 1
    },
    hookTypeLabel(type) {
      const map = { 1: '飞书', 2: '钉钉', 3: '企微' }
      return map[Number(type)] || type || '-'
    },
    onHookTypeFilterChange() {
      this.hookPageNo = 1
      this.fetchHooks()
    },
    fetchHooks() {
      const projectId = this.getProjectId()
      this.hookLoading = true
      const params = {
        projectId,
        pageNo: this.hookPageNo,
        pageSize: this.hookPageSize
      }
      if (this.hookTypeFilter !== '' && this.hookTypeFilter !== null && this.hookTypeFilter !== undefined) {
        params.hookType = this.hookTypeFilter
      }
      getProjectHookList(params)
        .then(res => {
          const data = (res && res.data) || res || {}
          const list = data.list || data.items || []
          this.hooks = Array.isArray(list) ? list : []
          this.hookTotal = Number(data.total != null ? data.total : this.hooks.length)
        })
        .catch(() => {
          this.hooks = []
          this.hookTotal = 0
        })
        .finally(() => {
          this.hookLoading = false
        })
    },
    openHookDialog(mode, row) {
      this.hookDialogMode = mode
      if (mode === 'create') {
        this.hookForm = getDefaultHookForm()
        this.hookDialogVisible = true
        this.$nextTick(() => {
          if (this.$refs.hookFormRef) this.$refs.hookFormRef.clearValidate()
        })
        return
      }
      const id = row && (row.id != null ? row.id : row.hookId)
      if (id == null) {
        this.$message.warning('缺少 Hook ID')
        return
      }
      getProjectHookDetail(id)
        .then(res => {
          const d = (res && res.data) || res || {}
          const cfg = d.config
          let configText = '{}'
          if (cfg != null && typeof cfg === 'object') {
            try {
              configText = JSON.stringify(cfg, null, 0)
            } catch (e) {
              configText = '{}'
            }
          } else if (typeof cfg === 'string' && cfg.trim()) {
            configText = cfg.trim()
          }
          this.hookForm = {
            hookId: d.id,
            hookType: d.hook_type != null ? d.hook_type : d.hookType,
            webhookUrl: d.webhook_url || d.webhookUrl || '',
            secret: d.secret != null ? String(d.secret) : '',
            enabled: d.enabled === 0 || d.enabled === false ? 0 : 1,
            description: d.description || '',
            configText
          }
          this.hookDialogVisible = true
          this.$nextTick(() => {
            if (this.$refs.hookFormRef) this.$refs.hookFormRef.clearValidate()
          })
        })
        .catch(() => {})
    },
    resetHookForm() {
      this.hookForm = getDefaultHookForm()
      this.hookSubmitting = false
      this.$nextTick(() => {
        if (this.$refs.hookFormRef) this.$refs.hookFormRef.resetFields()
      })
    },
    submitHook() {
      this.$refs.hookFormRef.validate(valid => {
        if (!valid) return
        let config = {}
        const ct = (this.hookForm.configText || '').trim()
        if (ct) {
          try {
            config = JSON.parse(ct)
          } catch (e) {
            this.$message.error('扩展配置 JSON 无效')
            return
          }
        }
        this.hookSubmitting = true
        const done = () => {
          this.hookDialogVisible = false
          this.hookPageNo = 1
          this.fetchHooks()
        }
        if (this.hookDialogMode === 'create') {
          createProjectHook({
            projectId: Number(this.getProjectId()),
            hookType: this.hookForm.hookType,
            webhookUrl: this.hookForm.webhookUrl,
            secret: this.hookForm.secret || undefined,
            enabled: this.hookForm.enabled,
            description: this.hookForm.description || undefined,
            config
          })
            .then(res => {
              if (res && res.code === 20000) {
                this.$message.success((res && res.message) || '创建成功')
                done()
              } else {
                this.$message.error((res && res.message) || '创建失败')
              }
            })
            .finally(() => {
              this.hookSubmitting = false
            })
          return
        }
        const payload = {
          hookId: this.hookForm.hookId,
          hookType: this.hookForm.hookType,
          webhookUrl: this.hookForm.webhookUrl,
          enabled: this.hookForm.enabled,
          description: this.hookForm.description || undefined,
          config
        }
        if (String(this.hookForm.secret || '').trim() !== '') {
          payload.secret = this.hookForm.secret
        }
        updateProjectHook(payload)
          .then(res => {
            if (res && res.code === 20000) {
              this.$message.success((res && res.message) || '更新成功')
              done()
            } else {
              this.$message.error((res && res.message) || '更新失败')
            }
          })
          .finally(() => {
            this.hookSubmitting = false
          })
      })
    },
    handleHookDelete(row) {
      const id = row && (row.id != null ? row.id : row.hookId)
      if (id == null) {
        this.$message.warning('缺少 Hook ID')
        return
      }
      this.$confirm('确认删除该 Hook 配置？', '提示', { type: 'warning' })
        .then(() => deleteProjectHook({ hookId: id }))
        .then(res => {
          if (res && res.code === 20000) {
            this.$message.success((res && res.message) || '已删除')
            this.hookPageNo = 1
            this.fetchHooks()
          } else {
            this.$message.error((res && res.message) || '删除失败')
          }
        })
        .catch(() => {})
    },
    handleHookSizeChange(val) {
      this.hookPageSize = val
      this.hookPageNo = 1
      this.fetchHooks()
    },
    handleHookCurrentChange(val) {
      this.hookPageNo = val
      this.fetchHooks()
    },
    codePrdStatusLabel(status) {
      const map = { 0: '待生成', 1: '生成中', 2: '成功', 3: '失败' }
      return map[Number(status)] || '-'
    },
    codePrdStatusType(status) {
      const map = { 0: 'info', 1: 'warning', 2: 'success', 3: 'danger' }
      return map[Number(status)] || 'info'
    },
    fetchCodePrdConfig() {
      return getProjectCodePrdConfig({ projectId: this.getProjectId() }).then(res => {
        const data = (res && res.data) || res || {}
        this.codePrdConfig = {
          repoUrl: data.repo_url || data.repoUrl || '',
          defaultBranch: data.default_branch || data.defaultBranch || ''
        }
        this.codePrdGenerateBranch = this.codePrdConfig.defaultBranch
      }).catch(() => {
        this.codePrdConfig = getDefaultCodePrdConfig()
      })
    },
    loadCodePrdBranches() {
      if (!this.codePrdConfig.repoUrl) {
        this.$message.warning('请先填写Git仓库地址')
        return
      }
      this.codePrdBranchLoading = true
      getProjectCodePrdBranches({ projectId: this.getProjectId(), repoUrl: this.codePrdConfig.repoUrl })
        .then(res => {
          const data = (res && res.data) || res || {}
          this.codePrdBranches = data.list || data.items || []
          if (!this.codePrdGenerateBranch && this.codePrdConfig.defaultBranch) {
            this.codePrdGenerateBranch = this.codePrdConfig.defaultBranch
          }
        })
        .finally(() => {
          this.codePrdBranchLoading = false
        })
    },
    saveCodePrdConfig() {
      this.$refs.codePrdConfigForm.validate(valid => {
        if (!valid) return
        this.codePrdConfigSaving = true
        saveProjectCodePrdConfig({
          projectId: Number(this.getProjectId()),
          repoUrl: this.codePrdConfig.repoUrl,
          defaultBranch: this.codePrdConfig.defaultBranch
        }).then(() => {
          this.$message.success('配置已保存')
          this.codePrdGenerateBranch = this.codePrdConfig.defaultBranch
          this.loadCodePrdBranches()
        }).finally(() => {
          this.codePrdConfigSaving = false
        })
      })
    },
    scheduleCodePrdRefresh() {
      if (this.codePrdRefreshTimer) {
        clearTimeout(this.codePrdRefreshTimer)
        this.codePrdRefreshTimer = null
      }
      const activeRecord = this.codePrdActiveRecordId
        ? this.codePrdRecords.find(item => String(item.id || item.recordId) === String(this.codePrdActiveRecordId))
        : null
      const hasRunningRecord = this.codePrdRecords.some(item => Number(item.status) === 1)
      const activeStatus = activeRecord ? Number(activeRecord.status) : null
      const shouldRefresh = hasRunningRecord || activeStatus === 0 || activeStatus === 1 || (this.codePrdProgressVisible && this.codePrdProgressPercent < 100)
      if (!shouldRefresh) {
        return
      }
      this.codePrdRefreshTimer = setTimeout(() => {
        this.fetchCodePrdRecords(true)
      }, 5000)
    },
    startCodePrdProgress(recordId) {
      this.codePrdActiveRecordId = recordId || null
      this.codePrdProgressVisible = true
      this.codePrdProgressPercent = 10
      this.codePrdProgressStatus = null
      this.codePrdProgressTitle = 'PRD生成进度'
      this.codePrdProgressText = '任务已创建，等待后台开始生成'
    },
    syncCodePrdProgress() {
      const activeRecord = this.codePrdActiveRecordId
        ? this.codePrdRecords.find(item => String(item.id || item.recordId) === String(this.codePrdActiveRecordId))
        : this.codePrdRecords.find(item => Number(item.status) === 1)
      if (!activeRecord) {
        return
      }
      this.codePrdActiveRecordId = activeRecord.id || activeRecord.recordId || this.codePrdActiveRecordId
      this.codePrdProgressVisible = true
      const status = Number(activeRecord.status)
      if (status === 0) {
        this.codePrdProgressStatus = null
        this.codePrdProgressPercent = Math.max(this.codePrdProgressPercent, 15)
        this.codePrdProgressText = '任务已创建，等待后台开始生成'
        return
      }
      if (status === 1) {
        this.codePrdProgressStatus = null
        this.codePrdProgressPercent = Math.min(Math.max(this.codePrdProgressPercent, 35) + 8, 90)
        this.codePrdProgressText = '正在拉取代码、分析仓库并调用大模型生成 PRD'
        return
      }
      if (status === 2) {
        this.codePrdProgressPercent = 100
        this.codePrdProgressStatus = 'success'
        this.codePrdProgressText = '生成完成，可查看或导出 docx'
        return
      }
      if (status === 3) {
        this.codePrdProgressPercent = 100
        this.codePrdProgressStatus = 'exception'
        this.codePrdProgressText = '生成失败，请查看错误信息'
      }
    },
    fetchCodePrdRecords(silent) {
      if (!silent) {
        this.codePrdLoading = true
      }
      getProjectCodePrdList({
        projectId: this.getProjectId(),
        pageNo: this.codePrdPageNo,
        pageSize: this.codePrdPageSize
      }).then(res => {
        const data = (res && res.data) || res || {}
        this.codePrdRecords = data.list || data.items || []
        this.codePrdTotal = data.total || data.totalCount || this.codePrdRecords.length
        this.syncCodePrdProgress()
        this.scheduleCodePrdRefresh()
      }).catch(() => {
        this.codePrdRecords = []
        this.codePrdTotal = 0
      }).finally(() => {
        this.codePrdLoading = false
      })
    },
    generateCodePrd() {
      if (!this.codePrdConfig.repoUrl) {
        this.$message.warning('请先配置Git仓库地址')
        return
      }
      if (!this.codePrdGenerateBranch) {
        this.$message.warning('请选择Git分支')
        return
      }
      this.codePrdGenerating = true
      generateProjectCodePrd({
        projectId: Number(this.getProjectId()),
        repoUrl: this.codePrdConfig.repoUrl,
        branch: this.codePrdGenerateBranch,
        promptAppend: this.codePrdPromptAppend
      }).then(res => {
        const data = (res && res.data) || {}
        this.$message.success('PRD生成任务已启动，正在拉取代码并调用大模型')
        this.startCodePrdProgress(data.id || data.recordId || res.id || res.recordId)
        this.codePrdPageNo = 1
        this.fetchCodePrdRecords()
      }).catch(() => {
        this.codePrdProgressVisible = true
        this.codePrdProgressPercent = 100
        this.codePrdProgressStatus = 'exception'
        this.codePrdProgressText = '任务启动失败，请稍后重试'
        this.fetchCodePrdRecords()
      }).finally(() => {
        this.codePrdGenerating = false
      })
    },
    openCodePrdDetail(row) {
      const id = row && (row.id || row.recordId)
      if (!id) return
      this.codePrdDetailVisible = true
      this.codePrdDetailLoading = true
      getProjectCodePrdDetail({ recordId: id }).then(res => {
        this.codePrdDetail = (res && res.data) || res || {}
      }).finally(() => {
        this.codePrdDetailLoading = false
      })
    },
    downloadCodePrdDocx(row) {
      const id = row && (row.id || row.recordId)
      if (!id) return
      exportProjectCodePrdDocx({ recordId: id }).then(blob => {
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'code-prd-' + id + '.docx'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      })
    },
    handleCodePrdSizeChange(val) {
      this.codePrdPageSize = val
      this.codePrdPageNo = 1
      this.fetchCodePrdRecords()
    },
    handleCodePrdCurrentChange(val) {
      this.codePrdPageNo = val
      this.fetchCodePrdRecords()
    },
    fetchData() {
      const projectId = this.getProjectId()
      getProjectMembers(projectId, {
        pageNo: this.memberPageNo,
        pageSize: this.memberPageSize
      }).then(res => {
        const data = (res && res.data) || res || []
        this.members = data.items || data.list || data.data || data || []
        this.memberTotal = data.total || data.totalCount || this.members.length
      }).catch(() => {
        this.members = []
        this.memberTotal = 0
      })
      getProjectEnvironments(projectId, {
        pageNo: this.environmentPageNo,
        pageSize: this.environmentPageSize
      }).then(res => {
        const data = (res && res.data) || res || []
        this.environments = data.items || data.list || data.data || data || []
        this.environmentTotal = data.total || data.totalCount || this.environments.length
      }).catch(() => {
        this.environments = []
        this.environmentTotal = 0
      })
    },
    openMemberDialog() {
      this.memberDialogVisible = true
      this.userOptions = []
      this.userPageNo = 1
      this.userHasMore = false
      this.$nextTick(() => {
        this.memberForm = getDefaultMemberForm()
        if (this.$refs.memberForm) {
          this.$refs.memberForm.clearValidate()
        }
      })
    },
    resetMemberForm() {
      this.memberForm = getDefaultMemberForm()
      this.memberSubmitting = false
      this.userOptions = []
      this.userPageNo = 1
      this.userHasMore = false
      this.$nextTick(() => {
        if (this.$refs.memberForm) {
          this.$refs.memberForm.resetFields()
        }
      })
    },
    loadMoreUsers() {
      if (this.userHasMore && !this.userLoading) {
        this.userPageNo++
        this.loadUserOptions()
      }
    },
    loadUserOptions() {
      this.userLoading = true
      getUserList({
        pageNo: this.userPageNo,
        pageSize: this.userPageSize,
        keyword: '',
        status: 1
      }).then(res => {
        const data = res && res.data ? res.data : res || {}
        const list = data.list || data.items || data.data || []
        this.userTotal = data.total || data.totalCount || 0
        if (this.userPageNo === 1) {
          this.userOptions = list
        } else {
          this.userOptions = [...this.userOptions, ...list]
        }
        this.userHasMore = this.userOptions.length < this.userTotal
      }).catch(() => {
        this.userOptions = []
        this.userHasMore = false
      }).finally(() => {
        this.userLoading = false
      })
    },
    submitMember() {
      this.$refs.memberForm.validate(valid => {
        if (!valid) {
          return
        }
        if (!this.memberForm.user_ids || this.memberForm.user_ids.length === 0) {
          this.$message.error('请选择用户')
          return
        }
        this.memberSubmitting = true
        createProjectMember({
          project_id: this.getProjectId(),
          user_ids: this.memberForm.user_ids
        }).then(res => {
          const message = (res && res.message) || ''
          if (res && res.code === 20000) {
            this.$message.success(message || '成员新增成功')
            this.memberDialogVisible = false
            this.memberPageNo = 1
            this.fetchData()
            return
          }
          this.$message.error(message || '成员新增失败')
        }).finally(() => {
          this.memberSubmitting = false
        })
      })
    },
    openEnvironmentDialog() {
      this.environmentDialogVisible = true
      this.$nextTick(() => {
        this.environmentForm = getDefaultEnvironmentForm()
        if (this.$refs.environmentForm) {
          this.$refs.environmentForm.clearValidate()
        }
      })
    },
    resetEnvironmentForm() {
      this.environmentForm = getDefaultEnvironmentForm()
      this.environmentSubmitting = false
      this.$nextTick(() => {
        if (this.$refs.environmentForm) {
          this.$refs.environmentForm.resetFields()
        }
      })
    },
    submitEnvironment() {
      this.$refs.environmentForm.validate(valid => {
        if (!valid) {
          return
        }
        let variables = {}
        try {
          variables = JSON.parse(this.environmentForm.variablesText || '{}')
        } catch (e) {
          this.$message.error('变量JSON格式不正确')
          return
        }
        this.environmentSubmitting = true
        createEnvironment({
          project_id: this.getProjectId(),
          name: this.environmentForm.name,
          variables
        }).then(res => {
          const message = (res && res.message) || ''
          if (res && res.code === 20000) {
            this.$message.success(message || '环境新增成功')
            this.environmentDialogVisible = false
            this.environmentPageNo = 1
            this.fetchData()
            return
          }
          this.$message.error(message || '环境新增失败')
        }).finally(() => {
          this.environmentSubmitting = false
        })
      })
    },
    handleMemberSizeChange(val) {
      this.memberPageSize = val
      this.memberPageNo = 1
      this.fetchData()
    },
    handleMemberCurrentChange(val) {
      this.memberPageNo = val
      this.fetchData()
    },
    handleEnvironmentSizeChange(val) {
      this.environmentPageSize = val
      this.environmentPageNo = 1
      this.fetchData()
    },
    handleEnvironmentCurrentChange(val) {
      this.environmentPageNo = val
      this.fetchData()
    }
  },
  created() {
    this.fetchData()
    this.fetchHooks()
    this.fetchCodePrdConfig()
    this.fetchCodePrdRecords()
  },
  beforeDestroy() {
    if (this.codePrdRefreshTimer) {
      clearTimeout(this.codePrdRefreshTimer)
      this.codePrdRefreshTimer = null
    }
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}

.toolbar-wrap {
  margin-bottom: 16px;
  text-align: right;
}

.hook-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.hook-toolbar-left {
  text-align: left;
}

.code-prd-config {
  padding: 14px 16px 6px;
  margin-bottom: 16px;
  background: #f8fafc;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.code-prd-form {
  max-width: 760px;
}

.code-prd-prompt-wrap {
  margin-bottom: 12px;
}

.code-prd-progress-wrap {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.code-prd-progress-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  color: #303133;
  font-size: 13px;
}

.code-prd-progress-status {
  color: #606266;
  text-align: right;
}

.code-prd-markdown {
  max-height: 560px;
  overflow: auto;
  margin: 0;
  padding: 14px;
  background: #f8fafc;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  color: #303133;
  font-family: Consolas, Monaco, monospace;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.code-prd-error {
  margin-bottom: 10px;
  color: #f56c6c;
}
</style>
