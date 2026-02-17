<template>
  <div class="card">
    <div class="card-header">
      <h2 class="card-title">Scanned Files</h2>
      <button class="btn btn-outline btn-sm" @click="refreshFiles" :disabled="store.isLoadingFiles">
        {{ store.isLoadingFiles ? 'Loading...' : 'Refresh' }}
      </button>
    </div>

    <!-- File List -->
    <div v-if="store.files.length > 0">
      <ul class="file-list">
        <li v-for="file in store.files" :key="file.name" class="file-item">
          <div class="file-info">
            <span class="file-name">
              <span v-if="file.extension === '.pdf'">📄</span>
              <span v-else>🖼️</span>
              {{ file.name }}
            </span>
            <span class="file-meta">
              {{ file.size_formatted }} • {{ formatDate(file.modified) }}
            </span>
          </div>
          <div class="file-actions">
            <a
              :href="getDownloadUrl(file.name)"
              class="btn btn-primary btn-sm"
              target="_blank"
            >
              Download
            </a>
            <button
              class="btn btn-danger btn-sm"
              @click="handleDelete(file.name)"
            >
              Delete
            </button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <div class="empty-state-icon">📁</div>
      <p>No scanned files yet.</p>
      <p>Start a scan to create your first file.</p>
    </div>
  </div>
</template>

<script setup>
import { useScannerStore } from '../stores/scanner'
import { filesApi } from '../services/api'

const store = useScannerStore()

const refreshFiles = () => {
  store.fetchFiles()
}

const getDownloadUrl = (filename) => {
  return filesApi.getDownloadUrl(filename)
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString()
}

const handleDelete = async (filename) => {
  if (confirm(`Are you sure you want to delete "${filename}"?`)) {
    await store.deleteFile(filename)
  }
}
</script>

<style scoped>
.file-list {
  max-height: 400px;
  overflow-y: auto;
}
</style>
