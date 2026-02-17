<template>
  <div class="card">
    <div class="card-header">
      <h2 class="card-title">Scan Configuration</h2>
    </div>

    <form @submit.prevent="handleScan">
      <!-- Printer IP -->
      <div class="form-group">
        <label class="form-label" for="printer-ip">Printer IP</label>
        <input
          id="printer-ip"
          type="text"
          class="form-input"
          v-model="localConfig.ip"
          placeholder="e.g., 192.168.1.100"
          :disabled="store.isScanning"
        />
      </div>

      <!-- DPI -->
      <div class="form-group">
        <label class="form-label" for="dpi">DPI (Resolution)</label>
        <select id="dpi" class="form-select" v-model="localConfig.dpi" :disabled="store.isScanning">
          <option :value="150">150 DPI (Draft)</option>
          <option :value="200">200 DPI (Standard)</option>
          <option :value="300">300 DPI (High Quality)</option>
          <option :value="600">600 DPI (Photo Quality)</option>
        </select>
      </div>

      <!-- Paper Format -->
      <div class="form-group">
        <label class="form-label" for="format">Paper Format</label>
        <select id="format" class="form-select" v-model="localConfig.format" :disabled="store.isScanning">
          <option value="A4">A4 (210 × 297 mm)</option>
          <option value="A5">A5 (148 × 210 mm)</option>
          <option value="Letter">Letter (8.5 × 11 in)</option>
        </select>
      </div>

      <!-- Color Mode -->
      <div class="form-group">
        <label class="form-label" for="colormode">Color Mode</label>
        <select id="colormode" class="form-select" v-model="localConfig.colormode" :disabled="store.isScanning">
          <option value="RGB24">Color (RGB24)</option>
          <option value="Grayscale8">Grayscale</option>
          <option value="BlackAndWhite1">Black & White</option>
        </select>
      </div>

      <!-- Output Format -->
      <div class="form-group">
        <label class="form-label">Output Format</label>
        <div class="toggle-group">
          <button
            type="button"
            :class="['toggle-btn', { active: localConfig.pdf }]"
            @click="localConfig.pdf = true"
            :disabled="store.isScanning"
          >
            PDF
          </button>
          <button
            type="button"
            :class="['toggle-btn', { active: !localConfig.pdf }]"
            @click="localConfig.pdf = false"
            :disabled="store.isScanning"
          >
            JPEG
          </button>
        </div>
      </div>

      <!-- Output Filename -->
      <div class="form-group">
        <label class="form-label" for="output">Filename (optional)</label>
        <input
          id="output"
          type="text"
          class="form-input"
          v-model="localConfig.output"
          placeholder="Leave empty for auto-generated name"
          :disabled="store.isScanning || store.isBulkScanning"
        />
      </div>

      <!-- Scan Buttons -->
      <div class="scan-buttons">
        <button
          type="submit"
          class="btn btn-primary btn-lg"
          :disabled="store.isScanning || store.isBulkScanning || !localConfig.ip"
        >
          <span v-if="store.isScanning" class="spinner"></span>
          {{ store.isScanning ? 'Scanning...' : 'Single Scan' }}
        </button>
        <button
          type="button"
          class="btn btn-secondary btn-lg"
          :disabled="store.isScanning || store.isBulkScanning || !localConfig.ip"
          @click="handleBulkScan"
        >
          Bulk Scan
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'
import { useScannerStore } from '../stores/scanner'

const store = useScannerStore()

// Local form state
const localConfig = reactive({
  ip: store.config.ip,
  dpi: store.config.dpi,
  format: store.config.format,
  colormode: store.config.colormode,
  pdf: store.config.pdf,
  output: store.config.output
})

// Watch for changes and update store
watch(localConfig, (newConfig) => {
  store.updateConfig(newConfig)
}, { deep: true })

// Handle single scan
const handleScan = async () => {
  await store.startScan()
}

// Handle bulk scan
const handleBulkScan = async () => {
  await store.startBulkScan()
}
</script>

<style scoped>
.scan-buttons {
  display: flex;
  gap: var(--spacing-md);
}

.scan-buttons .btn {
  flex: 1;
}
</style>
