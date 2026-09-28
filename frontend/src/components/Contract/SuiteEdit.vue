<template>
  <div class="page-wrap">
    <page-section :title="form.id ? '编辑契约套件' : '新建契约套件'">
      <template slot="extra">
        <el-button size="small" @click="$router.back()">返回</el-button>
        <el-button type="primary" size="small" :loading="saving" @click="submit">保存</el-button>
      </template>

      <el-form ref="form" :model="form" :rules="rules" label-width="120px" size="small" style="max-width:960px;">
        <el-form-item label="产品" prop="product_id">
          <el-select v-model="form.product_id" filterable placeholder="选择产品" style="width:100%;" @change="onProductChange">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" prop="project_id">
          <el-select v-model="form.project_id" filterable :disabled="!form.product_id" placeholder="选择项目" style="width:100%;" @change="onProjectChange">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="套件名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="Base URL" prop="base_url">
          <el-input v-model="form.base_url" placeholder="https://api.example.com" />
        </el-form-item>
        <el-form-item label="默认 Headers">
          <el-input v-model="headersText" type="textarea" :rows="3" placeholder='JSON，如 {"Authorization":"Bearer xxx"}' />
        </el-form-item>
        <el-form-item label="契约来源">
          <el-radio-group v-model="form.source_type">
            <el-radio label="mock_document">Mock 文档</el-radio>
            <el-radio label="openapi_upload">粘贴 OpenAPI</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.source_type === 'mock_document'" label="Mock 文档">
          <el-select v-model="form.mock_document_id" filterable clearable placeholder="选择文档" style="width:100%;">
            <el-option v-for="d in documents" :key="d.id" :label="d.name + ' (#' + d.id + ')'" :value="d.id" />
          </el-select>
          <el-button style="margin-top:8px;" size="mini" :loading="previewing" @click="preview">加载接口</el-button>
        </el-form-item>
        <el-form-item v-else label="OpenAPI JSON">
          <el-input v-model="form.openapi_content" type="textarea" :rows="8" placeholder="粘贴 OpenAPI JSON" />
          <el-button style="margin-top:8px;" size="mini" :loading="previewing" @click="preview">解析接口</el-button>
        </el-form-item>

        <el-form-item label="调度类型">
          <el-select v-model="form.schedule_type" style="width:200px;">
            <el-option label="手动" value="manual" />
            <el-option label="Cron" value="cron" />
            <el-option label="间隔" value="interval" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.schedule_type === 'cron'" label="Cron">
          <el-input v-model="form.cron_expression" placeholder="分 时 日 月 周，如 0 * * * *" />
        </el-form-item>
        <el-form-item v-if="form.schedule_type === 'interval'" label="间隔秒">
          <el-input-number v-model="form.interval_seconds" :min="60" />
        </el-form-item>
        <el-form-item label="通知渠道">
          <el-input v-model="form.notify_type" placeholder="feishu / wechat_work / dingtalk，逗号分隔" />
        </el-form-item>
        <el-form-item label="Webhook">
          <el-input v-model="form.notify_webhook" placeholder="breaking 时推送" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="enabledSwitch" />
        </el-form-item>
      </el-form>

      <div class="table-title">
        守护接口（勾选启用）
        <el-button type="primary" plain size="mini" style="margin-left:12px;" @click="openAiDesign">AI 设计接口</el-button>
      </div>
      <el-table :data="form.items" border max-height="420" @selection-change="onSelect">
        <el-table-column type="selection" width="48" :selectable="() => true" />
        <el-table-column prop="method" label="方法" width="80" />
        <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
        <el-table-column prop="name" label="名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="启用" width="80">
          <template slot-scope="scope">
            <el-switch v-model="scope.row.enabled" :active-value="1" :inactive-value="0" />
          </template>
        </el-table-column>
      </el-table>
      <p class="tip">提示：保存时会写入当前表格全部接口；未启用的接口执行时会跳过。可用 AI 设计生成契约草稿后点「采用」加入列表。</p>
    </page-section>

    <el-drawer title="AI 辅助设计接口" :visible.sync="aiVisible" size="480px" append-to-body>
      <div style="padding:0 16px 24px;">
        <el-form label-width="90px" size="small">
          <el-form-item label="模式">
            <el-radio-group v-model="aiForm.mode">
              <el-radio label="nl">自然语言</el-radio>
              <el-radio label="sample_json">样例 JSON</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="aiForm.mode === 'nl'" label="描述">
            <el-input
              v-model="aiForm.text"
              type="textarea"
              :rows="5"
              placeholder="例：获取当前用户资料，返回 userId(整数)、nickname、status(active/frozen/deleted)"
            />
          </el-form-item>
          <el-form-item v-else label="样例 JSON">
            <el-input v-model="aiForm.sampleText" type="textarea" :rows="8" placeholder="粘贴一段真实响应 JSON" />
          </el-form-item>
          <el-form-item label="方法提示">
            <el-input v-model="aiForm.hintMethod" placeholder="可选，如 GET" style="width:120px;" />
          </el-form-item>
          <el-form-item label="路径提示">
            <el-input v-model="aiForm.hintPath" placeholder="可选，如 /api/v1/user/profile" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="aiLoading" @click="runAiDesign">生成契约草稿</el-button>
          </el-form-item>
        </el-form>

        <div v-if="aiDraft" class="ai-draft">
          <p><b>{{ aiDraft.method }}</b> {{ aiDraft.path }} — {{ aiDraft.name }}</p>
          <p>置信度：{{ formatConfidence(aiDraft.confidence) }}</p>
          <p v-if="aiDraft.notes && aiDraft.notes.length"><b>需确认：</b>{{ aiDraft.notes.join('；') }}</p>
          <el-input
            type="textarea"
            :rows="10"
            :value="JSON.stringify(aiDraft.response_schema || {}, null, 2)"
            readonly
          />
          <div style="margin-top:12px;">
            <el-button type="success" size="small" @click="applyAiDraft">采用并加入套件</el-button>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import { getMockDocumentList } from '@/api/mockApi'
import {
  getContractSuiteDetail,
  createContractSuite,
  updateContractSuite,
  previewContractSource,
  designContractInterface
} from '@/api/contractApi'

export default {
  name: 'ContractSuiteEdit',
  components: { PageSection },
  data () {
    return {
      saving: false,
      previewing: false,
      products: [],
      projects: [],
      documents: [],
      headersText: '{}',
      enabledSwitch: true,
      selectedRows: [],
      aiVisible: false,
      aiLoading: false,
      aiDraft: null,
      aiForm: {
        mode: 'nl',
        text: '',
        sampleText: '',
        hintMethod: 'GET',
        hintPath: ''
      },
      form: {
        id: null,
        product_id: '',
        project_id: '',
        name: '',
        base_url: '',
        source_type: 'mock_document',
        mock_document_id: null,
        openapi_content: '',
        schedule_type: 'manual',
        cron_expression: '',
        interval_seconds: 3600,
        notify_type: 'feishu',
        notify_webhook: '',
        items: []
      },
      rules: {
        product_id: [{ required: true, message: '请选择产品', trigger: 'change' }],
        project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
        name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
        base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }]
      }
    }
  },
  created () {
    this.loadProducts()
    const id = this.$route.query.id
    if (id) this.loadDetail(id)
  },
  methods: {
    dataOf (res) { return (res && res.data) || res || {} },
    listOf (res) {
      const d = this.dataOf(res)
      return d.list || d.items || d.data || []
    },
    formatConfidence (c) {
      if (c == null || c === '') return '-'
      const n = Number(c)
      if (Number.isNaN(n)) return '-'
      return (n * 100).toFixed(0) + '%'
    },
    openAiDesign () {
      this.aiVisible = true
      this.aiDraft = null
    },
    runAiDesign () {
      const payload = {
        mode: this.aiForm.mode,
        text: this.aiForm.text,
        hints: {
          method: this.aiForm.hintMethod,
          path: this.aiForm.hintPath
        }
      }
      if (this.aiForm.mode === 'sample_json') {
        try {
          payload.sample_json = JSON.parse(this.aiForm.sampleText || '{}')
        } catch (e) {
          this.$message.error('样例 JSON 不合法，请检查逗号/引号')
          return
        }
      }
      this.aiLoading = true
      this.aiDraft = null
      designContractInterface(payload).then(res => {
        const data = this.dataOf(res)
        if (!data || !data.response_schema) {
          this.$message.error((res && res.message) || '未生成有效契约草稿')
          return
        }
        this.aiDraft = data
        const src = data.source === 'sample_infer' ? '（样例推断）' : ''
        this.$message.success('已生成契约草稿' + src + '，请确认后采用')
      }).catch(err => {
        const msg = (err && err.message) || '生成失败，请稍后重试'
        this.$message.error(msg)
      }).finally(() => { this.aiLoading = false })
    },
    applyAiDraft () {
      if (!this.aiDraft) return
      this.form.items.push({
        mock_interface_id: null,
        name: this.aiDraft.name,
        method: this.aiDraft.method || 'GET',
        path: this.aiDraft.path || '/',
        response_schema: this.aiDraft.response_schema || {},
        path_params: {},
        query_params: {},
        body_template: null,
        enabled: 1,
        sort_order: this.form.items.length
      })
      this.aiVisible = false
      this.$message.success('已加入套件接口列表，保存后生效')
    },
    loadProducts () {
      getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        this.products = this.listOf(res)
      })
    },
    onProductChange (productId) {
      this.form.project_id = ''
      this.projects = []
      this.documents = []
      if (!productId) return
      getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        this.projects = this.listOf(res)
      })
    },
    onProjectChange (projectId) {
      this.documents = []
      this.form.mock_document_id = null
      if (!projectId) return
      getMockDocumentList({ projectId, pageNo: 1, pageSize: 200 }).then(res => {
        this.documents = this.listOf(res)
      }).catch(() => {
        getMockDocumentList({ project_id: projectId, page_no: 1, page_size: 200 }).then(res => {
          this.documents = this.listOf(res)
        })
      })
    },
    loadDetail (id) {
      getContractSuiteDetail(id).then(res => {
        const data = this.dataOf(res)
        this.form = Object.assign({}, this.form, data, {
          items: (data.items || []).map(it => Object.assign({}, it, {
            enabled: it.enabled == null ? 1 : it.enabled
          }))
        })
        this.enabledSwitch = data.enabled === 1
        this.headersText = JSON.stringify(data.default_headers || {}, null, 2)
        if (data.product_id) {
          getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId: data.product_id }).then(r => {
            this.projects = this.listOf(r)
          })
          if (data.project_id) {
            getMockDocumentList({ projectId: data.project_id, pageNo: 1, pageSize: 200 }).then(r => {
              this.documents = this.listOf(r)
            }).catch(() => {})
          }
        }
      })
    },
    preview () {
      this.previewing = true
      const payload = { source_type: this.form.source_type }
      if (this.form.source_type === 'mock_document') {
        payload.mock_document_id = this.form.mock_document_id
      } else {
        payload.openapi_content = this.form.openapi_content
      }
      previewContractSource(payload).then(res => {
        const data = this.dataOf(res)
        this.form.items = (data.interfaces || []).map((it, idx) => ({
          mock_interface_id: it.mock_interface_id,
          name: it.name,
          method: it.method,
          path: it.path,
          response_schema: it.response_schema || {},
          path_params: {},
          query_params: {},
          body_template: null,
          enabled: 1,
          sort_order: idx
        }))
        this.$message.success('已加载 ' + this.form.items.length + ' 个接口')
      }).finally(() => { this.previewing = false })
    },
    onSelect (rows) {
      this.selectedRows = rows
      const selected = new Set(rows.map(r => r.path + '|' + r.method))
      this.form.items.forEach(it => {
        it.enabled = selected.has(it.path + '|' + it.method) ? 1 : 0
      })
    },
    submit () {
      this.$refs.form.validate(valid => {
        if (!valid) return
        let headers = {}
        try {
          headers = JSON.parse(this.headersText || '{}')
        } catch (e) {
          this.$message.error('Headers 必须是合法 JSON')
          return
        }
        if (!this.form.items.length) {
          this.$message.warning('请先加载并选择接口，或用 AI 设计添加')
          return
        }
        const payload = Object.assign({}, this.form, {
          default_headers: headers,
          enabled: this.enabledSwitch ? 1 : 0,
          items: this.form.items
        })
        this.saving = true
        const req = payload.id ? updateContractSuite(payload) : createContractSuite(payload)
        req.then(() => {
          this.$message.success('保存成功')
          this.$router.push('/contract/suites')
        }).finally(() => { this.saving = false })
      })
    }
  }
}
</script>

<style scoped>
.table-title { margin: 16px 0 8px; font-weight: 600; display: flex; align-items: center; }
.tip { color: #909399; font-size: 12px; margin-top: 8px; }
.ai-draft { margin-top: 8px; padding-top: 8px; border-top: 1px solid #ebeef5; font-size: 13px; }
</style>
