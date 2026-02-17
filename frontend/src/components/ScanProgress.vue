<template>
  <div class="card" v-if="store.isScanning || store.progress > 0">
    <div class="card-header">
      <h2 class="card-title">Scan Progress</h2>
    </div>

    <!-- Progress Bar -->
    <div class="progress-container">
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${store.progress}%` }"></div>
      </div>
      <div class="progress-text">{{ store.progress }}% - {{ store.status }}</div>
    </div>

    <!-- Status Message -->
    <div v-if="store.error" class="status-message status-error">
      {{ store.error }}
    </div>

    <!-- Result -->
    <div v-if="store.lastResult && !store.isScanning" class="status-message status-success">
      Scan saved: {{ store.lastResult.filename }}
    </div>
  </div>
</template>

<script setup>
import { useScannerStore } from '../stores/scanner'

const store = useScannerStore()
</script>

<style scoped>
/* Additional scoped styles if needed */
</style>
