<template>
  <div class="model-setting-panel">
    <el-form :model="form" label-width="120px" size="small">
      <el-form-item label="Provider">
        <el-select v-model="form.provider" placeholder="请选择">
          <el-option label="custom" value="custom" />
          <el-option label="openai" value="openai" />
        </el-select>
      </el-form-item>
      <el-form-item label="API Base">
        <el-input v-model="form.apiBase" placeholder="留空则使用服务端 .env 配置" />
      </el-form-item>
      <el-form-item label="问答模型">
        <el-input v-model="form.model" placeholder="留空则使用服务端默认模型" />
      </el-form-item>
      <el-form-item label="向量模型">
        <el-input v-model="form.embeddingModel" placeholder="如 text-embedding-3-small；不支持时自动本地兜底" />
      </el-form-item>
      <el-form-item label="Temperature">
        <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" />
      </el-form-item>
      <el-form-item label="Max Tokens">
        <el-input-number v-model="form.maxTokens" :min="256" :max="12000" :step="256" />
      </el-form-item>
      <el-form-item label="TopK">
        <el-input-number v-model="form.topK" :min="1" :max="20" />
      </el-form-item>
      <el-form-item label="Score阈值">
        <el-input-number v-model="form.scoreThreshold" :min="0" :max="1" :step="0.01" />
      </el-form-item>
      <el-form-item label="服务端Key">
        <el-switch v-model="form.useEnvKey" :active-value="1" :inactive-value="0" active-text="使用 .env" disabled />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
        <el-button :loading="testing" @click="test">测试连接</el-button>
      </el-form-item>
    </el-form>
    <el-alert title="安全说明：API Key 不在前端展示或保存，默认使用服务端 .env。" type="info" :closable="false" />
  </div>
</template>

<script>
import { getKnowledgeModelSetting, saveKnowledgeModelSetting, testKnowledgeModelSetting } from '@/api/knowledgeApi'

export default {
  name: 'ModelSettingPanel',
  props: {
    productId: [String, Number],
    projectId: [String, Number]
  },
  data() {
    return {
      saving: false,
      testing: false,
      form: {
        scopeType: 'project',
        scopeId: 0,
        provider: 'custom',
        apiBase: '',
        model: '',
        embeddingModel: 'text-embedding-3-small',
        temperature: 0.3,
        maxTokens: 2048,
        topK: 5,
        scoreThreshold: 0,
        useEnvKey: 1
      }
    }
  },
  watch: {
    projectId: {
      immediate: true,
      handler() {
        this.load()
      }
    }
  },
  methods: {
    scopeParams() {
      return { scopeType: 'project', scopeId: this.projectId || 0, projectId: this.projectId || 0 }
    },
    load() {
      if (!this.projectId) return
      getKnowledgeModelSetting(this.scopeParams()).then(res => {
        this.form = Object.assign({}, this.form, res.data || {}, this.scopeParams())
      })
    },
    save() {
      if (!this.projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      this.saving = true
      saveKnowledgeModelSetting(Object.assign({}, this.form, this.scopeParams())).then(() => {
        this.$message.success('模型设置已保存')
        this.$emit('saved', this.form)
      }).finally(() => {
        this.saving = false
      })
    },
    test() {
      if (!this.projectId) {
        this.$message.warning('请先选择项目')
        return
      }
      this.testing = true
      testKnowledgeModelSetting(Object.assign({}, this.form, this.scopeParams())).then(res => {
        const data = res.data || {}
        if (data.success) this.$message.success(data.message || '连接正常')
        else this.$message.error(data.message || '连接失败')
      }).finally(() => {
        this.testing = false
      })
    }
  }
}
</script>

<style scoped>
.model-setting-panel {
  max-width: 720px;
}
</style>
