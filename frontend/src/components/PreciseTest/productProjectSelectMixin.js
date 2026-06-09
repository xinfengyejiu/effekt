import { getProductList } from '@/api/productApi'
import { getProjectList } from '@/api/projectApi'

export default {
  data() {
    return {
      productOptions: [],
      projectOptions: [],
      queryProjectOptions: [],
      rowProjectOptions: []
    }
  },
  created() {
    this.loadProductOptions()
  },
  methods: {
    normalizeList(res) {
      const d = res && res.data ? res.data : res || {}
      return d.items || d.list || d.data || []
    },
    loadProductOptions() {
      return getProductList({ pageNo: 1, pageSize: 1000, status: 1 }).then(res => {
        this.productOptions = this.normalizeList(res)
      })
    },
    loadProjectOptions(productId, targetKey) {
      const key = targetKey || 'projectOptions'
      if (!productId) {
        this[key] = []
        return Promise.resolve([])
      }
      return getProjectList({ pageNo: 1, pageSize: 1000, status: 1, productId }).then(res => {
        const rows = this.normalizeList(res)
        if (key === 'rowProjectOptions') {
          const exists = new Set((this.rowProjectOptions || []).map(item => String(item.id)))
          this.rowProjectOptions = (this.rowProjectOptions || []).concat(rows.filter(item => !exists.has(String(item.id))))
        } else {
          this[key] = rows
        }
        return this[key]
      })
    },
    preciseProductName(row) {
      const directName = row.product_name || row.productName
      if (directName) return directName
      const productId = row.product_id || row.productId
      const product = (this.productOptions || []).find(item => String(item.id) === String(productId))
      return product ? product.name : '-'
    },
    preciseProjectName(row) {
      const directName = row.project_name || row.projectName
      if (directName) return directName
      const projectId = row.project_id || row.projectId
      const pools = [].concat(this.queryProjectOptions || [], this.projectOptions || [], this.rowProjectOptions || [])
      const project = pools.find(item => String(item.id) === String(projectId))
      return project ? project.name : '-'
    },
    fillPreciseProjectNames(rows) {
      const productIds = Array.from(new Set((rows || []).map(row => row.product_id || row.productId).filter(Boolean)))
      productIds.forEach(productId => {
        this.loadProjectOptions(productId, 'rowProjectOptions')
      })
    },
    buildPreciseProjectPayload(form) {
      const product = (this.productOptions || []).find(item => String(item.id) === String(form.productId))
      const project = (this.projectOptions || []).find(item => String(item.id) === String(form.projectId))
      return Object.assign({}, form, {
        productName: product ? product.name : '',
        product_name: product ? product.name : '',
        projectName: project ? project.name : '',
        project_name: project ? project.name : ''
      })
    }
  }
}
