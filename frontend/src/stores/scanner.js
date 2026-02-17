/**
 * Pinia store for scanner state management.
 */
import { defineStore } from 'pinia'
import { scannerApi, filesApi, bulkScanApi } from '../services/api'

export const useScannerStore = defineStore('scanner', {
  state: () => ({
    // Scan configuration
    config: {
      ip: '192.168.13.93',
      dpi: 300,
      format: 'A4',
      colormode: 'RGB24',
      pdf: true,
      output: '',
      output_dir: './scandir'
    },
    
    // Paper format dimensions
    paperFormats: {
      A4: { height: 3508, width: 2480 },
      A5: { height: 2480, width: 1748 },
      Letter: { height: 3300, width: 2550 }
    },
    
    // Printer capabilities
    capabilities: null,
    
    // Scan state
    isScanning: false,
    progress: 0,
    status: '',
    error: null,
    lastResult: null,
    
    // Printer search
    isSearching: false,
    discoveredPrinters: [],
    
    // Files
    files: [],
    isLoadingFiles: false,
    
    // Bulk scan state
    bulkScanSession: null,
    bulkScanPages: [],
    isBulkScanning: false,
    isBulkScanModalOpen: false,
    bulkScanPageInProgress: false,
    
    // UI state
    notification: null
  }),

  getters: {
    /**
     * Check if a printer IP is configured
     */
    hasPrinterIp: (state) => !!state.config.ip,
    
    /**
     * Get current paper format dimensions
     */
    currentPaperDimensions: (state) => {
      return state.paperFormats[state.config.format] || state.paperFormats.A4
    },
    
    /**
     * Check if scan is in progress
     */
    isScanInProgress: (state) => state.isScanning,
    
    /**
     * Get bulk scan page count
     */
    bulkScanPageCount: (state) => state.bulkScanPages.length
  },

  actions: {
    /**
     * Update scan configuration
     */
    updateConfig(newConfig) {
      this.config = { ...this.config, ...newConfig }
    },

    /**
     * Set printer IP
     */
    setPrinterIp(ip) {
      this.config.ip = ip
    },

    /**
     * Set paper format
     */
    setPaperFormat(format) {
      this.config.format = format
    },

    /**
     * Toggle output format (PDF/JPEG)
     */
    toggleOutputFormat() {
      this.config.pdf = !this.config.pdf
    },

    /**
     * Fetch printer capabilities
     */
    async fetchCapabilities() {
      if (!this.config.ip) {
        this.error = 'No printer IP configured'
        return false
      }

      try {
        const response = await scannerApi.getCapabilities(this.config.ip)
        if (response.data.success) {
          this.capabilities = response.data.capabilities
          return true
        } else {
          this.error = response.data.error
          return false
        }
      } catch (err) {
        this.error = err.message || 'Failed to get printer capabilities'
        return false
      }
    },

    /**
     * Start a scan job
     */
    async startScan() {
      if (this.isScanning) {
        this.showNotification('A scan is already in progress', 'warning')
        return false
      }

      if (!this.config.ip) {
        this.error = 'No printer IP configured'
        this.showNotification('Please configure a printer IP', 'error')
        return false
      }

      this.isScanning = true
      this.progress = 0
      this.status = 'Starting scan...'
      this.error = null
      this.lastResult = null

      try {
        const response = await scannerApi.startScan(this.config)
        if (response.data.success) {
          this.status = 'Scan started'
          this.pollProgress()
          return true
        } else {
          this.isScanning = false
          this.error = response.data.error || response.data.message
          this.showNotification(this.error, 'error')
          return false
        }
      } catch (err) {
        this.isScanning = false
        this.error = err.message || 'Failed to start scan'
        this.showNotification(this.error, 'error')
        return false
      }
    },

    /**
     * Poll for scan progress
     */
    async pollProgress() {
      const pollInterval = setInterval(async () => {
        try {
          const response = await scannerApi.getProgress()
          const { scanning, progress, status, error, result } = response.data

          this.progress = progress
          this.status = status

          if (error) {
            this.error = error
            this.showNotification(error, 'error')
          }

          if (!scanning) {
            clearInterval(pollInterval)
            this.isScanning = false
            
            if (result) {
              this.lastResult = result
              this.showNotification('Scan completed successfully!', 'success')
              this.fetchFiles() // Refresh file list
            }
          }
        } catch (err) {
          console.error('Error polling progress:', err)
        }
      }, 500) // Poll every 500ms
    },

    /**
     * Search for printers on the network
     */
    async searchPrinters() {
      this.isSearching = true
      this.discoveredPrinters = []
      this.error = null

      try {
        const response = await scannerApi.searchPrinters()
        if (response.data.success) {
          this.discoveredPrinters = response.data.printers
          if (this.discoveredPrinters.length === 0) {
            this.showNotification('No printers found on the network', 'warning')
          } else {
            this.showNotification(`Found ${this.discoveredPrinters.length} printer(s)`, 'success')
          }
        }
      } catch (err) {
        this.error = err.message || 'Failed to search for printers'
        this.showNotification(this.error, 'error')
      } finally {
        this.isSearching = false
      }
    },

    /**
     * Check if a printer is reachable
     */
    async checkPrinter(ip) {
      try {
        const response = await scannerApi.checkPrinter(ip)
        return response.data.reachable
      } catch (err) {
        return false
      }
    },

    /**
     * Fetch scanned files
     */
    async fetchFiles() {
      this.isLoadingFiles = true

      try {
        const response = await filesApi.listFiles({ sort: 'modified', order: 'desc' })
        if (response.data.success) {
          this.files = response.data.files
        }
      } catch (err) {
        this.error = err.message || 'Failed to fetch files'
      } finally {
        this.isLoadingFiles = false
      }
    },

    /**
     * Delete a file
     */
    async deleteFile(filename) {
      try {
        const response = await filesApi.deleteFile(filename)
        if (response.data.success) {
          this.files = this.files.filter(f => f.name !== filename)
          this.showNotification('File deleted', 'success')
          return true
        }
      } catch (err) {
        this.showNotification(err.message || 'Failed to delete file', 'error')
        return false
      }
    },

    // ==================== Bulk Scan Actions ====================

    /**
     * Start a bulk scan session
     */
    async startBulkScan() {
      if (!this.config.ip) {
        this.showNotification('Please configure a printer IP', 'error')
        return false
      }

      this.isBulkScanning = true
      this.bulkScanPages = []
      this.error = null

      try {
        const response = await bulkScanApi.startSession(this.config)
        if (response.data.success) {
          this.bulkScanSession = response.data.session_id
          this.isBulkScanModalOpen = true
          this.showNotification('Bulk scan session started', 'success')
          return true
        } else {
          this.isBulkScanning = false
          this.error = response.data.error
          this.showNotification(this.error, 'error')
          return false
        }
      } catch (err) {
        this.isBulkScanning = false
        this.error = err.message || 'Failed to start bulk scan'
        this.showNotification(this.error, 'error')
        return false
      }
    },

    /**
     * Scan a page in bulk scan session
     */
    async scanBulkPage() {
      if (!this.bulkScanSession) {
        this.showNotification('No active bulk scan session', 'error')
        return false
      }

      this.bulkScanPageInProgress = true
      this.error = null

      try {
        const response = await bulkScanApi.scanPage(this.bulkScanSession)
        if (response.data.success) {
          this.bulkScanPages.push({
            pageNumber: response.data.page_number,
            previewUrl: response.data.preview_url
          })
          this.showNotification(response.data.message, 'success')
          return true
        } else {
          this.error = response.data.error
          this.showNotification(this.error, 'error')
          return false
        }
      } catch (err) {
        this.error = err.message || 'Failed to scan page'
        this.showNotification(this.error, 'error')
        return false
      } finally {
        this.bulkScanPageInProgress = false
      }
    },

    /**
     * Delete a page from bulk scan session
     */
    async deleteBulkPage(pageNum) {
      if (!this.bulkScanSession) {
        return false
      }

      try {
        const response = await bulkScanApi.deletePage(this.bulkScanSession, pageNum)
        if (response.data.success) {
          this.bulkScanPages = this.bulkScanPages.filter(p => p.pageNumber !== pageNum)
          // Update page numbers
          this.bulkScanPages = this.bulkScanPages.map((p, idx) => ({
            ...p,
            pageNumber: idx + 1
          }))
          this.showNotification(response.data.message, 'success')
          return true
        }
      } catch (err) {
        this.showNotification(err.message || 'Failed to delete page', 'error')
        return false
      }
    },

    /**
     * Finish bulk scan and save PDF
     */
    async finishBulkScan(output = null) {
      if (!this.bulkScanSession) {
        return false
      }

      if (this.bulkScanPages.length === 0) {
        this.showNotification('No pages to save', 'warning')
        return false
      }

      this.isBulkScanning = false

      try {
        const response = await bulkScanApi.finishSession(this.bulkScanSession, output)
        if (response.data.success) {
          this.showNotification(`PDF saved: ${response.data.filename} (${response.data.pages} pages)`, 'success')
          this.closeBulkScanModal()
          this.fetchFiles() // Refresh file list
          return true
        } else {
          this.error = response.data.error
          this.showNotification(this.error, 'error')
          return false
        }
      } catch (err) {
        this.error = err.message || 'Failed to save PDF'
        this.showNotification(this.error, 'error')
        return false
      }
    },

    /**
     * Cancel bulk scan session
     */
    async cancelBulkScan() {
      if (!this.bulkScanSession) {
        return false
      }

      try {
        const response = await bulkScanApi.cancelSession(this.bulkScanSession)
        if (response.data.success) {
          this.showNotification(response.data.message, 'info')
          this.closeBulkScanModal()
          return true
        }
      } catch (err) {
        this.showNotification(err.message || 'Failed to cancel session', 'error')
        return false
      }
    },

    /**
     * Close bulk scan modal
     */
    closeBulkScanModal() {
      this.isBulkScanModalOpen = false
      this.bulkScanSession = null
      this.bulkScanPages = []
      this.isBulkScanning = false
      this.bulkScanPageInProgress = false
    },

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
      this.notification = { message, type }
      // Auto-clear after 5 seconds
      setTimeout(() => {
        this.notification = null
      }, 5000)
    },

    /**
     * Clear notification
     */
    clearNotification() {
      this.notification = null
    },

    /**
     * Clear error
     */
    clearError() {
      this.error = null
    }
  }
})
