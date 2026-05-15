<template>
  <!-- Config Loading State -->
  <div v-if="isConfigLoading" class="config-loading">
    <div class="spinner"></div>
    <p>Connecting to backend...</p>
  </div>
  
  <!-- Main App -->
  <div v-else id="app">
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
import { storeToRefs } from 'pinia'
import { useScannerStore } from './stores/scanner'
import Notification from './components/Notification.vue'
import ScanForm from './components/ScanForm.vue'
import ScanProgress from './components/ScanProgress.vue'
import PrinterSearch from './components/PrinterSearch.vue'
import FileBrowser from './components/FileBrowser.vue'
import PrinterInfo from './components/PrinterInfo.vue'
import BulkScanModal from './components/BulkScanModal.vue'

const store = useScannerStore()
const { isConfigLoading } = storeToRefs(store)

// Initialize on mount
onMounted(async () => {
  // Fetch configuration from backend first
  await store.fetchConfig()
  // Then fetch files
  await store.fetchFiles()
})
</script>

<style scoped>
.config-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #fff;
}

.config-loading p {
  margin-top: 1rem;
  font-size: 1.1rem;
  color: #a0a0a0;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-left-color: #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
