<template>
  <div id="app">
    <!-- Header -->
    <header class="app-header">
      <h1>HP Scan Web</h1>
    </header>

    <!-- Notification -->
    <Notification 
      v-if="store.notification" 
      :message="store.notification.message" 
      :type="store.notification.type"
      @close="store.clearNotification()"
    />

    <!-- Main Content -->
    <main class="app-main">
      <div class="app-grid">
        <!-- Left Column: Scan Controls -->
        <div class="left-column">
          <!-- Scan Form -->
          <ScanForm />
          
          <!-- Scan Progress -->
          <ScanProgress />
          
          <!-- Printer Search -->
          <PrinterSearch />
        </div>

        <!-- Right Column: Files & Info -->
        <div class="right-column">
          <!-- File Browser -->
          <FileBrowser />
          
          <!-- Printer Capabilities -->
          <PrinterInfo />
        </div>
      </div>
    </main>

    <!-- Bulk Scan Modal -->
    <BulkScanModal />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useScannerStore } from './stores/scanner'
import Notification from './components/Notification.vue'
import ScanForm from './components/ScanForm.vue'
import ScanProgress from './components/ScanProgress.vue'
import PrinterSearch from './components/PrinterSearch.vue'
import FileBrowser from './components/FileBrowser.vue'
import PrinterInfo from './components/PrinterInfo.vue'
import BulkScanModal from './components/BulkScanModal.vue'

const store = useScannerStore()

// Initialize on mount
onMounted(async () => {
  // Fetch files on load
  await store.fetchFiles()
})
</script>

<style scoped>
/* Additional scoped styles if needed */
</style>
