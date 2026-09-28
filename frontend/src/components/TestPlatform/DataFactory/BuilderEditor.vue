<template>
  <div class="page-wrap">
    <page-section :title="pageTitle">
      <template slot="extra">
        <el-button size="small" @click="goBack">返回列表</el-button>
      </template>
      <el-alert
        v-if="fromAi"
        title="当前为 AI 生成草稿：请审阅 steps 与参数，确认后保存；保存前不会写库。"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 16px;">
      </el-alert>
      <el-form :model="form" label-width="120px" size="small">
        <el-form-item label="产品">
          <el-select
            v-model="productId"
            filterable
            clearable
            placeholder="请选择产品"
            style="width: 240px;"
            :disabled="!!builderId"
            @change="onProductChange">
            <el-option
              v-for="item in productOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目">
          <el-select
            v-model="projectId"
            filterable
            clearable
            placeholder="请选择项目"
            style="width: 240px;"
            :disabled="!!builderId || !productId"
            @change="onProjectChange">
            <el-option
              v-for="item in projectOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.name"></el-input>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="tagsText" placeholder="逗号分隔，如 AI,订单"></el-input>
        </el-form-item>
        <el-form-item label="来源">
          <el-select v-model="form.source" style="width: 180px;">
            <el-option label="手工" value="manual"></el-option>
            <el-option label="AI" value="ai"></el-option>
            <el-option label="任务另存" value="saved_from_task"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3"></el-input>
        </el-form-item>
        <el-form-item label="默认参数(JSON)">
          <el-input v-model="paramsText" type="textarea" :rows="5"></el-input>
        </el-form-item>
        <el-form-item label="步骤预览">
          <el-table :data="stepRows" border size="mini" style="width: 100%;">
            <el-table-column prop="type" label="类型" width="90"></el-table-column>
            <el-table-column prop="name" label="名称" width="140"></el-table-column>
            <el-table-column prop="summary" label="摘要" min-width="280" show-overflow-tooltip></el-table-column>
          </el-table>
        </el-form-item>
        <el-form-item label="定义(JSON)">
          <el-input v-model="definitionText" type="textarea" :rows="12" @change="syncStepsFromDefinition"></el-input>
        </el-form-item>
        <el-form-item label="输入Schema(JSON)">
          <el-input v-model="inputSchemaText" type="textarea" :rows="6"></el-input>
        </el-form-item>
        <el-form-item v-if="fromAi" label="继续改稿">
          <el-input v-model="refineText" type="textarea" :rows="2" placeholder="例如：把 env 改成 st，并增加 assert 校验行数"></el-input>
          <el-button style="margin-top: 8px;" size="mini" :loading="refineLoading" @click="doRefine">AI 改一版</el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submitForm">保存场景</el-button>
          <el-button v-if="builderId" :loading="runLoading" @click="confirmExecute">确认执行</el-button>
          <el-button @click="goBack">取消</el-button>
        </el-form-item>
      </el-form>
      <div v-if="lastResult" style="margin-top: 12px;">
        <div class="hint">执行结果</div>
        <json-viewer :value="lastResult"></json-viewer>
      </div>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import JsonViewer from '@/components/TestPlatform/common/JsonViewer'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import {
  aiRefineBuilder,
  createBuilder,
  executeBuilder,
  getBuilderDetail,
  updateBuilder
} from '@/api/dataFactoryApi'
import {
  pickIdFromOptions,
  readLastProductProjectCache,
  saveLastProductProjectCache
} from '@/utils/lastProductProjectCache'

export default {
  name: 'BuilderEditor',
  components: { PageSection, JsonViewer },
  data() {
    return {
      saving: false,
      runLoading: false,
      refineLoading: false,
      fromAi: !!this.$route.query.fromAi,
      productId: '',
      projectId: '',
      productOptions: [],
      projectOptions: [],
      builderId: this.$route.query.builderId || '',
      definitionText: '{\n  "steps": [],\n  "output": {}\n}',
      inputSchemaText: '{\n  "type": "object",\n  "properties": {}\n}',
      paramsText: '{}',
      tagsText: '',
      refineText: '',
      stepRows: [],
      lastResult: null,
      form: {
        name: '',
        description: '',
        source: 'manual',
        builderType: 1
      }
    }
  },
  computed: {
    pageTitle() {
      if (this.fromAi) return 'AI 场景草稿审阅'
      return this.builderId ? '编辑造数场景' : '新建造数场景'
    }
  },
  methods: {
    listOf(res) {
      const data = (res && res.data) || res || {}
      return data.list || data.items || data.data || []
    },
    routeQuery() {
      const q = {}
      if (this.productId) q.productId = this.productId
      if (this.projectId) q.projectId = this.projectId
      return q
    },
    loadProducts() {
      return getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        this.productOptions = this.listOf(res)
      }).catch(() => { this.productOptions = [] })
    },
    loadProjects(productId) {
      if (!productId) {
        this.projectOptions = []
        return Promise.resolve()
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        this.projectOptions = this.listOf(res)
      }).catch(() => { this.projectOptions = [] })
    },
    onProductChange(val) {
      this.projectId = ''
      this.loadProjects(val)
    },
    onProjectChange(val) {
      if (this.productId && val) saveLastProductProjectCache(this.productId, val)
    },
    restoreSelection() {
      const routeProductId = this.$route.query.productId
      const routeProjectId = this.$route.query.projectId
      const cached = readLastProductProjectCache()
      this.productId = ''
      this.projectId = ''
      return this.loadProducts().then(() => {
        let productId = routeProductId
        let projectId = routeProductId ? routeProjectId : ''
        if (!productId && cached && cached.productId != null && cached.productId !== '') {
          productId = cached.productId
          projectId = cached.projectId
        }
        if (productId === '' || productId === undefined || productId === null) return
        const pickedProduct = pickIdFromOptions(this.productOptions, productId)
        const productExists = (this.productOptions || []).some(p => String(p.id) === String(pickedProduct))
        if (!productExists) return
        this.productId = pickedProduct
        return this.loadProjects(this.productId).then(() => {
          if (projectId === '' || projectId === undefined || projectId === null) return
          const has = (this.projectOptions || []).some(p => String(p.id) === String(projectId))
          if (has) this.projectId = pickIdFromOptions(this.projectOptions, projectId)
        })
      })
    },
    goBack() {
      this.$router.push({ path: '/data-tools/factory', query: this.routeQuery() })
    },
    applyDraft(draft) {
      if (!draft || typeof draft !== 'object') return
      this.form.name = draft.name || this.form.name
      this.form.description = draft.description || ''
      this.form.source = (draft.meta && draft.meta.generatedBy === 'ai') ? 'ai' : (draft.source || this.form.source || 'ai')
      this.tagsText = (draft.tags || []).join(',')
      this.paramsText = JSON.stringify(draft.params || {}, null, 2)
      this.definitionText = JSON.stringify(draft.definition || { steps: [], output: {} }, null, 2)
      this.inputSchemaText = JSON.stringify(draft.inputSchema || draft.input_schema || {}, null, 2)
      this.syncStepsFromDefinition()
    },
    syncStepsFromDefinition() {
      try {
        const def = JSON.parse(this.definitionText || '{}')
        const steps = (def && def.steps) || []
        this.stepRows = steps.map(step => ({
          type: step.type,
          name: step.name,
          summary: this.stepSummary(step)
        }))
      } catch (e) {
        this.stepRows = []
      }
    },
    stepSummary(step) {
      if (!step) return ''
      if (step.type === 'sql') {
        return [step.db_project || step.dbProject, step.env, (step.sql || '').slice(0, 80)].filter(Boolean).join(' | ')
      }
      if (step.type === 'set_var') {
        return 'vars: ' + Object.keys(step.vars || {}).join(',')
      }
      if (step.type === 'assert') {
        return step.expr || ''
      }
      return JSON.stringify(step).slice(0, 80)
    },
    loadDetail() {
      if (!this.builderId) return
      getBuilderDetail(this.projectId, this.builderId).then(res => {
        const data = (res && res.data) || res || {}
        this.form.name = data.name || ''
        this.form.description = data.description || ''
        this.form.source = data.source || 'manual'
        this.form.builderType = data.builder_type || data.builderType || 1
        this.tagsText = (data.tags || []).join(',')
        this.definitionText = JSON.stringify(data.definition || { steps: [], output: {} }, null, 2)
        this.inputSchemaText = JSON.stringify(data.input_schema || data.inputSchema || {}, null, 2)
        this.syncStepsFromDefinition()
      })
    },
    loadAiDraft() {
      if (!this.fromAi) return
      try {
        const raw = sessionStorage.getItem('dataFactoryAiDraft')
        if (raw) this.applyDraft(JSON.parse(raw))
      } catch (e) { /* ignore */ }
    },
    parsePayload() {
      const definition = JSON.parse(this.definitionText || '{}')
      const inputSchema = JSON.parse(this.inputSchemaText || '{}')
      const params = JSON.parse(this.paramsText || '{}')
      const tags = (this.tagsText || '').split(/[,，]/).map(s => s.trim()).filter(Boolean)
      return {
        name: this.form.name,
        description: this.form.description,
        builderType: this.form.builderType || 1,
        source: this.form.source || 'manual',
        tags,
        definition,
        inputSchema,
        params
      }
    },
    submitForm() {
      if (!this.projectId) {
        this.$message({ type: 'warning', message: '请先选择产品与项目' })
        return
      }
      let payload
      try {
        payload = this.parsePayload()
      } catch (e) {
        this.$message({ type: 'error', message: 'JSON 格式错误' })
        return
      }
      if (!payload.name) {
        this.$message({ type: 'warning', message: '请填写名称' })
        return
      }
      saveLastProductProjectCache(this.productId, this.projectId)
      this.saving = true
      const req = this.builderId
        ? updateBuilder(this.projectId, this.builderId, payload)
        : createBuilder(this.projectId, payload)
      req.then(res => {
        const data = (res && res.data) || res || {}
        if (!this.builderId && data.id) this.builderId = data.id
        this.$message({ type: 'success', message: '场景已保存' })
        try { sessionStorage.removeItem('dataFactoryAiDraft') } catch (e) { /* ignore */ }
        this.fromAi = false
      }).finally(() => {
        this.saving = false
      })
    },
    doRefine() {
      if (!(this.refineText || '').trim()) {
        this.$message({ type: 'warning', message: '请输入改稿指令' })
        return
      }
      let draft
      try {
        draft = this.parsePayload()
      } catch (e) {
        this.$message({ type: 'error', message: '当前草稿 JSON 有误，请先修正' })
        return
      }
      this.refineLoading = true
      aiRefineBuilder({ draft, instruction: this.refineText }).then(res => {
        const next = (res && res.data) || res || {}
        this.applyDraft(next)
        this.$message({ type: 'success', message: '已生成新草稿，请继续审阅' })
      }).finally(() => {
        this.refineLoading = false
      })
    },
    confirmExecute() {
      if (!this.builderId) {
        this.$message({ type: 'warning', message: '请先保存场景再执行' })
        return
      }
      let params = {}
      try {
        params = JSON.parse(this.paramsText || '{}')
      } catch (e) {
        this.$message({ type: 'error', message: '参数 JSON 格式错误' })
        return
      }
      this.$confirm('确认执行？将按 steps 写入目标库（生产环境已禁止）。', '确认执行', {
        type: 'warning'
      }).then(() => {
        this.runLoading = true
        return executeBuilder(this.projectId, this.builderId, { params })
      }).then(res => {
        this.lastResult = (res && res.data) || res || {}
        this.$message({ type: 'success', message: '执行完成' })
      }).catch(() => {}).finally(() => {
        this.runLoading = false
      })
    }
  },
  created() {
    this.restoreSelection().then(() => {
      this.loadAiDraft()
      this.loadDetail()
      this.syncStepsFromDefinition()
    })
  }
}
</script>

<style scoped>
.page-wrap {
  padding: 20px;
}
.hint {
  color: #666;
  font-size: 13px;
  margin-bottom: 8px;
}
</style>
