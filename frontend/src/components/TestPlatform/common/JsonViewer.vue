<template>
  <pre class="json-viewer">{{ formattedValue }}</pre>
</template>

<script>
export default {
  name: 'JsonViewer',
  props: {
    value: {
      type: [Object, Array, String, Number, Boolean],
      default: () => ({})
    }
  },
  computed: {
    formattedValue() {
      if (typeof this.value === 'string') {
        try {
          return JSON.stringify(JSON.parse(this.value), null, 2)
        } catch (e) {
          return this.value
        }
      }
      return JSON.stringify(this.value || {}, null, 2)
    }
  }
}
</script>

<style scoped>
.json-viewer {
  margin: 0;
  padding: 16px;
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
}
</style>
