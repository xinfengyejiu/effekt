<template>
  <div class="create-data">
    <div class="search">
      <el-form :inline="true" :model="queryForm" class="search" size="small" @submit.native.prevent>
        <el-form-item label="项目">
          <el-select
            v-model="queryForm.project"
            placeholder="请选择项目"
            clearable
            filterable>
            <el-option
              v-for="item in projectOptions"
              :key="item"
              :label="item"
              :value="item">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="环境">
          <el-select
            v-model="queryForm.runEnv"
            placeholder="请选择项目"
            clearable
            filterable>
            <el-option
              v-for="item in envOptions"
              :key="item"
              :label="item"
              :value="item">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="创建人">
          <el-input
            v-model="queryForm.creator"
            placeholder="请输入创建人"
            clearable
            @keyup.enter.native="search()">
          </el-input>
        </el-form-item>
        <el-form-item label="分组">
          <el-input
            v-model="queryForm.runGroup"
            placeholder="请输入分组"
            clearable
            @keyup.enter.native="search()">
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
          <el-button type="success" @click="addTask">新增</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="api-form">
      <el-table
        ref="table"
        v-loading="loading"
        :data="tableData"
        :header-cell-style="{textAlign: 'center'}"
        :stripe="true"
        :height="tableHeight"
        border>
        <el-table-column label="项目名称" prop="project" min-width="150"></el-table-column>
        <el-table-column label="运行环境" prop="run_env" width="120"></el-table-column>
        <el-table-column label="运行分组" prop="run_group" min-width="150"></el-table-column>
        <el-table-column label="SQL语句" prop="sql" min-width="220">
          <template slot-scope="props">
            <el-tooltip v-if="props.row.sql && props.row.sql.length > 40" :content="props.row.sql" placement="top">
              <span>{{ formatSql(props.row.sql) }}</span>
            </el-tooltip>
            <span v-else>{{ props.row.sql || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="备注" prop="remark" min-width="180" :show-overflow-tooltip="true"></el-table-column>
        <el-table-column label="创建人" prop="creator" width="120"></el-table-column>
        <el-table-column label="创建时间" prop="created_time" min-width="170"></el-table-column>
        <el-table-column label="操作" align="center" width="280" fixed="right">
          <template slot-scope="props">
            <el-button type="text" @click="editTask(props.row)">编辑</el-button>
            <el-button type="text" @click="viewDetail(props.row)">查看详情</el-button>
            <el-button type="text" style="color: #F56C6C;" @click="deleteTask(props.row)">删除</el-button>
            <el-button type="text" :loading="runningId === getRowId(props.row)" @click="runTask(props.row)">执行</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="block">
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="pageNo"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total">
      </el-pagination>
    </div>

    <el-dialog title="任务详情" :visible.sync="detailVisible" width="60%">
      <el-table v-if="detailRow" :data="detailItems" border>
        <el-table-column label="字段" prop="key" width="180"></el-table-column>
        <el-table-column label="值" prop="value" :show-overflow-tooltip="true"></el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog title="执行结果" :visible.sync="executeVisible" width="60%">
      <pre class="execute-result" v-html="executeResult"></pre>
    </el-dialog>
  </div>
</template>

<script>
import {ItApiDelete, ItApiDetail, ItApiList, ItApiRun} from '@/api/CreateDtapi'

export default {
  name: "CreateManage",
  data() {
    return {
      tableHeight: null,
      total: 0,
      tableData: [],
      pageNo: 1,
      pageSize: 10,
      loading: false,
      runningId: '',
      detailVisible: false,
      detailRow: null,
      executeVisible: false,
      executeResult: '',
      queryForm: {
        project: '',
        runEnv: '',
        creator: '',
        runGroup: ''
      },
      projectOptions: ['ZHYY', 'DLZ', 'JOYHUB', 'OA', 'APP'],
      envOptions: ['dev', 'st', 'pre']
    }
  },
  computed: {
    detailItems() {
      if (!this.detailRow) {
        return []
      }
      const fieldMap = [
        {label: '项目名称', keys: ['project']},
        {label: '运行环境', keys: ['runEnv', 'run_env']},
        {label: '运行分组', keys: ['runGroup', 'run_group']},
        {label: 'SQL语句', keys: ['sql']},
        {label: '备注', keys: ['remark']},
        {label: '创建时间', keys: ['createdTime', 'created_time']},
        {label: '更新时间', keys: ['updatedTime', 'updated_time']}
      ]
      return fieldMap.reduce((list, item) => {
        const value = this.getDetailValue(item.keys)
        if (value === '') {
          return list
        }
        list.push({
          key: item.label,
          value
        })
        return list
      }, [])
    }
  },
  methods: {
    handleSizeChange(val) {
      this.pageSize = val
      this.search()
    },
    handleCurrentChange(val) {
      this.pageNo = val
      this.search(true)
    },
    getList() {
      this.loading = true
      ItApiList(this.buildParams()).then(res => {
        const data = res.data || {}
        this.tableData = data.list || []
        this.total = data.total || data.totalCount || res.total || res.totalCount || this.tableData.length
      }).finally(() => {
        this.loading = false
      })
    },
    buildParams() {
      const params = {
        pageNo: this.pageNo,
        pageSize: this.pageSize
      }
      Object.keys(this.queryForm).forEach(key => {
        const value = this.queryForm[key]
        if (value !== '') {
          params[key] = value
        }
      })
      return params
    },
    search(keepPage) {
      if (!keepPage) {
        this.pageNo = 1
      }
      this.getList()
    },
    resetSearch() {
      this.queryForm = {
        project: '',
        runEnv: '',
        creator: '',
        runGroup: ''
      }
      this.search()
    },
    addTask() {
      this.$router.push({path: '/create/info'})
    },
    editTask(row) {
      const sqlId = this.getRowId(row)
      if (!sqlId) {
        this.$message({type: 'error', message: '缺少sqlId，无法编辑'})
        return
      }
      this.$router.push({path: '/create/info', query: {sqlId}})
    },
    viewDetail(row) {
      const sqlId = this.getRowId(row)
      if (!sqlId) {
        this.$message({type: 'error', message: '缺少sqlId，无法查看详情'})
        return
      }
      this.loading = true
      ItApiDetail({sqlId}).then(res => {
        const data = res && res.data ? res.data : {}
        this.detailRow = data
        this.detailVisible = true
      }).finally(() => {
        this.loading = false
      })
    },
    deleteTask(row) {
      const sqlId = this.getRowId(row)
      if (!sqlId) {
        this.$message({type: 'error', message: '缺少sqlId，无法删除'})
        return
      }
      this.$confirm('确认删除该条记录吗？', '提示', {
        type: 'warning'
      }).then(() => {
        ItApiDelete({sqlId: Number(sqlId) || sqlId}).then(res => {
          if (res && res.success === true) {
            this.$message({type: 'success', message: '删除成功'})
            if (this.tableData.length === 1 && this.pageNo > 1) {
              this.pageNo = this.pageNo - 1
            }
            this.getList()
          } else {
            this.$message({type: 'error', message: res.message || '删除失败'})
          }
        })
      }).catch(() => {})
    },
    runTask(row) {
      const sqlId = this.getRowId(row)
      if (!sqlId) {
        this.$message({type: 'error', message: '缺少sqlId，无法执行'})
        return
      }
      this.runningId = sqlId
      ItApiRun({sqlId}).then(res => {
        this.executeResult = this.formatJsonHtml(res && res.data)
        this.executeVisible = true
      }).catch(err => {
        this.$message({type: 'error', message: (err && err.message) || '执行失败'})
      }).finally(() => {
        this.runningId = ''
      })
    },
    escapeHtml(value) {
      return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
    },
    syntaxHighlight(json) {
      return this.escapeHtml(json).replace(/("(?:\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"\s*:?)|(\btrue\b|\bfalse\b)|(\bnull\b)|(-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
        let className = 'json-number'
        if (/^"/.test(match)) {
          className = /:$/.test(match) ? 'json-key' : 'json-string'
        } else if (/true|false/.test(match)) {
          className = 'json-boolean'
        } else if (/null/.test(match)) {
          className = 'json-null'
        }
        return '<span class="' + className + '">' + match + '</span>'
      })
    },
    formatJsonHtml(value) {
      if (typeof value === 'string') {
        try {
          return this.syntaxHighlight(JSON.stringify(JSON.parse(value), null, 2))
        } catch (e) {
          return this.syntaxHighlight(value)
        }
      }
      return this.syntaxHighlight(JSON.stringify(value || {}, null, 2))
    },
    getRowId(row) {
      return String(row.sqlId || row.sql_id || row.id || row.create_data_detail_id || row.createDataDetailId || row.apiId || '')
    },
    formatSql(sql) {
      if (!sql) {
        return '-'
      }
      return sql.length > 40 ? sql.substring(0, 40) + '...' : sql
    },
    getDetailValue(keys) {
      for (let i = 0; i < keys.length; i++) {
        const value = this.detailRow[keys[i]]
        if (value !== null && typeof value !== 'undefined' && value !== '') {
          return this.formatValue(value)
        }
      }
      return ''
    },
    formatValue(value) {
      if (value === null || typeof value === 'undefined') {
        return ''
      }
      if (typeof value === 'object') {
        return JSON.stringify(value)
      }
      return String(value)
    }
  },
  created() {
    this.tableHeight = document.getElementById("app").clientHeight - 183
    this.getList()
  }
}
</script>

<style scoped>
.api-form {
  text-align: center;
}

.execute-result {
  max-height: 500px;
  overflow: auto;
  margin: 0;
  padding: 16px;
  background: #1e293b;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-all;
  text-align: left;
  color: #e2e8f0;
  line-height: 1.6;
}

.execute-result ::v-deep .json-key {
  color: #93c5fd;
}

.execute-result ::v-deep .json-string {
  color: #86efac;
}

.execute-result ::v-deep .json-number {
  color: #f9a8d4;
}

.execute-result ::v-deep .json-boolean {
  color: #fcd34d;
}

.execute-result ::v-deep .json-null {
  color: #c4b5fd;
}
</style>

