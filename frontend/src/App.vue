<template>
  <div id="app">
    <router-view/>
  </div>
</template>

<script>
import { getRoleList, parseMenusFromRoleListResponse } from '@/api/rbacApi'

export default {
  name: 'App',
  mounted() {
    this.applyTheme()
    const authUser = JSON.parse(localStorage.getItem('authUser') || 'null')
    const userMenus = JSON.parse(localStorage.getItem('userMenus') || '[]')
    if (authUser) {
      this.$store.commit('SetCurrentUser', authUser)
      this.$store.commit('SetRole', authUser.roleIds || [])
      this.$store.commit('SetUserMenus', userMenus)
      this.loadUserMenus(authUser)
    }
  },
  methods: {
    applyTheme() {
      const theme = localStorage.getItem('uiTheme') || 'light'
      document.body.classList.remove('theme-dark', 'theme-light')
      document.body.classList.add(theme === 'dark' ? 'theme-dark' : 'theme-light')
    },
    loadUserMenus(authUser) {
      const roleId = authUser && authUser.roleIds && authUser.roleIds.length ? authUser.roleIds[0] : undefined
      if (!roleId) {
        return
      }
      getRoleList({ roleId }).then(res => {
        this.$store.commit('SetUserMenus', parseMenusFromRoleListResponse(res))
      }).catch(() => {})
    }
  }
}
</script>

<style>
html,
body {
  height: 100%;
  margin: 0;
  overflow: hidden;
  background: #fafbfc;
  color: #111827;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
}

#app{
  height: 100%;
  overflow: hidden;
}

* {
  box-sizing: border-box;
}

button,
.el-button,
.el-link,
.el-menu-item,
.el-submenu__title {
  cursor: pointer;
}

/* Element UI 主色覆盖 */
.el-button--primary {
  background-color: #1e40af;
  border-color: #1e40af;
}
.el-button--primary:hover,
.el-button--primary:focus {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
}
.el-button--warning {
  background-color: #f97316;
  border-color: #f97316;
}
.el-button--warning:hover,
.el-button--warning:focus {
  background-color: #ea580c;
  border-color: #ea580c;
}
.el-link--primary {
  color: #1e40af;
}
.el-checkbox__input.is-checked .el-checkbox__inner,
.el-radio__input.is-checked .el-radio__inner {
  background: #1e40af;
  border-color: #1e40af;
}
.el-checkbox__input.is-checked + .el-checkbox__label,
.el-radio__input.is-checked + .el-radio__label {
  color: #1e40af;
}
.el-switch.is-checked .el-switch__core {
  background-color: #1e40af;
  border-color: #1e40af;
}

/* ========== Light Theme (Default) ========== */
.el-card {
  border-color: #e5e7eb;
  background: #ffffff;
  color: #111827;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.el-table,
.el-table__expanded-cell {
  background-color: #ffffff !important;
  color: #111827 !important;
}

.el-table th,
.el-table tr,
.el-table td {
  background-color: #ffffff !important;
  color: #111827 !important;
}

.el-table th,
.el-table thead,
.el-table__header-wrapper th,
.el-table__fixed-header-wrapper th {
  background: #f9fafb !important;
  color: #374151 !important;
  font-weight: 600;
}

.el-table .cell,
.el-table th > .cell,
.el-table__body-wrapper,
.el-table__fixed-body-wrapper {
  color: inherit !important;
}

.el-table td,
.el-table th.is-leaf {
  border-bottom-color: #e5e7eb !important;
}

.el-table--border,
.el-table--group,
.el-table--border td,
.el-table--border th,
.el-table__fixed-right-patch {
  border-color: #e5e7eb !important;
}

.el-table--striped .el-table__body tr.el-table__row--striped td {
  background-color: #f9fafb !important;
  color: #111827 !important;
}

.el-table--enable-row-hover .el-table__body tr:hover > td,
.el-table__body tr.hover-row > td,
.el-table__body tr.hover-row.current-row > td,
.el-table__body tr.hover-row.el-table__row--striped > td,
.el-table__body tr.hover-row.el-table__row--striped.current-row > td {
  background-color: #fff7ed !important;
  color: #111827 !important;
}

.el-table__body tr.current-row > td,
.el-table__body tr.current-row:hover > td {
  background-color: #fff7ed !important;
  color: #111827 !important;
}

.el-table__fixed,
.el-table__fixed-right,
.el-table__fixed::before,
.el-table__fixed-right::before {
  background-color: #ffffff !important;
}

.el-table::before,
.el-table--group::after,
.el-table--border::after {
  background-color: #e5e7eb !important;
}

.el-form-item__label,
.el-checkbox,
.el-radio,
.el-dialog__body,
.el-pagination,
.el-pagination button,
.el-pagination span:not([class*=suffix]),
.el-select-dropdown__item,
.el-dropdown-menu__item {
  color: #6b7280;
}

.el-input__inner,
.el-textarea__inner,
.el-select .el-input__inner,
.el-date-editor .el-input__inner {
  background-color: #ffffff;
  border-color: #d1d5db;
  color: #111827;
}

.el-input__inner::placeholder,
.el-textarea__inner::placeholder {
  color: #9ca3af;
}

.el-input__inner:hover,
.el-textarea__inner:hover {
  border-color: #9ca3af;
}

.el-input__inner:focus,
.el-textarea__inner:focus {
  border-color: #1e40af;
}

.el-dialog,
.el-drawer,
.el-message-box {
  background: #ffffff;
  color: #111827;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
}

.el-dialog__title,
.el-message-box__title {
  color: #111827;
}

.el-dialog__header,
.el-dialog__footer,
.el-message-box__header,
.el-message-box__content {
  border-color: #e5e7eb;
}

.el-select-dropdown,
.el-dropdown-menu,
.el-picker-panel {
  background: #ffffff;
  border-color: #e5e7eb;
  color: #111827;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover,
.el-dropdown-menu__item:hover {
  background-color: #fff7ed;
  color: #1e40af;
}

.el-select-dropdown__item.selected {
  color: #1e40af;
  font-weight: 600;
}

.el-pagination .btn-prev,
.el-pagination .btn-next,
.el-pager li {
  background: #ffffff;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.el-pager li.active {
  color: #1e40af;
  border-color: #1e40af;
}

.el-tag:not(.el-tag--success):not(.el-tag--warning):not(.el-tag--danger):not(.el-tag--info) {
  border-color: #bfdbfe;
  background: #eff6ff;
  color: #1e40af;
}

.el-tag.el-tag--success {
  border-color: #a7f3d0;
  background: #ecfdf5;
  color: #059669;
}

.el-tag.el-tag--warning {
  border-color: #fed7aa;
  background: #fff7ed;
  color: #d97706;
}

.el-tag.el-tag--danger {
  border-color: #fecaca;
  background: #fef2f2;
  color: #dc2626;
}

.el-tag.el-tag--info {
  border-color: #e5e7eb;
  background: #f9fafb;
  color: #6b7280;
}

.el-card__header {
  background: #f9fafb;
  border-bottom-color: #e5e7eb;
  color: #111827;
}

.el-tabs__item {
  color: #9ca3af;
}

.el-tabs__item:hover,
.el-tabs__item.is-active {
  color: #1e40af;
}

.el-tabs__active-bar {
  background-color: #1e40af;
}

.el-tabs__nav-wrap::after {
  background-color: #e5e7eb;
}

.el-popover,
.el-tooltip__popper.is-light {
  background: #ffffff;
  border-color: #e5e7eb;
  color: #111827;
}

.el-tree,
.el-tree-node__content {
  background: transparent;
  color: #111827;
}

.el-tree-node__content:hover,
.el-tree-node:focus > .el-tree-node__content {
  background-color: #f9fafb;
  color: #1e40af;
}

.el-tree-node.is-current > .el-tree-node__content {
  background-color: #eff6ff;
  color: #1e40af;
}

.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.8);
}

/* ========== Dark Theme (Optional) ========== */
body.theme-dark {
  background: #111827;
  color: #f9fafb;
}

body.theme-dark .el-card {
  border-color: #374151;
  background: #1f2937;
  color: #f9fafb;
  box-shadow: none;
}

body.theme-dark .el-table,
body.theme-dark .el-table__expanded-cell {
  background-color: #1f2937 !important;
  color: #f9fafb !important;
}

body.theme-dark .el-table th,
body.theme-dark .el-table tr,
body.theme-dark .el-table td {
  background-color: #1f2937 !important;
  color: #f9fafb !important;
}

body.theme-dark .el-table th,
body.theme-dark .el-table thead,
body.theme-dark .el-table__header-wrapper th,
body.theme-dark .el-table__fixed-header-wrapper th {
  background: #374151 !important;
  color: #f9fafb !important;
}

body.theme-dark .el-table--striped .el-table__body tr.el-table__row--striped td {
  background-color: #1f2937 !important;
}

body.theme-dark .el-table--enable-row-hover .el-table__body tr:hover > td,
body.theme-dark .el-table__body tr.hover-row > td {
  background-color: #374151 !important;
  color: #f9fafb !important;
}

body.theme-dark .el-table td,
body.theme-dark .el-table th.is-leaf,
body.theme-dark .el-table--border,
body.theme-dark .el-table--group,
body.theme-dark .el-table--border td,
body.theme-dark .el-table--border th,
body.theme-dark .el-table__fixed-right-patch {
  border-color: #374151 !important;
}

body.theme-dark .el-table__fixed,
body.theme-dark .el-table__fixed-right,
body.theme-dark .el-table__fixed::before,
body.theme-dark .el-table__fixed-right::before {
  background-color: #1f2937 !important;
}

body.theme-dark .el-table::before,
body.theme-dark .el-table--group::after,
body.theme-dark .el-table--border::after {
  background-color: #374151 !important;
}

body.theme-dark .el-form-item__label,
body.theme-dark .el-checkbox,
body.theme-dark .el-radio,
body.theme-dark .el-dialog__body,
body.theme-dark .el-pagination,
body.theme-dark .el-pagination button,
body.theme-dark .el-pagination span:not([class*=suffix]),
body.theme-dark .el-select-dropdown__item,
body.theme-dark .el-dropdown-menu__item {
  color: #d1d5db;
}

body.theme-dark .el-input__inner,
body.theme-dark .el-textarea__inner,
body.theme-dark .el-select .el-input__inner,
body.theme-dark .el-date-editor .el-input__inner {
  background-color: #111827;
  border-color: #374151;
  color: #f9fafb;
}

body.theme-dark .el-input__inner::placeholder,
body.theme-dark .el-textarea__inner::placeholder {
  color: #6b7280;
}

body.theme-dark .el-input__inner:hover,
body.theme-dark .el-textarea__inner:hover {
  border-color: #6b7280;
}

body.theme-dark .el-input__inner:focus,
body.theme-dark .el-textarea__inner:focus {
  border-color: #3b82f6;
}

body.theme-dark .el-dialog,
body.theme-dark .el-drawer,
body.theme-dark .el-message-box,
body.theme-dark .el-select-dropdown,
body.theme-dark .el-dropdown-menu,
body.theme-dark .el-picker-panel,
body.theme-dark .el-popover,
body.theme-dark .el-tooltip__popper.is-light {
  background: #1f2937;
  border-color: #374151;
  color: #f9fafb;
}

body.theme-dark .el-dialog__title,
body.theme-dark .el-message-box__title {
  color: #f9fafb;
}

body.theme-dark .el-dialog__header,
body.theme-dark .el-dialog__footer,
body.theme-dark .el-message-box__header,
body.theme-dark .el-message-box__content {
  border-color: #374151;
}

body.theme-dark .el-card__header {
  background: #374151;
  border-bottom-color: #374151;
  color: #f9fafb;
}

body.theme-dark .el-select-dropdown__item.hover,
body.theme-dark .el-select-dropdown__item:hover,
body.theme-dark .el-dropdown-menu__item:hover,
body.theme-dark .el-tree-node__content:hover,
body.theme-dark .el-tree-node:focus > .el-tree-node__content {
  background-color: #374151;
  color: #f9fafb;
}

body.theme-dark .el-select-dropdown__item.selected {
  color: #3b82f6;
}

body.theme-dark .el-pagination .btn-prev,
body.theme-dark .el-pagination .btn-next,
body.theme-dark .el-pager li {
  background: #1f2937;
  color: #d1d5db;
  border-color: #374151;
}

body.theme-dark .el-pager li.active {
  color: #3b82f6;
  border-color: #3b82f6;
}

body.theme-dark .el-tabs__item {
  color: #9ca3af;
}

body.theme-dark .el-tabs__item:hover,
body.theme-dark .el-tabs__item.is-active {
  color: #3b82f6;
}

body.theme-dark .el-tabs__nav-wrap::after {
  background-color: #374151;
}

body.theme-dark .el-tag:not(.el-tag--success):not(.el-tag--warning):not(.el-tag--danger):not(.el-tag--info) {
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(59, 130, 246, 0.12);
  color: #93c5fd;
}

body.theme-dark .el-tag.el-tag--success {
  border-color: rgba(5, 150, 105, 0.4);
  background: rgba(5, 150, 105, 0.15);
  color: #6ee7b7;
}

body.theme-dark .el-tag.el-tag--warning {
  border-color: rgba(217, 119, 6, 0.4);
  background: rgba(217, 119, 6, 0.15);
  color: #fcd34d;
}

body.theme-dark .el-tag.el-tag--danger {
  border-color: rgba(220, 38, 38, 0.4);
  background: rgba(220, 38, 38, 0.15);
  color: #fca5a5;
}

body.theme-dark .el-tag.el-tag--info {
  border-color: #374151;
  background: rgba(107, 114, 128, 0.15);
  color: #d1d5db;
}

body.theme-dark .el-tree,
body.theme-dark .el-tree-node__content {
  color: #f9fafb;
}

body.theme-dark .el-loading-mask {
  background-color: rgba(17, 24, 39, 0.72);
}
</style>
