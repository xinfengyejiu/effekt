<template>
  <div class="page-wrap">
    <page-section :title="isCreate ? '新建 Bug' : '编辑 Bug'">
      <template slot="extra">
        <el-button size="small" @click="goBack">返回</el-button>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" size="small" class="bug-form">
        <el-form-item label="标题" prop="title">
          <el-input v-model.trim="form.title" maxlength="200" show-word-limit placeholder="Bug 标题" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="产品" prop="productId">
              <el-select v-model="form.productId" filterable placeholder="请选择产品" style="width: 100%;" @change="onProductChange" @focus="loadProductOptions">
                <el-option v-for="p in productOptions" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="项目" prop="projectId">
              <el-select v-model="form.projectId" filterable placeholder="请选择项目" style="width: 100%;" :disabled="!form.productId" @change="onProjectChange">
                <el-option v-for="p in projectOptions" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="模块" prop="moduleId">
              <el-select v-model="form.moduleId" filterable placeholder="请选择模块" style="width: 100%;" :disabled="!form.projectId">
                <el-option v-for="m in flatModules" :key="m.id" :label="m.name" :value="m.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="类型" prop="bugType">
              <el-select v-model="form.bugType" placeholder="类型" style="width: 100%;">
                <el-option v-for="(label, key) in bugTypeOptions" :key="key" :label="label" :value="Number(key)" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="严重程度" prop="severity">
              <el-select v-model="form.severity" placeholder="严重程度" style="width: 100%;">
                <el-option v-for="(label, key) in severityOptions" :key="key" :label="label" :value="Number(key)" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="form.priority" placeholder="优先级" style="width: 100%;">
                <el-option v-for="(label, key) in priorityOptions" :key="key" :label="label" :value="Number(key)" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="复现率" prop="reproduceRate">
              <el-select v-model="form.reproduceRate" placeholder="请选择复现率" style="width: 100%;">
                <el-option v-for="(label, key) in reproduceRateOptions" :key="key" :label="label" :value="Number(key)" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col v-if="!isCreate" :span="8">
            <el-form-item label="状态">
              <el-select v-model="form.status" clearable placeholder="状态" style="width: 100%;">
                <el-option v-for="(label, key) in statusOptions" :key="key" :label="label" :value="Number(key)" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="isCreate ? 12 : 8">
            <el-form-item label="创建人" prop="reporterId">
              <el-input
                v-if="isCreate"
                class="bug-creator-readonly"
                :value="defaultCreatorDisplayName"
                readonly
                placeholder="当前登录用户"
                style="width: 100%;" />
              <el-select
                v-else
                ref="reporterSelect"
                v-model="form.reporterId"
                filterable
                placeholder="请先选择项目"
                style="width: 100%;"
                popper-class="bug-editor-reporter-members"
                :disabled="!form.projectId"
                @visible-change="onReporterDropdownVisible">
                <el-option v-for="u in reporterMemberOptions" :key="'r-' + u.id" :label="u.name" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="isCreate ? 12 : 8">
            <el-form-item label="当前指派" prop="assigneeId">
              <el-select
                ref="assigneeSelect"
                v-model="form.assigneeId"
                filterable
                placeholder="请选择当前指派"
                style="width: 100%;"
                popper-class="bug-editor-assignee-members"
                :disabled="!form.projectId"
                @visible-change="onAssigneeDropdownVisible">
                <el-option v-for="u in assigneeMemberOptions" :key="'a-' + u.id" :label="u.name" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="环境">
              <el-input v-model.trim="form.environment" maxlength="64" placeholder="如 st / pre" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="关联用例">
              <el-input v-model="form.caseId" placeholder="选填，用例 ID" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="关联计划">
              <el-input v-model="form.planId" placeholder="选填，计划 ID" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="复现步骤">
          <bug-steps-rich-editor :key="stepsEditorKey" v-model="form.steps" />
        </el-form-item>
        <el-form-item>
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" :loading="saving" @click="submit">{{ isCreate ? '创建' : '保存' }}</el-button>
        </el-form-item>
      </el-form>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import BugStepsRichEditor from '@/components/Bug/BugStepsRichEditor.vue'
import { getBugDetail, createBug, updateBug } from '@/api/bugApi'
import { recordBugHistory, recordBugEditDiff, buildBugEditBaseline } from '@/utils/bugHistory'
import { legacyStepsToEditorHtml, BUG_STEPS_DEFAULT_HTML } from '@/utils/bugStepsFormat'
import { getProductList } from '@/api/productApi'
import { getProjectList, getProjectMembers } from '@/api/projectApi'
import { getModuleTree } from '@/api/caseApi'
import { BUG_TYPE_MAP, SEVERITY_MAP, PRIORITY_MAP, STATUS_MAP, REPRODUCE_RATE_MAP } from '@/utils/bugMaps'

export default {
  name: 'BugEditor',
  components: { PageSection, BugStepsRichEditor },
  data() {
    return {
      saving: false,
      bugId: '',
      /** 新建页复制带入后递增，用于富文本编辑器 key 强制刷新 */
      editorNonce: 0,
      productOptions: [],
      projectOptions: [],
      moduleTree: [],
      memberPageSize: 10,
      reporterMemberOptions: [],
      reporterMemberPageNo: 0,
      reporterMemberNoMore: false,
      reporterMemberLoading: false,
      assigneeMemberOptions: [],
      assigneeMemberPageNo: 0,
      assigneeMemberNoMore: false,
      assigneeMemberLoading: false,
      assigneeExtraLabel: '',
      editBaseline: null,
      form: {
        title: '',
        bugType: 1,
        severity: 2,
        priority: 2,
        status: '',
        productId: '',
        projectId: '',
        moduleId: '',
        caseId: '',
        planId: '',
        environment: '',
        steps: BUG_STEPS_DEFAULT_HTML,
        reporterId: '',
        assigneeId: '',
        reproduceRate: 1
      },
      rules: {
        title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
        reproduceRate: [{ required: true, message: '请选择复现率', trigger: 'change' }],
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }],
        moduleId: [{ required: true, message: '请选择模块', trigger: 'change' }],
        assigneeId: [{ required: true, message: '请选择当前指派', trigger: 'change' }],
        reporterId: [
          {
            required: true,
            validator: (rule, value, callback) => {
              if (this.isCreate) {
                const uid = this.defaultReporterId()
                if (uid === '' || uid === undefined || uid === null) {
                  callback(new Error('未获取到当前登录用户，请重新登录'))
                } else {
                  callback()
                }
                return
              }
              if (value === '' || value === undefined || value === null) {
                callback(new Error('请选择创建人'))
              } else {
                callback()
              }
            },
            trigger: 'change'
          }
        ]
      }
    }
  },
  computed: {
    isCreate() {
      return (this.$route.path || '').indexOf('/bug/create') !== -1
    },
    bugTypeOptions() {
      return BUG_TYPE_MAP
    },
    severityOptions() {
      return SEVERITY_MAP
    },
    priorityOptions() {
      return PRIORITY_MAP
    },
    statusOptions() {
      return STATUS_MAP
    },
    reproduceRateOptions() {
      return REPRODUCE_RATE_MAP
    },
    flatModules() {
      const out = []
      const walk = (nodes, prefix) => {
        ;(nodes || []).forEach(n => {
          const name = prefix ? `${prefix} / ${n.name}` : n.name
          out.push({ id: n.id, name })
          const ch = n.children || n.child_list || n.childList || []
          if (ch.length) walk(ch, name)
        })
      }
      walk(this.moduleTree, '')
      return out
    },
    stepsEditorKey() {
      if (this.isCreate) {
        return 'create-' + String(this.editorNonce)
      }
      return 'edit-' + String(this.bugId || '0')
    },
    currentUser() {
      return this.$store.state.currentUser
    },
    /** 新建页展示：优先 real_name（接口字段），与 store 中 realName 一致 */
    defaultCreatorDisplayName() {
      const u = this.currentUser
      if (!u) return '-'
      return u.real_name || u.realName || u.username || '-'
    }
  },
  watch: {
    '$route.query.bugId'(v) {
      this.bugId = v || ''
      if (!this.isCreate) this.loadDetail()
    },
    isCreate(val) {
      if (val) {
        if (this.$route.query.copyFrom) return
        this.form.steps = BUG_STEPS_DEFAULT_HTML
        this.form.reporterId = this.defaultReporterId()
        this.form.reproduceRate = 1
        this.form.assigneeId = ''
        this.assigneeExtraLabel = ''
        this.resetReporterMembers()
        this.resetAssigneeMembers()
      }
    },
    '$route.query.copyFrom': {
      handler(v) {
        if (!this.isCreate || !v) return
        this.loadProductOptions().then(() => this.applyCopyFromDetail(v))
      },
      immediate: true
    }
  },
  destroyed() {
    this.unbindReporterMemberScroll()
    this.unbindAssigneeMemberScroll()
  },
  methods: {
    defaultReporterId() {
      const u = this.currentUser
      return u && u.id != null && u.id !== '' ? u.id : ''
    },
    mapMemberRows(list) {
      const arr = Array.isArray(list) ? list : []
      return arr
        .map(item => ({
          id: item.user_id || item.userId || item.id,
          name:
            item.real_name ||
            item.realName ||
            item.username ||
            item.name ||
            item.user_name ||
            String(item.user_id || item.id)
        }))
        .filter(u => u.id !== undefined && u.id !== null)
    },
    ensureCurrentUserInMemberOptions(opts) {
      const u = this.currentUser
      if (!u || u.id == null || u.id === '') return opts || []
      const list = opts || []
      if (list.some(m => String(m.id) === String(u.id))) return list
      const label = u.realName || u.username || '当前用户'
      return [{ id: u.id, name: label }, ...list]
    },
    applyDefaultReporterIfNeeded() {
      if (!this.isCreate) return
      const uid = this.defaultReporterId()
      const inList = id =>
        id !== '' && id !== undefined && id !== null &&
        this.reporterMemberOptions.some(m => String(m.id) === String(id))
      if (!uid) return
      if (!this.form.reporterId || !inList(this.form.reporterId)) {
        if (inList(uid)) this.form.reporterId = uid
      }
    },
    mergeMemberById(existing, incoming) {
      const base = (existing || []).slice()
      const seen = new Set(base.map(x => String(x.id)))
      ;(incoming || []).forEach(x => {
        if (x.id === undefined || x.id === null) return
        const k = String(x.id)
        if (!seen.has(k)) {
          seen.add(k)
          base.push(x)
        }
      })
      return base
    },
    resetReporterMembers() {
      this.reporterMemberOptions = []
      this.reporterMemberPageNo = 0
      this.reporterMemberNoMore = false
    },
    resetAssigneeMembers() {
      this.assigneeMemberOptions = []
      this.assigneeMemberPageNo = 0
      this.assigneeMemberNoMore = false
    },
    fetchReporterMemberPage(append) {
      const pid = this.form.projectId
      if (!pid || this.reporterMemberLoading) return Promise.resolve()
      if (append && this.reporterMemberNoMore) return Promise.resolve()
      const nextPage = append ? this.reporterMemberPageNo + 1 : 1
      if (!append) {
        this.resetReporterMembers()
      }
      this.reporterMemberLoading = true
      return getProjectMembers(pid, { pageNo: nextPage, pageSize: this.memberPageSize })
        .then(res => {
          const data = (res && res.data) || res || {}
          const raw = data.items || data.list || data.data || []
          const rows = this.mapMemberRows(Array.isArray(raw) ? raw : [])
          if (append) {
            this.reporterMemberOptions = this.mergeMemberById(this.reporterMemberOptions, rows)
          } else {
            this.reporterMemberOptions = this.ensureCurrentUserInMemberOptions(rows)
          }
          this.reporterMemberPageNo = nextPage
          this.reporterMemberNoMore = rows.length < this.memberPageSize
        })
        .catch(() => {
          if (!append) {
            this.reporterMemberOptions = this.ensureCurrentUserInMemberOptions([])
          }
          this.reporterMemberNoMore = true
        })
        .finally(() => {
          this.reporterMemberLoading = false
        })
        .then(() => {
          this.applyDefaultReporterIfNeeded()
        })
    },
    fetchAssigneeMemberPage(append) {
      const pid = this.form.projectId
      if (!pid || this.assigneeMemberLoading) return Promise.resolve()
      if (append && this.assigneeMemberNoMore) return Promise.resolve()
      const nextPage = append ? this.assigneeMemberPageNo + 1 : 1
      if (!append) {
        this.resetAssigneeMembers()
      }
      this.assigneeMemberLoading = true
      return getProjectMembers(pid, { pageNo: nextPage, pageSize: this.memberPageSize })
        .then(res => {
          const data = (res && res.data) || res || {}
          const raw = data.items || data.list || data.data || []
          const rows = this.mapMemberRows(Array.isArray(raw) ? raw : [])
          if (append) {
            this.assigneeMemberOptions = this.mergeMemberById(this.assigneeMemberOptions, rows)
          } else {
            this.assigneeMemberOptions = rows.slice()
          }
          this.assigneeMemberPageNo = nextPage
          this.assigneeMemberNoMore = rows.length < this.memberPageSize
          this.ensureAssigneeInOptions()
        })
        .catch(() => {
          if (!append) this.assigneeMemberOptions = []
          this.assigneeMemberNoMore = true
        })
        .finally(() => {
          this.assigneeMemberLoading = false
        })
    },
    ensureAssigneeInOptions() {
      const id = this.form.assigneeId
      if (id === '' || id === undefined || id === null) return
      if (this.assigneeMemberOptions.some(m => String(m.id) === String(id))) return
      const name = this.assigneeExtraLabel || `用户 ${id}`
      this.assigneeMemberOptions = [{ id, name }, ...this.assigneeMemberOptions]
    },
    getMemberDropdownScrollWrap(popperClass) {
      const pop = document.querySelector(`.${popperClass}`)
      if (!pop) return null
      return pop.querySelector('.el-select-dropdown__wrap') || pop.querySelector('.el-scrollbar__wrap')
    },
    unbindReporterMemberScroll() {
      if (this._reporterScrollEl && this._reporterScrollHandler) {
        this._reporterScrollEl.removeEventListener('scroll', this._reporterScrollHandler)
      }
      this._reporterScrollEl = null
      this._reporterScrollHandler = null
    },
    unbindAssigneeMemberScroll() {
      if (this._assigneeScrollEl && this._assigneeScrollHandler) {
        this._assigneeScrollEl.removeEventListener('scroll', this._assigneeScrollHandler)
      }
      this._assigneeScrollEl = null
      this._assigneeScrollHandler = null
    },
    bindReporterMemberScroll() {
      this.unbindReporterMemberScroll()
      this.$nextTick(() => {
        const el = this.getMemberDropdownScrollWrap('bug-editor-reporter-members')
        if (!el) return
        this._reporterScrollEl = el
        this._reporterScrollHandler = this.onReporterMemberDropdownScroll.bind(this)
        el.addEventListener('scroll', this._reporterScrollHandler, { passive: true })
      })
    },
    bindAssigneeMemberScroll() {
      this.unbindAssigneeMemberScroll()
      this.$nextTick(() => {
        const el = this.getMemberDropdownScrollWrap('bug-editor-assignee-members')
        if (!el) return
        this._assigneeScrollEl = el
        this._assigneeScrollHandler = this.onAssigneeMemberDropdownScroll.bind(this)
        el.addEventListener('scroll', this._assigneeScrollHandler, { passive: true })
      })
    },
    onReporterMemberDropdownScroll(e) {
      const el = e.target
      if (this.reporterMemberLoading || this.reporterMemberNoMore) return
      if (el.scrollHeight - el.scrollTop - el.clientHeight < 40) {
        this.fetchReporterMemberPage(true)
      }
    },
    onAssigneeMemberDropdownScroll(e) {
      const el = e.target
      if (this.assigneeMemberLoading || this.assigneeMemberNoMore) return
      if (el.scrollHeight - el.scrollTop - el.clientHeight < 40) {
        this.fetchAssigneeMemberPage(true)
      }
    },
    onReporterDropdownVisible(visible) {
      if (!visible) {
        this.unbindReporterMemberScroll()
        return
      }
      if (!this.form.projectId) return
      const load = !this.reporterMemberOptions.length
        ? this.fetchReporterMemberPage(false)
        : Promise.resolve()
      load.finally(() => {
        this.$nextTick(() => this.bindReporterMemberScroll())
      })
    },
    onAssigneeDropdownVisible(visible) {
      if (!visible) {
        this.unbindAssigneeMemberScroll()
        return
      }
      if (!this.form.projectId) return
      const load = !this.assigneeMemberOptions.length
        ? this.fetchAssigneeMemberPage(false)
        : Promise.resolve()
      load.finally(() => {
        this.$nextTick(() => this.bindAssigneeMemberScroll())
      })
    },
    loadProjectMembersForForm(projectId) {
      if (!projectId) {
        this.resetReporterMembers()
        this.resetAssigneeMembers()
        return Promise.resolve()
      }
      if (this.isCreate) {
        this.resetReporterMembers()
        return this.fetchAssigneeMemberPage(false)
      }
      return Promise.all([
        this.fetchReporterMemberPage(false),
        this.fetchAssigneeMemberPage(false)
      ])
    },
    loadProductOptions() {
      if (this.productOptions.length) return Promise.resolve()
      return getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        const data = (res && res.data) || res || {}
        this.productOptions = data.items || data.list || data.data || []
      }).catch(() => { this.productOptions = [] })
    },
    loadProjects(productId) {
      if (!productId) {
        this.projectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        const data = (res && res.data) || res || {}
        this.projectOptions = data.items || data.list || data.data || []
      }).catch(() => { this.projectOptions = [] })
    },
    loadModules(projectId) {
      if (!projectId) {
        this.moduleTree = []
        return Promise.resolve()
      }
      return getModuleTree({ projectId, pageNo: 1, pageSize: 1000 }).then(res => {
        const data = (res && res.data) || res || {}
        this.moduleTree = data.list || data.items || []
      }).catch(() => { this.moduleTree = [] })
    },
    onProductChange(val) {
      this.form.projectId = ''
      this.form.moduleId = ''
      this.form.assigneeId = ''
      this.form.reporterId = this.defaultReporterId()
      this.moduleTree = []
      this.assigneeExtraLabel = ''
      this.resetReporterMembers()
      this.resetAssigneeMembers()
      this.loadProjects(val)
    },
    onProjectChange(val) {
      this.form.moduleId = ''
      this.form.assigneeId = ''
      this.assigneeExtraLabel = ''
      this.loadModules(val)
      this.loadProjectMembersForForm(val)
    },
    applyCopyTitle(raw) {
      const t = String(raw || '').trim()
      const suffix = '（复制）'
      if (!t) return suffix
      if (t.indexOf(suffix) !== -1) {
        return t.length > 200 ? t.slice(0, 200) : t
      }
      const combined = t + suffix
      if (combined.length <= 200) return combined
      return t.slice(0, Math.max(0, 200 - suffix.length)) + suffix
    },
    applyCopyFromDetail(sourceBugId) {
      const sid = String(sourceBugId || '').trim()
      if (!sid) return Promise.resolve()
      return getBugDetail(sid)
        .then(res => {
          const d = (res && res.data) || res || {}
          this.assigneeExtraLabel =
            d.assignee_real_name ||
            d.assigneeRealName ||
            d.assignee_name ||
            d.assigneeName ||
            d.assignee_username ||
            d.assigneeUsername ||
            ''
          const rawSteps =
            d.steps || d.reproduce_steps || d.reproduceSteps || d.reproduction_steps || d.reproductionSteps || ''
          this.form = {
            title: this.applyCopyTitle(d.title || ''),
            bugType: d.bug_type != null ? d.bug_type : d.bugType != null ? d.bugType : 1,
            severity: d.severity != null ? d.severity : 2,
            priority: d.priority != null ? d.priority : 2,
            status: '',
            productId: d.product_id || d.productId || '',
            projectId: d.project_id || d.projectId || '',
            moduleId: d.module_id || d.moduleId || '',
            caseId: d.case_id != null && d.case_id !== '' ? d.case_id : d.caseId != null && d.caseId !== '' ? d.caseId : '',
            planId: d.plan_id != null && d.plan_id !== '' ? d.plan_id : d.planId != null && d.planId !== '' ? d.planId : '',
            environment: d.environment || '',
            steps: legacyStepsToEditorHtml(rawSteps),
            reporterId: this.defaultReporterId(),
            assigneeId: d.assignee_id || d.assigneeId || '',
            reproduceRate:
              d.reproduce_rate != null && d.reproduce_rate !== ''
                ? Number(d.reproduce_rate)
                : d.reproduceRate != null && d.reproduceRate !== ''
                  ? Number(d.reproduceRate)
                  : 1
          }
          if (this.form.productId) this.loadProjects(this.form.productId)
          if (this.form.projectId) {
            this.loadModules(this.form.projectId)
            this.loadProjectMembersForForm(this.form.projectId)
          }
          this.editorNonce = (this.editorNonce || 0) + 1
          this.bugId = ''
          this.editBaseline = null
          this.$nextTick(() => {
            if (this.$refs.formRef) this.$refs.formRef.clearValidate()
          })
          this.$message.success('已带入原 Bug 内容，请确认后创建')
        })
        .then(() => this.$router.replace({ path: '/bug/create', query: {} }).catch(() => {}))
        .catch(() => {
          this.$message.error('复制失败：无法加载原 Bug 详情')
        })
    },
    loadDetail() {
      if (!this.bugId) return
      getBugDetail(this.bugId).then(res => {
        const d = (res && res.data) || res || {}
        this.assigneeExtraLabel =
          d.assignee_real_name ||
          d.assigneeRealName ||
          d.assignee_name ||
          d.assigneeName ||
          d.assignee_username ||
          d.assigneeUsername ||
          ''
        const rawSteps =
          d.steps || d.reproduce_steps || d.reproduceSteps || d.reproduction_steps || d.reproductionSteps || ''
        this.form = {
          title: d.title || '',
          bugType: d.bug_type != null ? d.bug_type : (d.bugType != null ? d.bugType : 1),
          severity: d.severity != null ? d.severity : 2,
          priority: d.priority != null ? d.priority : 2,
          status: d.status != null ? d.status : '',
          productId: d.product_id || d.productId || '',
          projectId: d.project_id || d.projectId || '',
          moduleId: d.module_id || d.moduleId || '',
          caseId: d.case_id || d.caseId || '',
          planId: d.plan_id || d.planId || '',
          environment: d.environment || '',
          steps: legacyStepsToEditorHtml(rawSteps),
          reporterId:
            d.reporter_id ||
            d.reporterId ||
            d.creator_id ||
            d.creatorId ||
            d.created_by ||
            d.createdBy ||
            '',
          assigneeId: d.assignee_id || d.assigneeId || '',
          reproduceRate:
            d.reproduce_rate != null && d.reproduce_rate !== ''
              ? Number(d.reproduce_rate)
              : d.reproduceRate != null && d.reproduceRate !== ''
                ? Number(d.reproduceRate)
                : 1
        }
        if (this.form.productId) this.loadProjects(this.form.productId)
        if (this.form.projectId) {
          this.loadModules(this.form.projectId)
          this.loadProjectMembersForForm(this.form.projectId)
        }
        this.$nextTick(() => {
          this.editBaseline = buildBugEditBaseline(this.form)
        })
      }).catch(() => {})
    },
    clean(obj) {
      const o = {}
      Object.keys(obj).forEach(k => {
        const v = obj[k]
        if (v !== '' && v !== undefined && v !== null) o[k] = v
      })
      return o
    },
    submit() {
      this.$refs.formRef.validate(valid => {
        if (!valid) return
        this.saving = true
        if (this.isCreate) {
          const payload = this.clean({
            title: this.form.title,
            bugType: this.form.bugType,
            severity: this.form.severity,
            priority: this.form.priority,
            productId: this.form.productId,
            projectId: this.form.projectId,
            moduleId: this.form.moduleId,
            caseId: this.form.caseId,
            planId: this.form.planId,
            environment: this.form.environment,
            steps: this.form.steps,
            reporterId: this.form.reporterId,
            assigneeId: this.form.assigneeId,
            reproduceRate: this.form.reproduceRate
          })
          payload.description = ''
          createBug(payload).then(res => {
            const data = (res && res.data) || {}
            this.$message.success('创建成功')
            const id = data.id
            if (id) {
              recordBugHistory(this.$store, {
                bugId: id,
                fieldName: 'create',
                oldValue: '',
                newValue: '1'
              })
              this.$router.replace({ path: '/bug/detail', query: { bugId: id } })
            } else {
              this.$router.push({ path: '/bug/list' })
            }
          }).finally(() => { this.saving = false })
        } else {
          const payload = this.clean({
            bugId: Number(this.bugId),
            id: Number(this.bugId),
            title: this.form.title,
            bugType: this.form.bugType,
            severity: this.form.severity,
            priority: this.form.priority,
            status: this.form.status,
            reporterId: this.form.reporterId,
            assigneeId: this.form.assigneeId,
            moduleId: this.form.moduleId,
            caseId: this.form.caseId,
            planId: this.form.planId,
            environment: this.form.environment,
            steps: this.form.steps,
            reproduceRate: this.form.reproduceRate
          })
          payload.description = ''
          updateBug(payload)
            .then(() =>
              recordBugEditDiff(
                this.$store,
                Number(this.bugId),
                this.editBaseline,
                buildBugEditBaseline(this.form)
              )
            )
            .then(() => {
              this.$message.success('保存成功')
              this.goBack()
            })
            .finally(() => {
              this.saving = false
            })
        }
      })
    },
    goBack() {
      if (this.isCreate || this.$route.query.from !== 'detail') {
        this.$router.push({ path: '/bug/list' })
      } else {
        this.$router.push({ path: '/bug/detail', query: { bugId: this.bugId } })
      }
    }
  },
  created() {
    this.bugId = this.$route.query.bugId || ''
    if (this.isCreate) {
      this.form.reporterId = this.defaultReporterId()
    }
    if (!this.isCreate) {
      this.loadProductOptions().then(() => this.loadDetail())
    } else if (!this.$route.query.copyFrom) {
      this.loadProductOptions()
    }
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}
.bug-form {
  max-width: 960px;
}

.bug-creator-readonly >>> .el-input__inner {
  cursor: default;
  color: #606266;
  background-color: #f5f7fa;
}
</style>
