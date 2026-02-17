<template>
  <div class="card">
    <div class="card-header">
      <h2 class="card-title">Printer Discovery</h2>
      <button
        class="btn btn-secondary btn-sm"
        @click="handleSearch"
        :disabled="store.isSearching"
      >
        <span v-if="store.isSearching" class="spinner"></span>
        {{ store.isSearching ? 'Searching...' : 'Search Network' }}
      </button>
    </div>

    <!-- Printer List -->
    <div v-if="store.discoveredPrinters.length > 0">
      <p class="form-label">Found {{ store.discoveredPrinters.length }} printer(s):</p>
      <ul class="printer-list">
        <li
          v-for="printer in store.discoveredPrinters"
          :key="printer"
          :class="['printer-item', { selected: store.config.ip === printer }]"
          @click="selectPrinter(printer)"
        >
          <span class="printer-icon">🖨️</span>
          <span class="printer-ip">{{ printer }}</span>
        </li>
      </ul>
    </div>

    <!-- Empty State -->
    <div v-else-if="!store.isSearching" class="empty-state">
      <p>Click "Search Network" to discover HP printers on your network.</p>
    </div>

    <!-- Searching State -->
    <div v-else class="empty-state">
      <span class="spinner"></span>
      <p>Scanning network for printers...</p>
    </div>
  </div>
</template>

<script setup>
import { useScannerStore } from '../stores/scanner'

const store = useScannerStore()

const handleSearch = async () => {
  await store.searchPrinters()
}

const selectPrinter = (ip) => {
  store.setPrinterIp(ip)
  store.showNotification(`Printer ${ip} selected`, 'success')
}
</script>

<style scoped>
.printer-icon {
  margin-right: var(--spacing-sm);
}

.printer-ip {
  font-family: monospace;
  font-size: 1rem;
}
</style>
