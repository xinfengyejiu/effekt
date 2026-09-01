<template>
  <div class="page-wrap page-wrap--bug-detail page-wrap--fixed-actions">
    <page-section title="Bug 详情">
      <template slot="extra">
        <el-button size="small" @click="goBack">返回列表</el-button>
        <el-button type="primary" size="small" @click="goEdit">编辑</el-button>
      </template>
      <div class="detail-layout">
        <div v-loading="loading" class="detail-top-loading">
          <el-row :gutter="20">
            <el-col :span="24">
            <div class="detail-card main-card">
              <div class="main-card-head">
                <div class="main-card-head-left">
                  <span class="bug-key">{{ detail.bug_key || detail.bugKey || '' }}</span>
                  <el-tag size="small" :type="severityTagType(detail.severity)">{{ formatSeverity(detail.severity) }}</el-tag>
                  <el-tag size="small" :type="priorityTagType(detail.priority)">{{ formatPriority(detail.priority) }}</el-tag>
                </div>
                <div class="status-corner" :class="statusBadgeClass(detail.status)">
                  {{ formatStatus(detail.status) }}
                </div>
              </div>
              <h2 class="bug-title">{{ detail.title }}</h2>
              <el-row :gutter="16" class="meta-rows">
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">缺陷类型</div>
                    <div class="meta-value">{{ formatBugType(detailBugType) }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">环境</div>
                    <div class="meta-value">{{ detail.environment || '-' }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">当前指派</div>
                    <div class="meta-value">{{ assigneeDisplay }}</div>
                  </div>
                </el-col>
              </el-row>
              <el-row :gutter="16" class="meta-rows">
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">创建人</div>
                    <div class="meta-value">{{ reporterDisplay }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">产品</div>
                    <div class="meta-value">{{ productDisplay }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">项目</div>
                    <div class="meta-value">{{ projectDisplay }}</div>
                  </div>
                </el-col>
              </el-row>
              <el-row :gutter="16" class="meta-rows">
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">模块</div>
                    <div class="meta-value">{{ moduleDisplay }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">关联用例</div>
                    <div class="meta-value">{{ caseDisplay }}</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">关联计划</div>
                    <div class="meta-value">{{ detail.plan_id || detail.planId || '-' }}</div>
                  </div>
                </el-col>
              </el-row>
              <el-row :gutter="16" class="meta-rows meta-rows-last">
                <el-col :span="8">
                  <div class="meta-field">
                    <div class="meta-label">创建时间</div>
                    <div class="meta-value">{{ formatTime(detail.created_time || detail.createdTime) }}</div>
                  </div>
                </el-col>
              </el-row>
            </div>

            <div class="detail-card steps-card mt">
              <div
                v-if="hasStepsContent"
                class="steps-display"
                v-html="stepsDisplayHtml"
              ></div>
              <div v-else class="steps-empty">暂无复现内容</div>
            </div>
            </el-col>
          </el-row>
        </div>

        <div class="detail-card mt feed-tab-card">
          <div class="feed-pill-tabs" role="tablist">
            <button
              type="button"
              class="feed-pill-tab"
              :class="{ 'is-active': feedMainTab === 'comments' }"
              role="tab"
              :aria-selected="feedMainTab === 'comments'"
              @click="feedMainTab = 'comments'">
              评论
            </button>
            <button
              type="button"
              class="feed-pill-tab"
              :class="{ 'is-active': feedMainTab === 'history' }"
              role="tab"
              :aria-selected="feedMainTab === 'history'"
              @click="feedMainTab = 'history'">
              变更历史
            </button>
          </div>
          <div class="feed-tab-divider"></div>

          <div v-show="feedMainTab === 'comments'" class="feed-tab-panel" role="tabpanel">
            <div class="comment-tab-toolbar">
              <el-button
                type="primary"
                plain
                size="small"
                class="comment-add-remark-btn"
                icon="el-icon-edit-outline"
                @click="openCommentDialog">
                添加备注
              </el-button>
            </div>
            <div v-for="c in commentList" :key="c.id" class="comment-item">
              <div class="comment-meta">
                <span>{{ (c.user_name || c.userName || c.username || '-') }}：</span>
                <span class="time">{{ formatTime(c.created_time || c.createdTime) }}</span>
              </div>
              <div class="comment-body" v-html="c.content || ''"></div>
            </div>
            <div v-if="!commentList.length" class="empty-hint">暂无评论</div>
          </div>

          <div v-show="feedMainTab === 'history'" class="feed-tab-panel" role="tabpanel">
            <el-timeline v-if="historyList.length">
              <el-timeline-item v-for="h in historyList" :key="h.id" :timestamp="formatTime(h.created_time || h.createdTime)" placement="top">
                <div class="history-line">
                  <span class="history-field">{{ formatHistoryFieldName(h.field_name || h.fieldName) }}</span>
                  <span class="history-arrow">
                    <template v-if="historyFieldUsesColoredTags(h)">
                      <span class="history-tag-pair">
                        <el-tag
                          size="mini"
                          :type="historyTagType(historyNormKey(h), h.old_value || h.oldValue)"
                          :effect="historyTagEffect(h.old_value || h.oldValue)"
                          class="history-enum-tag">
                          {{ formatHistoryCellValue(h.field_name || h.fieldName, h.old_value || h.oldValue) }}
                        </el-tag>
                        <span class="history-arrow-symbol">→</span>
                        <el-tag
                          size="mini"
                          :type="historyTagType(historyNormKey(h), h.new_value || h.newValue)"
                          :effect="historyTagEffect(h.new_value || h.newValue)"
                          class="history-enum-tag">
                          {{ formatHistoryCellValue(h.field_name || h.fieldName, h.new_value || h.newValue) }}
                        </el-tag>
                      </span>
                    </template>
                    <template v-else>
                      {{ formatHistoryCellValue(h.field_name || h.fieldName, h.old_value || h.oldValue) }}
                      <span class="history-arrow-symbol history-arrow-symbol--text">→</span>
                      {{ formatHistoryCellValue(h.field_name || h.fieldName, h.new_value || h.newValue) }}
                    </template>
                  </span>
                  <span class="history-op">操作人 {{ historyOperatorLabel(h) }}</span>
                </div>
              </el-timeline-item>
            </el-timeline>
            <div v-else class="empty-hint">暂无历史记录</div>
          </div>
        </div>
      </div>
    </page-section>

    <div v-if="effectiveBugId" class="bug-action-dock">
      <div class="bug-action-dock-inner">
        <div class="bug-action-strip">
          <el-button
            v-if="nextStatusTransition"
            type="primary"
            size="small"
            :loading="actionSaving"
            :disabled="loading"
            @click="applyNextStatus">
            {{ nextStatusTransition.nextLabel }}
          </el-button>
          <span v-if="nextStatusTransition" class="bug-action-strip-divider" />
          <el-button
            size="small"
            plain
            :disabled="loading || cannotUseResolveButton"
            @click="openResolveDialog">
            解决
          </el-button>
          <span class="bug-action-strip-divider" />
          <el-button
            size="small"
            plain
            :loading="reopenSaving"
            :disabled="loading || !canReopenBug"
            @click="applyReopen">
            重新打开
          </el-button>
          <span class="bug-action-strip-divider" />
          <el-button
            size="small"
            type="danger"
            plain
            :loading="deleteSaving"
            :disabled="loading"
            @click="confirmDelete">
            删除
          </el-button>
        </div>
      </div>
    </div>

    <el-dialog
      :visible.sync="resolveDialogVisible"
      width="800px"
      append-to-body
      destroy-on-close
      custom-class="bug-resolve-dialog"
      :close-on-click-modal="false"
      @closed="resetResolveForm">
      <div slot="title" class="resolve-dialog-header">
        <span class="resolve-dialog-id">{{ detail.id || detail.bug_id || detail.bugId || bugId }}</span>
        <span class="resolve-dialog-title-text">{{ detail.title || '解决 Bug' }}</span>
      </div>
      <el-form
        ref="resolveFormRef"
        :model="resolveForm"
        :rules="resolveFormRules"
        label-width="108px"
        label-position="right"
        size="small"
        class="resolve-dialog-form">
        <el-form-item label="解决方案" prop="solutionType">
          <el-select
            v-model="resolveForm.solutionType"
            placeholder="请选择"
            class="resolve-field-select"
            popper-class="bug-resolve-solution-dropdown"
            style="width: 100%;">
            <el-option
              v-for="opt in solutionOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="解决版本">
          <el-select
            v-model="resolveForm.fixedVersion"
            clearable
            placeholder="请选择"
            class="resolve-field-select"
            style="width: 100%;">
            <el-option
              v-for="opt in versionOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="解决日期" prop="resolvedAt">
          <el-date-picker
            v-model="resolveForm.resolvedAt"
            type="datetime"
            value-format="yyyy-MM-dd HH:mm:ss"
            format="yyyy-MM-dd HH:mm:ss"
            placeholder="选择日期时间"
            style="width: 100%;" />
        </el-form-item>
        <el-form-item label="当前指派" prop="assigneeId">
          <el-select
            v-model="resolveForm.assigneeId"
            filterable
            clearable
            placeholder="请选择"
            style="width: 100%;"
            @focus="onResolveAssigneeFocus">
            <el-option
              v-for="u in resolveMemberOptions"
              :key="'rm-' + u.id"
              :label="u.name"
              :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="解决人">
          <span class="resolve-resolver-readonly">{{ currentResolverDisplay }}</span>
          <span class="resolve-resolver-hint">（默认当前登录用户）</span>
        </el-form-item>
        <el-form-item label="备注" class="resolve-remark-item">
          <bug-steps-rich-editor :key="'resolve-editor-' + resolveDialogKey" v-model="resolveForm.remarkHtml" />
        </el-form-item>
      </el-form>
      <div class="resolve-dialog-footer">
        <el-button type="primary" :loading="resolveDialogSaving" @click="submitResolveDialog">保存</el-button>
      </div>
      <div class="resolve-history-block">
        <div class="resolve-history-title">历史记录</div>
        <ol v-if="resolveHistoryPreviewList.length" class="resolve-history-list">
          <li v-for="(row, idx) in resolveHistoryPreviewList" :key="'rh-' + (row.raw && row.raw.id != null ? row.raw.id : idx)">
            <span class="resolve-history-time">{{ row.time }}</span>，
            <span class="history-field">{{ formatHistoryFieldName(row.fieldKey) }}</span>
            <span class="history-arrow history-arrow--inline">
              <template v-if="historyFieldKeyUsesColoredTags(row.fieldKey)">
                <span class="history-tag-pair">
                  <el-tag
                    size="mini"
                    :type="historyTagType(row.fieldKey, row.oldVal)"
                    :effect="historyTagEffect(row.oldVal)"
                    class="history-enum-tag">
                    {{ formatHistoryCellValue(row.fieldKey, row.oldVal) }}
                  </el-tag>
                  <span class="history-arrow-symbol">→</span>
                  <el-tag
                    size="mini"
                    :type="historyTagType(row.fieldKey, row.newVal)"
                    :effect="historyTagEffect(row.newVal)"
                    class="history-enum-tag">
                    {{ formatHistoryCellValue(row.fieldKey, row.newVal) }}
                  </el-tag>
                </span>
              </template>
              <template v-else>
                {{ formatHistoryCellValue(row.fieldKey, row.oldVal) }}
                <span class="history-arrow-symbol history-arrow-symbol--text">→</span>
                {{ formatHistoryCellValue(row.fieldKey, row.newVal) }}
              </template>
            </span>
            <span class="resolve-history-op">（操作人 {{ row.op }}）</span>
          </li>
        </ol>
        <div v-else class="resolve-history-empty">暂无历史记录</div>
      </div>
    </el-dialog>

    <el-dialog
      title="添加备注"
      :visible.sync="commentDialogVisible"
      width="900px"
      append-to-body
      custom-class="bug-comment-dialog"
      :close-on-click-modal="false"
      @closed="resetCommentDialog">
      <bug-steps-rich-editor
        :key="'comment-editor-' + commentDialogKey"
        v-model="commentRemarkHtml"
        :height="320"
        placeholder="请输入备注内容，工具栏可插入图片，支持粘贴截图" />
      <div slot="footer" class="bug-comment-dialog-footer">
        <el-button @click="commentDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="commentSubmitting" @click="submitCommentFromDialog">保存</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import BugStepsRichEditor from '@/components/Bug/BugStepsRichEditor.vue'
import { getBugDetail, updateBug, addBugComment, deleteBug } from '@/api/bugApi'
import { recordBugHistory } from '@/utils/bugHistory'
import {
  formatBugHistoryFieldName,
  formatBugHistoryCellValue,
  normalizeBugHistoryFieldKey
} from '@/utils/bugHistoryDisplay'
import { getProductList } from '@/api/productApi'
import { getProjectDetail, getProjectMembers } from '@/api/projectApi'
import { getModuleTree } from '@/api/caseApi'
import {
  formatBugType,
  formatSeverity,
  formatPriority,
  formatStatus,
  statusBadgeClass,
  getBugStatusNextTransition,
  BUG_STATUS_RESOLVED,
  BUG_STATUS_CLOSED,
  BUG_STATUS_PENDING,
  BUG_STATUS_REJECTED,
  severityTagType,
  priorityTagType,
  statusTagType
} from '@/utils/bugMaps'
import {
  formatBugStepsToHtml,
  isStepsLikelyHtml,
  rewriteImgSrcsInHtml
} from '@/utils/bugStepsFormat'

function getDefaultResolveForm() {
  const now = new Date()
  const pad = n => (n < 10 ? '0' + n : '' + n)
  const ts =
    now.getFullYear() +
    '-' +
    pad(now.getMonth() + 1) +
    '-' +
    pad(now.getDate()) +
    ' ' +
    pad(now.getHours()) +
    ':' +
    pad(now.getMinutes()) +
    ':' +
    pad(now.getSeconds())
  return {
    solutionType: '',
    fixedVersion: '',
    resolvedAt: ts,
    assigneeId: '',
    remarkHtml: '<p><br></p>'
  }
}

export default {
  name: 'BugDetail',
  components: { PageSection, BugStepsRichEditor },
  data() {
    return {
      loading: false,
      bugId: '',
      feedMainTab: 'comments',
      detail: {},
      commentDialogVisible: false,
      commentDialogKey: 0,
      commentRemarkHtml: '',
      commentSubmitting: false,
      actionSaving: false,
      deleteSaving: false,
      reopenSaving: false,
      resolvedProductName: '',
      resolvedProjectName: '',
      resolvedModuleName: '',
      resolveDialogVisible: false,
      resolveDialogKey: 0,
      resolveDialogSaving: false,
      resolveForm: getDefaultResolveForm(),
      resolveFormRules: {
        solutionType: [{ required: true, message: '请选择解决方案', trigger: 'change' }],
        resolvedAt: [{ required: true, message: '请选择解决日期', trigger: 'change' }],
        assigneeId: [{ required: true, message: '请选择当前指派', trigger: 'change' }]
      },
      resolveMemberOptions: [],
      solutionOptions: [
        { label: '设计如此', value: 'by_design' },
        { label: '重复Bug', value: 'duplicate_bug' },
        { label: '外部原因', value: 'external_reason' },
        { label: '已解决', value: 'solution_resolved' },
        { label: '无法重现', value: 'cannot_reproduce' },
        { label: '延期处理', value: 'deferred' },
        { label: '不予解决', value: 'wont_fix' }
      ],
      versionOptions: [
        { label: '主干', value: 'trunk' },
        { label: '当前迭代', value: 'current_sprint' },
        { label: '下一版本', value: 'next' }
      ]
    }
  },
  computed: {
    nextStatusTransition() {
      return getBugStatusNextTransition(this.detail.status)
    },
    isResolvedStatus() {
      return Number(this.detail.status) === BUG_STATUS_RESOLVED
    },
    isClosedStatus() {
      return Number(this.detail.status) === BUG_STATUS_CLOSED
    },
    /** 已解决或已关闭时不可再点「解决」弹窗 */
    cannotUseResolveButton() {
      return this.isResolvedStatus || this.isClosedStatus
    },
    /** 已解决 / 已关闭 / 已拒绝 可重新打开为待处理 */
    canReopenBug() {
      const s = Number(this.detail.status)
      return s === BUG_STATUS_RESOLVED || s === BUG_STATUS_CLOSED || s === BUG_STATUS_REJECTED
    },
    detailBugType() {
      const d = this.detail || {}
      return d.bug_type != null ? d.bug_type : d.bugType
    },
    reporterDisplay() {
      const d = this.detail || {}
      const name =
        d.reporter_real_name ||
        d.reporterRealName ||
        d.reporter_name ||
        d.reporterName ||
        d.creator_real_name ||
        d.creatorRealName ||
        d.creator_name ||
        d.creatorName ||
        ''
      const id = d.reporter_id || d.reporterId || d.creator_id || d.creatorId || d.created_by || d.createdBy
      if (name) return name
      if (id !== undefined && id !== null && id !== '') return String(id)
      return '-'
    },
    assigneeDisplay() {
      const d = this.detail || {}
      const name =
        d.assignee_real_name ||
        d.assigneeRealName ||
        d.assignee_name ||
        d.assigneeName ||
        ''
      const id = d.assignee_id || d.assigneeId
      if (name) return name
      if (id !== undefined && id !== null && id !== '') return String(id)
      return '-'
    },
    /** 解决操作中的「解决人」：仅展示，提交时 resolvedBy 取当前登录用户 id */
    currentResolverDisplay() {
      const u = this.$store.state.currentUser
      if (!u) return '—'
      return u.real_name || u.realName || u.username || (u.id != null ? String(u.id) : '—')
    },
    productDisplay() {
      const d = this.detail || {}
      const name = d.product_name || d.productName || this.resolvedProductName
      const id = d.product_id || d.productId
      if (name) return name
      if (id !== undefined && id !== null && id !== '') return String(id)
      return '-'
    },
    projectDisplay() {
      const d = this.detail || {}
      const name = d.project_name || d.projectName || this.resolvedProjectName
      const id = d.project_id || d.projectId
      if (name) return name
      if (id !== undefined && id !== null && id !== '') return String(id)
      return '-'
    },
    moduleDisplay() {
      const d = this.detail || {}
      const name = d.module_name || d.moduleName || this.resolvedModuleName
      const id = d.module_id || d.moduleId
      if (name) return name
      if (id !== undefined && id !== null && id !== '') return String(id)
      return '-'
    },
    caseDisplay() {
      const d = this.detail || {}
      const key = d.case_key || d.caseKey
      if (key) return key
      return '-'
    },
    commentList() {
      const c = this.detail.comments
      return Array.isArray(c) ? c : []
    },
    historyList() {
      const h = this.detail.history
      return Array.isArray(h) ? h : []
    },
    detailStepsRaw() {
      const d = this.detail || {}
      const candidates = [
        d.steps,
        d.reproduce_steps,
        d.reproduceSteps,
        d.reproduction_steps,
        d.reproductionSteps
      ]
      for (let i = 0; i < candidates.length; i++) {
        const v = candidates[i]
        if (v !== undefined && v !== null) return v
      }
      return ''
    },
    hasStepsContent() {
      return String(this.detailStepsRaw).trim() !== ''
    },
    stepsDisplayHtml() {
      const raw = this.detailStepsRaw
      if (!String(raw).trim()) return ''
      if (isStepsLikelyHtml(raw)) {
        return rewriteImgSrcsInHtml(raw)
      }
      return formatBugStepsToHtml(raw)
    },
    effectiveBugId() {
      const id = this.bugId != null && this.bugId !== '' ? String(this.bugId) : ''
      return id
    },
    resolveHistoryPreviewList() {
      const list = this.historyList || []
      return list.slice(0, 20).map((h, idx) => ({
        idx,
        raw: h,
        time: this.formatTime(h.created_time || h.createdTime),
        fieldKey: normalizeBugHistoryFieldKey(h.field_name || h.fieldName),
        oldVal: h.old_value !== undefined && h.old_value !== null ? h.old_value : h.oldValue,
        newVal: h.new_value !== undefined && h.new_value !== null ? h.new_value : h.newValue,
        op: this.historyOperatorLabel(h)
      }))
    }
  },
  watch: {
    $route: {
      handler() {
        this.syncBugIdFromRoute()
        if (this.bugId) {
          this.loadDetail()
        } else {
          this.detail = {}
        }
      },
      immediate: true
    }
  },
  methods: {
    formatHistoryFieldName: formatBugHistoryFieldName,
    formatHistoryCellValue: formatBugHistoryCellValue,
    historyNormKey(h) {
      return normalizeBugHistoryFieldKey((h && (h.field_name || h.fieldName)) || '')
    },
    historyFieldUsesColoredTags(h) {
      const k = this.historyNormKey(h)
      return this.historyFieldKeyUsesColoredTags(k)
    },
    historyFieldKeyUsesColoredTags(fieldKey) {
      const k = String(fieldKey || '').trim()
      return k === 'status' || k === 'priority' || k === 'severity'
    },
    historyValueIsEmpty(val) {
      return val === undefined || val === null || val === ''
    },
    historyTagEffect(val) {
      return this.historyValueIsEmpty(val) ? 'plain' : 'dark'
    },
    historyTagType(fieldKey, raw) {
      const k = String(fieldKey || '').trim()
      if (this.historyValueIsEmpty(raw)) return 'info'
      const n = Number(String(raw).trim())
      if (Number.isNaN(n)) return undefined
      if (k === 'status') return statusTagType(n)
      if (k === 'priority') return priorityTagType(n)
      if (k === 'severity') return severityTagType(n)
      return 'info'
    },
    historyOperatorLabel(h) {
      const d = h || {}
      return d.operator_name || d.operatorName || d.operator_real_name || d.operatorRealName || d.operator_id || d.operatorId || '-'
    },
    syncBugIdFromRoute() {
      const q = (this.$route && this.$route.query) || {}
      if (q.bugId != null && q.bugId !== '') {
        this.bugId = String(q.bugId)
        return
      }
      if (q.id != null && q.id !== '') {
        this.bugId = String(q.id)
        return
      }
      this.bugId = ''
    },
    formatBugType,
    formatSeverity,
    formatPriority,
    formatStatus,
    statusBadgeClass,
    severityTagType,
    priorityTagType,
    formatTime(v) {
      if (!v) return '-'
      return String(v).replace('T', ' ').slice(0, 19)
    },
    findModuleNameInTree(nodes, targetId) {
      const idStr = String(targetId)
      const walk = (list, pfx) => {
        for (let i = 0; i < (list || []).length; i++) {
          const n = list[i]
          const name = pfx ? `${pfx} / ${n.name}` : n.name
          if (String(n.id) === idStr) return name
          const ch = n.children || n.child_list || n.childList || []
          if (ch.length) {
            const hit = walk(ch, name)
            if (hit) return hit
          }
        }
        return ''
      }
      return walk(nodes || [], '')
    },
    loadScopeNames() {
      const d = this.detail || {}
      const productId = d.product_id || d.productId
      const projectId = d.project_id || d.projectId
      const moduleId = d.module_id || d.moduleId
      this.resolvedProductName = ''
      this.resolvedProjectName = ''
      this.resolvedModuleName = ''
      if (d.product_name || d.productName) {
        this.resolvedProductName = d.product_name || d.productName
      }
      if (d.project_name || d.projectName) {
        this.resolvedProjectName = d.project_name || d.projectName
      }
      if (d.module_name || d.moduleName) {
        this.resolvedModuleName = d.module_name || d.moduleName
      }
      const tasks = []
      if (!this.resolvedProductName && productId) {
        tasks.push(
          getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
            const data = (res && res.data) || res || {}
            const items = data.items || data.list || data.data || []
            const p = (items || []).find(x => String(x.id) === String(productId))
            if (p) this.resolvedProductName = p.name || ''
          }).catch(() => {})
        )
      }
      if (!this.resolvedProjectName && projectId) {
        tasks.push(
          getProjectDetail(projectId).then(res => {
            const data = (res && res.data) || res || {}
            this.resolvedProjectName = data.name || ''
          }).catch(() => {})
        )
      }
      if (!this.resolvedModuleName && projectId && moduleId) {
        tasks.push(
          getModuleTree({ projectId, pageNo: 1, pageSize: 1000 }).then(res => {
            const data = (res && res.data) || res || {}
            const tree = data.list || data.items || []
            this.resolvedModuleName = this.findModuleNameInTree(tree, moduleId) || ''
          }).catch(() => {})
        )
      }
      return Promise.all(tasks)
    },
    loadDetail() {
      if (!this.bugId) return
      this.loading = true
      this.resolvedProductName = ''
      this.resolvedProjectName = ''
      this.resolvedModuleName = ''
      getBugDetail(this.bugId).then(res => {
        this.detail = (res && res.data) || res || {}
        return this.loadScopeNames()
      }).catch(() => { this.detail = {} }).finally(() => { this.loading = false })
    },
    applyReopen() {
      if (!this.bugId) return
      if (!this.canReopenBug) {
        this.$message.info('当前状态无需重新打开')
        return
      }
      this.reopenSaving = true
      const oldStatus = this.detail.status
      updateBug({
        bugId: Number(this.bugId),
        id: Number(this.bugId),
        status: BUG_STATUS_PENDING
      })
        .then(() => {
          recordBugHistory(this.$store, {
            bugId: this.bugId,
            fieldName: 'status',
            oldValue: oldStatus,
            newValue: BUG_STATUS_PENDING
          })
          this.$message.success('已重新打开为待处理')
          this.loadDetail()
        })
        .finally(() => {
          this.reopenSaving = false
        })
    },
    applyNextStatus() {
      const t = this.nextStatusTransition
      if (!this.bugId || !t) return
      this.actionSaving = true
      const oldStatus = this.detail.status
      updateBug({
        bugId: Number(this.bugId),
        id: Number(this.bugId),
        status: t.nextStatus
      })
        .then(() => {
          recordBugHistory(this.$store, {
            bugId: this.bugId,
            fieldName: 'status',
            oldValue: oldStatus,
            newValue: t.nextStatus
          })
          this.$message.success('状态已更新')
          this.loadDetail()
        })
        .finally(() => {
          this.actionSaving = false
        })
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
    loadResolveMembers() {
      const pid = this.detail.project_id || this.detail.projectId
      if (!pid) {
        this.resolveMemberOptions = []
        return Promise.resolve()
      }
      return getProjectMembers(pid, { pageNo: 1, pageSize: 500 })
        .then(res => {
          const data = (res && res.data) || res || {}
          const raw = data.items || data.list || data.data || []
          this.resolveMemberOptions = this.mapMemberRows(Array.isArray(raw) ? raw : [])
        })
        .catch(() => {
          this.resolveMemberOptions = []
        })
    },
    onResolveAssigneeFocus() {
      this.loadResolveMembers()
    },
    openResolveDialog() {
      if (!this.bugId) return
      if (this.cannotUseResolveButton) {
        if (this.isClosedStatus) {
          this.$message.info('已关闭的 Bug 请使用「重新打开」')
        } else {
          this.$message.info('当前已是已解决')
        }
        return
      }
      this.resolveForm = getDefaultResolveForm()
      this.resolveForm.assigneeId = this.detail.assignee_id || this.detail.assigneeId || ''
      this.resolveDialogKey += 1
      this.resolveDialogVisible = true
      this.$nextTick(() => {
        this.loadResolveMembers()
        if (this.$refs.resolveFormRef) {
          this.$refs.resolveFormRef.clearValidate()
        }
      })
    },
    resetResolveForm() {
      this.resolveForm = getDefaultResolveForm()
      this.resolveMemberOptions = []
      if (this.$refs.resolveFormRef) {
        this.$refs.resolveFormRef.resetFields()
      }
    },
    /** 解决弹窗备注：空编辑器不传；保留含截图的 HTML（img 为 /bug/upload 地址） */
    resolveRemarkHtmlForApi(html) {
      const h = (html || '').trim()
      if (!h || h === '<p><br></p>' || h === '<p><br/></p>') return ''
      return h
    },
    submitResolveDialog() {
      if (!this.bugId) return
      this.$refs.resolveFormRef.validate(valid => {
        if (!valid) return
        const user = this.$store.state.currentUser
        const uid = user && user.id
        if (uid === undefined || uid === null || uid === '') {
          this.$message.warning('未获取到当前登录用户')
          return
        }
        this.resolveDialogSaving = true
        const oldStatus = this.detail.status
        const oldSolution =
          this.detail.solution ||
          this.detail.solution_type ||
          this.detail.solutionType ||
          ''
        const resolvedBy = Number(uid)
        const assigneeId = Number(this.resolveForm.assigneeId)
        const clean = {
          bugId: Number(this.bugId),
          id: Number(this.bugId),
          status: BUG_STATUS_RESOLVED,
          solution: this.resolveForm.solutionType,
          user_id: Number(uid),
          assigneeId,
          resolvedBy,
          comment: this.resolveRemarkHtmlForApi(this.resolveForm.remarkHtml)
        }
        if (this.resolveForm.fixedVersion !== '' && this.resolveForm.fixedVersion != null) {
          clean.resolveVersion = this.resolveForm.fixedVersion
        }
        const oldResolvedBy =
          this.detail.resolved_by != null && this.detail.resolved_by !== ''
            ? this.detail.resolved_by
            : this.detail.resolvedBy != null && this.detail.resolvedBy !== ''
              ? this.detail.resolvedBy
              : ''
        const oldAssigneeId =
          this.detail.assignee_id != null && this.detail.assignee_id !== ''
            ? this.detail.assignee_id
            : this.detail.assigneeId != null && this.detail.assigneeId !== ''
              ? this.detail.assigneeId
              : ''
        updateBug(clean)
          .then(() => {
            recordBugHistory(this.$store, {
              bugId: this.bugId,
              fieldName: 'status',
              oldValue: oldStatus,
              newValue: BUG_STATUS_RESOLVED
            })
            recordBugHistory(this.$store, {
              bugId: this.bugId,
              fieldName: 'solution',
              oldValue: oldSolution,
              newValue: this.resolveForm.solutionType
            })
            if (String(oldAssigneeId) !== String(assigneeId)) {
              recordBugHistory(this.$store, {
                bugId: this.bugId,
                fieldName: 'assignee_id',
                oldValue: oldAssigneeId,
                newValue: assigneeId
              })
            }
            if (String(oldResolvedBy) !== String(resolvedBy)) {
              recordBugHistory(this.$store, {
                bugId: this.bugId,
                fieldName: 'resolved_by',
                oldValue: oldResolvedBy,
                newValue: resolvedBy
              })
            }
            if (this.resolveForm.fixedVersion !== '' && this.resolveForm.fixedVersion != null) {
              recordBugHistory(this.$store, {
                bugId: this.bugId,
                fieldName: 'resolve_version',
                oldValue: '',
                newValue: this.resolveForm.fixedVersion
              })
            }
            const remark = this.resolveRemarkHtmlForApi(this.resolveForm.remarkHtml)
            if (remark) {
              recordBugHistory(this.$store, {
                bugId: this.bugId,
                fieldName: 'resolve_comment',
                oldValue: '',
                newValue: remark.length > 2000 ? remark.slice(0, 2000) : remark
              })
            }
            this.$message.success('已保存为已解决')
            this.resolveDialogVisible = false
            this.loadDetail()
          })
          .catch(() => {})
          .finally(() => {
            this.resolveDialogSaving = false
          })
      })
    },
    confirmDelete() {
      if (!this.bugId) return
      this.$confirm('确认删除该 Bug？删除后不可恢复。', '删除确认', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消'
      })
        .then(() => {
          this.deleteSaving = true
          const bid = Number(this.bugId)
          return recordBugHistory(this.$store, {
            bugId: bid,
            fieldName: 'delete',
            oldValue: '0',
            newValue: '1'
          }).then(() => deleteBug({ bugId: bid, id: bid }))
        })
        .then(() => {
          this.$message.success('已删除')
          this.$router.push({ path: '/bug/list' })
        })
        .catch(() => {})
        .finally(() => {
          this.deleteSaving = false
        })
    },
    openCommentDialog() {
      this.commentRemarkHtml = ''
      this.commentDialogKey += 1
      this.commentDialogVisible = true
    },
    resetCommentDialog() {
      this.commentRemarkHtml = ''
    },
    submitCommentFromDialog() {
      const content = this.resolveRemarkHtmlForApi(this.commentRemarkHtml)
      if (!content) {
        this.$message.warning('请输入备注内容')
        return
      }
      const user = this.$store.state.currentUser
      const uid = user && user.id
      if (uid === undefined || uid === null || uid === '') {
        this.$message.warning('未获取到当前登录用户')
        return
      }
      this.commentSubmitting = true
      addBugComment({
        bugId: Number(this.bugId),
        id: Number(this.bugId),
        content,
        user_id: Number(uid)
      }).then(() => {
        recordBugHistory(this.$store, {
          bugId: Number(this.bugId),
          fieldName: 'comment',
          oldValue: '',
          newValue: content.length > 2000 ? content.slice(0, 2000) : content
        })
        this.$message.success('评论已提交')
        this.commentDialogVisible = false
        this.resetCommentDialog()
        this.loadDetail()
      }).finally(() => {
        this.commentSubmitting = false
      })
    },
    goBack() {
      this.$router.push({ path: '/bug/list' })
    },
    goEdit() {
      this.$router.push({ path: '/bug/edit', query: { bugId: this.bugId, from: 'detail' } })
    }
  },
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}
.page-wrap--bug-detail {
  background: #f0f2f5;
  margin: -20px;
  padding: 20px;
  min-height: calc(100vh - 60px);
}
.page-wrap--fixed-actions {
  padding-bottom: 88px;
}
.page-wrap--bug-detail >>> .page-section.el-card {
  background: transparent;
  border: none;
  box-shadow: none;
}
.page-wrap--bug-detail >>> .page-section > .el-card__header {
  border-bottom: none;
  background: transparent;
  padding: 0 0 16px;
}
.page-wrap--bug-detail >>> .page-section > .el-card__body {
  padding: 0;
  background: transparent;
}
.detail-layout {
  min-height: 200px;
}
.detail-top-loading {
  min-height: 120px;
}
.detail-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
}
.main-card {
  position: relative;
}
.main-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.main-card-head-left {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.status-corner {
  flex-shrink: 0;
  padding: 5px 14px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
}
.bug-status-new {
  background: #ecf5ff;
  color: #1e40af;
}
.bug-status-pending {
  background: #fdf6ec;
  color: #e6a23c;
}
.bug-status-progress {
  background: #e8f4ff;
  color: #1989fa;
  border: 1px solid #b3d8ff;
}
.bug-status-resolved {
  background: #f0f9eb;
  color: #67c23a;
}
.bug-status-closed {
  background: #f4f4f5;
  color: #909399;
}
.bug-status-rejected {
  background: #fef0f0;
  color: #f56c6c;
}
.bug-status-unknown {
  background: #f4f4f5;
  color: #606266;
}
.mt {
  margin-top: 16px;
}
.mt-sm {
  margin-top: 10px;
}
.bug-key {
  font-weight: 600;
  color: #1e40af;
  margin-right: 4px;
}
.bug-title {
  margin: 12px 0 18px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.meta-rows {
  margin-bottom: 14px;
}
.meta-rows-last {
  margin-bottom: 0;
}
.meta-field {
  min-height: 56px;
}
.meta-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
  line-height: 1.5;
  font-weight: 500;
}
.meta-value {
  font-size: 15px;
  color: #303133;
  line-height: 1.55;
  word-break: break-word;
}
.steps-card {
  min-height: 72px;
}
.steps-empty {
  color: #909399;
  font-size: 13px;
  line-height: 1.6;
}
.block-title {
  font-weight: 600;
  color: #606266;
  margin: 12px 0 8px;
}
.steps-display {
  line-height: 1.6;
  color: #303133;
  word-break: break-word;
}
.steps-display >>> .bug-step-img,
.steps-display >>> img {
  display: block;
  max-width: 100%;
  margin: 10px 0;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}
.steps-display >>> p {
  margin: 0 0 8px;
}
.comment-item {
  border-bottom: 1px solid #ebeef5;
  padding: 10px 0;
}
.comment-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  justify-content: space-between;
}
.comment-body {
  margin-top: 6px;
  color: #303133;
  line-height: 1.6;
  word-break: break-word;
}
.comment-body >>> img {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 8px 0;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}
.comment-body >>> p {
  margin: 0 0 6px;
}
.empty-hint {
  color: #909399;
  font-size: 13px;
}
.feed-tab-card {
  padding-top: 18px;
}
.feed-pill-tabs {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.feed-pill-tab {
  border: none;
  border-radius: 18px;
  padding: 6px 18px;
  font-size: 13px;
  line-height: 1.5;
  cursor: pointer;
  background: #f4f4f5;
  color: #606266;
  outline: none;
  transition: background 0.2s, color 0.2s;
}
.feed-pill-tab:hover:not(.is-active) {
  color: #303133;
  background: #ebeef5;
}
.feed-pill-tab.is-active {
  background: #ecf5ff;
  color: #1e40af;
  font-weight: 500;
}
.feed-tab-divider {
  height: 1px;
  background: #ebeef5;
  margin: 12px 0 8px;
}
.feed-tab-panel {
  min-height: 48px;
}
.comment-tab-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}
.comment-add-remark-btn {
  flex-shrink: 0;
}
.history-field {
  font-weight: 600;
  margin-right: 8px;
}
.history-arrow {
  color: #606266;
}
.history-op {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}
.history-line {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 8px;
}
.history-tag-pair {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  vertical-align: middle;
}
.history-arrow-symbol {
  color: #909399;
  font-weight: 500;
  user-select: none;
}
.history-arrow-symbol--text {
  margin: 0 4px;
}
.history-arrow--inline {
  margin-right: 4px;
}
.history-enum-tag {
  vertical-align: middle;
}
.bug-action-dock {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 200;
  padding: 12px 20px calc(14px + env(safe-area-inset-bottom, 0px));
  background: transparent;
  border: none;
  box-shadow: none;
  pointer-events: none;
}
.bug-action-dock-inner {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  pointer-events: none;
}
.bug-action-strip {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px 12px;
  padding: 12px 18px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  pointer-events: auto;
}
.bug-action-strip-divider {
  width: 1px;
  height: 18px;
  background: #dcdfe6;
  flex-shrink: 0;
}
</style>

<style>
/* el-dialog 挂载到 body，需非 scoped */
.bug-resolve-dialog .el-dialog__header {
  padding: 16px 36px 10px;
  border-bottom: 1px solid #ebeef5;
}
.bug-resolve-dialog .el-dialog__body {
  padding: 20px 40px 16px;
}
.bug-resolve-dialog .resolve-dialog-form {
  max-width: 640px;
  margin: 0 auto;
}
.bug-resolve-dialog .resolve-dialog-form .el-form-item {
  margin-bottom: 18px;
}
.bug-resolve-dialog .resolve-dialog-form .el-form-item__label {
  padding-right: 16px;
}
.bug-resolve-dialog .resolve-field-select .el-input__inner,
.bug-resolve-dialog .resolve-dialog-form .el-date-editor .el-input__inner,
.bug-resolve-dialog .resolve-dialog-form .el-select:not(.resolve-field-select) .el-input__inner {
  border-radius: 6px;
}
.bug-resolve-dialog .el-dialog__headerbtn {
  top: 14px;
}
.bug-resolve-dialog .resolve-dialog-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding-right: 28px;
}
.bug-resolve-dialog .resolve-dialog-id {
  flex-shrink: 0;
  background: #f0f2f5;
  color: #909399;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
}
.bug-resolve-dialog .resolve-dialog-title-text {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  line-height: 1.5;
  text-align: left;
}
.bug-resolve-dialog .resolve-resolver-readonly {
  color: #303133;
  font-weight: 500;
}
.bug-resolve-dialog .resolve-resolver-hint {
  margin-left: 8px;
  font-size: 12px;
  color: #909399;
}
.bug-resolve-dialog .resolve-remark-item .el-form-item__content {
  line-height: 1.4;
}
.bug-resolve-dialog .resolve-dialog-footer {
  text-align: center;
  padding: 8px 0 4px;
  max-width: 640px;
  margin: 0 auto;
}
.bug-resolve-dialog .resolve-history-block {
  margin-top: 16px;
  margin-left: auto;
  margin-right: auto;
  max-width: 640px;
  padding-top: 14px;
  border-top: 1px solid #ebeef5;
}
.bug-resolve-dialog .resolve-history-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 10px;
}
.bug-resolve-dialog .resolve-history-list {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  font-size: 13px;
  line-height: 1.7;
}
.bug-resolve-dialog .resolve-history-list li {
  margin-bottom: 6px;
}
.bug-resolve-dialog .resolve-history-time {
  color: #909399;
  font-size: 12px;
}
.bug-resolve-dialog .resolve-history-op {
  font-size: 12px;
  color: #909399;
}
.bug-resolve-dialog .resolve-history-empty {
  font-size: 13px;
  color: #909399;
}
/* 解决方案下拉面挂载在 body */
.bug-resolve-solution-dropdown.el-select-dropdown {
  border-radius: 6px;
}
.bug-resolve-solution-dropdown .el-select-dropdown__item {
  padding: 0 20px;
  line-height: 36px;
}
.bug-resolve-solution-dropdown .el-select-dropdown__list {
  padding: 6px 0;
}

.bug-comment-dialog .el-dialog__body {
  padding: 12px 20px 8px;
}
.bug-comment-dialog .bug-comment-dialog-footer {
  text-align: center;
}
.bug-comment-dialog .bug-comment-dialog-footer .el-button + .el-button {
  margin-left: 12px;
}
</style>
