/**
 * API service for communicating with the Flask backend.
 */
import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api',
  timeout: 60000, // 60 seconds timeout for long operations
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * Scanner API endpoints
 */
export const scannerApi = {
  /**
   * Get current scanner status
   */
  getStatus() {
    return api.get('/scanner/status')
  },

  /**
   * Get printer capabilities
   * @param {string} ip - Printer IP address
   */
  getCapabilities(ip) {
    return api.get('/scanner/capabilities', { params: { ip } })
  },

  /**
   * Start a scan job
   * @param {Object} config - Scan configuration
   */
  startScan(config) {
    return api.post('/scanner/scan', config)
  },

  /**
   * Get scan progress
   */
  getProgress() {
    return api.get('/scanner/progress')
  },

  /**
   * Search for printers on the network
   */
  searchPrinters() {
    return api.post('/scanner/search')
  },

  /**
   * Check if a printer is reachable
   * @param {string} ip - Printer IP address
   */
  checkPrinter(ip) {
    return api.get('/scanner/check', { params: { ip } })
  }
}

/**
 * Files API endpoints
 */
export const filesApi = {
  /**
   * List all scanned files
   * @param {Object} params - Query parameters (sort, order)
   */
  listFiles(params = {}) {
    return api.get('/files', { params })
  },

  /**
   * Get download URL for a file
   * @param {string} filename - File name
   */
  getDownloadUrl(filename) {
    return `/api/files/${encodeURIComponent(filename)}`
  },

  /**
   * Delete a file
   * @param {string} filename - File name
   */
  deleteFile(filename) {
    return api.delete(`/files/${encodeURIComponent(filename)}`)
  },

  /**
   * Browse directory structure
   * @param {string} path - Directory path
   */
  browseDirectory(path = '') {
    return api.get('/files/browse', { params: { path } })
  },

  /**
   * Get preview URL for an image file
   * @param {string} filename - File name
   */
  getPreviewUrl(filename) {
    return `/api/files/preview/${encodeURIComponent(filename)}`
  }
}

/**
 * Health check endpoint
 */
export const healthCheck = () => api.get('/health')

/**
 * Configuration API endpoints
 */
export const configApi = {
  /**
   * Get scanner configuration including scan directory
   */
  getConfig() {
    return api.get('/scanner/config')
  }
}

/**
 * Bulk scan API endpoints
 */
export const bulkScanApi = {
  /**
   * Start a new bulk scan session
   * @param {Object} config - Scan configuration
   */
  startSession(config) {
    return api.post('/scanner/bulk/start', config)
  },

  /**
   * Scan and add a page to the session
   * @param {string} sessionId - Session identifier
   */
  scanPage(sessionId) {
    return api.post('/scanner/bulk/scan-page', { session_id: sessionId })
  },

  /**
   * Get preview URL for a page
   * @param {string} sessionId - Session identifier
   * @param {number} pageNum - Page number
   */
  getPreviewUrl(sessionId, pageNum) {
    return `/api/scanner/bulk/preview/${sessionId}/${pageNum}`
  },

  /**
   * Delete a page from the session
   * @param {string} sessionId - Session identifier
   * @param {number} pageNum - Page number to delete
   */
  deletePage(sessionId, pageNum) {
    return api.delete('/scanner/bulk/delete-page', {
      data: { session_id: sessionId, page_num: pageNum }
    })
  },

  /**
   * Finish the session and save the PDF
   * @param {string} sessionId - Session identifier
   * @param {string} output - Output filename (optional)
   */
  finishSession(sessionId, output = null) {
    return api.post('/scanner/bulk/finish', {
      session_id: sessionId,
      output: output
    })
  },

  /**
   * Cancel the session and discard all pages
   * @param {string} sessionId - Session identifier
   */
  cancelSession(sessionId) {
    return api.delete('/scanner/bulk/cancel', {
      data: { session_id: sessionId }
    })
  },

  /**
   * Get session status
   * @param {string} sessionId - Session identifier
   */
  getStatus(sessionId) {
    return api.get(`/scanner/bulk/status/${sessionId}`)
  }
}

export default {
  scanner: scannerApi,
  files: filesApi,
  bulkScan: bulkScanApi,
  config: configApi,
  healthCheck
}
