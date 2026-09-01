<template>
  <div class="page-wrap ai-review-page">
    <page-section title="新建AI测试评审">
      <template slot="extra">
        <el-button size="small" @click="$router.push({ path: '/ai-review' })">返回列表</el-button>
      </template>
      <el-form ref="form" :model="form" :rules="rules" label-width="120px" size="small" class="review-form">
        <el-form-item label="产品" prop="productId">
          <el-select v-model="form.productId" clearable filterable placeholder="选择产品" style="width:100%;" @change="onProductChange">
            <el-option v-for="item in productOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目" prop="projectId">
          <el-select v-model="form.projectId" clearable filterable :disabled="!form.productId" placeholder="选择项目" style="width:100%;">
            <el-option v-for="item in projectOptions" :key="item.id" :label="item.name" :value="String(item.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model.trim="form.title" maxlength="120" show-word-limit />
        </el-form-item>
        <el-form-item label="评审类型" prop="reviewType">
          <el-select v-model="form.reviewType" placeholder="选择评审类型" style="width:100%;">
            <el-option v-for="item in reviewTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源类型" prop="sourceType">
          <el-select v-model="form.sourceType" placeholder="选择来源类型" style="width:100%;">
            <el-option v-for="item in sourceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.sourceType !== 'manual'" label="来源ID" prop="sourceId">
          <el-input v-model.trim="form.sourceId" placeholder="输入文档、精准测试分析、用例或缺陷ID" />
        </el-form-item>
        <el-form-item v-if="form.sourceType === 'manual' || form.sourceType === 'release'" label="评审内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="8" placeholder="输入需求、变更说明、发布说明或需要AI评审的内容" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="submit">创建评审</el-button>
          <el-button :disabled="saving" @click="$router.push({ path: '/ai-review' })">取消</el-button>
        </el-form-item>
      </el-form>
    </page-section>
  </div>
</template>

<script>
import PageSection from '@/components/TestPlatform/common/PageSection'
import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'
import { createAiReview } from '@/api/aiReviewApi'

const REVIEW_TYPES = [
  { value: 'requirement', label: '需求评审' },
  { value: 'change', label: '变更评审' },
  { value: 'case', label: '用例评审' },
  { value: 'bug', label: '缺陷评审' },
  { value: 'release', label: '发布评审' }
]
const SOURCE_TYPES = [
  { value: 'manual', label: '手工输入' },
  { value: 'document', label: '需求文档' },
  { value: 'precise_analysis', label: '精准测试' },
  { value: 'case', label: '测试用例' },
  { value: 'bug', label: '缺陷' },
  { value: 'release', label: '发布' }
]

export default {
  name: 'AiReviewCreate',
  components: { PageSection },
  data() {
    return {
      saving: false,
      productOptions: [],
      projectOptions: [],
      reviewTypeOptions: REVIEW_TYPES,
      sourceTypeOptions: SOURCE_TYPES,
      form: { productId: '', projectId: '', title: '', reviewType: 'requirement', sourceType: 'manual', sourceId: '', content: '' },
      rules: {
        productId: [{ required: true, message: '请选择产品', trigger: 'change' }],
        projectId: [{ required: true, message: '请选择项目', trigger: 'change' }],
        title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
        reviewType: [{ required: true, message: '请选择评审类型', trigger: 'change' }],
        sourceType: [{ required: true, message: '请选择来源类型', trigger: 'change' }]
      }
    }
  },
  created() {
    this.loadProducts()
  },
  methods: {
    apiData(res) { return (res && res.data) || res || {} },
    loadProducts() { getProductList({ pageNo: 1, pageSize: 200 }).then(res => { const d = this.apiData(res); this.productOptions = d.list || d.items || [] }) },
    loadProjects(productId) { if (!productId) { this.projectOptions = []; return }; getProjectList({ productId, pageNo: 1, pageSize: 200 }).then(res => { const d = this.apiData(res); this.projectOptions = d.list || d.items || [] }) },
    onProductChange(productId) { this.form.projectId = ''; this.loadProjects(productId) },
    submit() {
      this.$refs.form.validate(valid => {
        if (!valid) return
        if (this.form.sourceType !== 'manual' && this.form.sourceType !== 'release' && !this.form.sourceId) {
          this.$message.warning('请输入来源ID')
          return
        }
        this.saving = true
        const product = this.productOptions.find(item => String(item.id) === String(this.form.productId))
        const project = this.projectOptions.find(item => String(item.id) === String(this.form.projectId))
        const payload = {
          productId: this.form.productId,
          productName: product ? product.name : '',
          projectId: this.form.projectId,
          projectName: project ? project.name : '',
          title: this.form.title,
          reviewType: this.form.reviewType,
          sourceType: this.form.sourceType,
          sourceId: this.form.sourceId,
          inputPayload: { content: this.form.content, title: this.form.title }
        }
        createAiReview(payload).then(res => {
          const data = this.apiData(res)
          const reviewId = data.reviewId || data.id
          this.$message.success('创建成功')
          this.$router.push({ path: '/ai-review/detail', query: { id: reviewId } })
        }).finally(() => { this.saving = false })
      })
    }
  }
}
</script>

<style scoped>
.review-form { max-width: 760px; }
</style>
