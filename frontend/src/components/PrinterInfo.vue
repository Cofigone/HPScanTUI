<template>
  <div class="card">
    <div class="card-header">
      <h2 class="card-title">Printer Information</h2>
      <button
        class="btn btn-outline btn-sm"
        @click="fetchCapabilities"
        :disabled="!store.config.ip || isLoading"
      >
        {{ isLoading ? 'Loading...' : 'Get Info' }}
      </button>
    </div>

    <!-- Capabilities Display -->
    <div v-if="store.capabilities" class="capabilities-grid">
      <div class="capability-item">
        <div class="capability-label">Make & Model</div>
        <div class="capability-value">{{ store.capabilities.make_and_model }}</div>
      </div>
      <div class="capability-item">
        <div class="capability-label">Serial Number</div>
        <div class="capability-value">{{ store.capabilities.serial_number }}</div>
      </div>
      <div class="capability-item">
        <div class="capability-label">Manufacturer</div>
        <div class="capability-value">{{ store.capabilities.manufacturer }}</div>
      </div>
      <div class="capability-item">
        <div class="capability-label">Firmware</div>
        <div class="capability-value">{{ store.capabilities.firmware_version }}</div>
      </div>
      <div class="capability-item">
        <div class="capability-label">Max Width</div>
        <div class="capability-value">{{ store.capabilities.max_width }} px</div>
      </div>
      <div class="capability-item">
        <div class="capability-label">Max Height</div>
        <div class="capability-value">{{ store.capabilities.max_height }} px</div>
      </div>
      <div class="capability-item capability-full">
        <div class="capability-label">Color Modes</div>
        <div class="capability-value">{{ store.capabilities.color_modes?.join(', ') }}</div>
      </div>
      <div class="capability-item capability-full">
        <div class="capability-label">Resolutions</div>
        <div class="capability-value">{{ store.capabilities.supported_resolutions?.join(', ') }} DPI</div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <div class="empty-state-icon">🖨️</div>
      <p>Enter a printer IP and click "Get Info" to view printer capabilities.</p>
    </div>

    <!-- Error -->
    <div v-if="error" class="status-message status-error">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useScannerStore } from '../stores/scanner'

const store = useScannerStore()
const isLoading = ref(false)
const error = ref(null)

const fetchCapabilities = async () => {
  isLoading.value = true
  error.value = null
  
  const success = await store.fetchCapabilities()
  
  if (!success) {
    error.value = store.error
  }
  
  isLoading.value = false
}
</script>

<style scoped>
.capability-full {
  grid-column: span 2;
}
</style>
