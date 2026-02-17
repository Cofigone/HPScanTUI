<template>
  <div class="modal-overlay" v-if="store.isBulkScanModalOpen">
    <div class="modal-content">
      <!-- Header -->
      <div class="modal-header">
        <h2 class="modal-title">
          Bulk Scan - {{ store.bulkScanPages.length }} page(s) scanned
        </h2>
        <button class="modal-close" @click="handleCancel">&times;</button>
      </div>

      <!-- Body -->
      <div class="modal-body">
        <!-- Page Thumbnails -->
        <div class="pages-container">
          <!-- Existing Pages -->
          <div
            v-for="page in store.bulkScanPages"
            :key="page.pageNumber"
            class="page-thumbnail"
          >
            <img
              :src="getPreviewUrl(page.pageNumber)"
              :alt="`Page ${page.pageNumber}`"
              class="thumbnail-image"
            />
            <div class="page-number">Page {{ page.pageNumber }}</div>
            <button
              class="delete-page-btn"
              @click="handleDeletePage(page.pageNumber)"
              :disabled="store.bulkScanPageInProgress"
            >
              &times;
            </button>
          </div>

          <!-- Add Page Button -->
          <div class="page-thumbnail add-page" @click="handleScanPage">
            <div v-if="store.bulkScanPageInProgress" class="scanning-indicator">
              <span class="spinner"></span>
              <span>Scanning...</span>
            </div>
            <template v-else>
              <div class="add-icon">+</div>
              <div class="add-text">Scan Page</div>
            </template>
          </div>
        </div>

        <!-- Status Message -->
        <div v-if="store.error" class="status-message status-error">
          {{ store.error }}
        </div>
        <div v-else-if="store.bulkScanPageInProgress" class="status-message status-info">
          Scanning page {{ store.bulkScanPages.length + 1 }}...
        </div>
        <div v-else class="status-message status-info">
          Ready to scan page {{ store.bulkScanPages.length + 1 }}
        </div>

        <!-- Filename Input -->
        <div class="form-group">
          <label class="form-label" for="bulk-filename">Filename (optional)</label>
          <input
            id="bulk-filename"
            type="text"
            class="form-input"
            v-model="outputFilename"
            placeholder="Leave empty for auto-generated name"
          />
        </div>
      </div>

      <!-- Footer -->
      <div class="modal-footer">
        <button
          class="btn btn-outline"
          @click="handleCancel"
          :disabled="store.bulkScanPageInProgress"
        >
          Cancel
        </button>
        <button
          class="btn btn-primary"
          @click="handleFinish"
          :disabled="store.bulkScanPageInProgress || store.bulkScanPages.length === 0"
        >
          Save PDF
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useScannerStore } from '../stores/scanner'

const store = useScannerStore()
const outputFilename = ref('')

const getPreviewUrl = (pageNum) => {
  if (store.bulkScanSession) {
    return `/api/scanner/bulk/preview/${store.bulkScanSession}/${pageNum}`
  }
  return ''
}

const handleScanPage = async () => {
  await store.scanBulkPage()
}

const handleDeletePage = async (pageNum) => {
  if (confirm(`Delete page ${pageNum}?`)) {
    await store.deleteBulkPage(pageNum)
  }
}

const handleFinish = async () => {
  await store.finishBulkScan(outputFilename.value || null)
}

const handleCancel = async () => {
  if (store.bulkScanPages.length > 0) {
    if (confirm('Are you sure you want to cancel? All scanned pages will be discarded.')) {
      await store.cancelBulkScan()
    }
  } else {
    await store.cancelBulkScan()
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--card-bg);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: modalSlideIn 0.3s ease;
}

@keyframes modalSlideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--primary-color);
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--text-muted);
  line-height: 1;
}

.modal-close:hover {
  color: var(--text-color);
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.pages-container {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.page-thumbnail {
  width: 120px;
  height: 160px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
  position: relative;
  background: var(--bg-color);
}

.thumbnail-image {
  width: 100%;
  height: 120px;
  object-fit: cover;
}

.page-number {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: var(--spacing-xs);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  font-size: 0.75rem;
  text-align: center;
}

.delete-page-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--danger-color);
  color: white;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.page-thumbnail:hover .delete-page-btn {
  opacity: 1;
}

.delete-page-btn:hover {
  background: #c0392b;
}

.add-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-style: dashed;
  transition: all 0.2s;
}

.add-page:hover {
  border-color: var(--primary-color);
  background: rgba(0, 150, 214, 0.05);
}

.add-icon {
  font-size: 3rem;
  color: var(--primary-color);
  line-height: 1;
}

.add-text {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-top: var(--spacing-sm);
}

.scanning-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
  color: var(--primary-color);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--border-color);
}

@media (max-width: 600px) {
  .modal-content {
    width: 95%;
    max-height: 95vh;
  }

  .page-thumbnail {
    width: 100px;
    height: 140px;
  }

  .thumbnail-image {
    height: 100px;
  }
}
</style>
