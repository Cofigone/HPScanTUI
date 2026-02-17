# HPScan Web Application Architecture Plan

## Overview

This document outlines the architecture for converting the existing HPScan TUI application to a web application with a Flask backend and Vue.js 3 frontend.

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **API**: RESTful JSON API
- **Async**: Threading for long-running scan operations
- **File Handling**: Direct filesystem access to Docker volume

### Frontend
- **Framework**: Vue.js 3 with Composition API
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **UI Components**: Custom components with CSS (optional: consider Vuetify or PrimeVue later)

### Deployment
- **Containerization**: Docker + Docker Compose
- **Storage**: Docker named volume for scanned files
- **Network**: Bridge network for local access

## Architecture Diagram

```mermaid
flowchart TB
    subgraph Docker Container
        subgraph Frontend [Vue.js 3 Frontend]
            UI[UI Components]
            Store[Pinia Store]
            API[API Service]
        end
        
        subgraph Backend [Flask Backend]
            Routes[REST Routes]
            Scanner[HPScanner Class]
            FileSrv[File Server]
        end
    end
    
    subgraph Volumes [Docker Volumes]
        ScanDir[/scandir - Scanned Files]
    end
    
    subgraph External
        Printer[HP Printer - eSCL Protocol]
        Browser[User Browser]
    end
    
    Browser --> UI
    UI --> Store
    Store --> API
    API --> Routes
    Routes --> Scanner
    Routes --> FileSrv
    Scanner --> Printer
    FileSrv --> ScanDir
    Scanner --> ScanDir
```

## Project Structure

```
HPScan/
├── backend/                    # Flask backend
│   ├── app/
│   │   ├── __init__.py        # Flask app factory
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── scanner.py     # Scanner API endpoints
│   │   │   └── files.py       # File management endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── scan_service.py # Scan orchestration
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── progress.py    # Progress tracking
│   ├── hpscan.py              # Existing HPScanner class (reused)
│   ├── schema.py              # Existing XML schema (reused)
│   ├── config.py              # Configuration settings
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container
│   └── run.py                 # Entry point
│
├── frontend/                   # Vue.js 3 frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ScanForm.vue       # Scan configuration form
│   │   │   ├── PrinterSearch.vue  # Network printer discovery
│   │   │   ├── ScanProgress.vue   # Progress indicator
│   │   │   ├── FileBrowser.vue    # Scanned files browser
│   │   │   └── PrinterInfo.vue    # Printer capabilities display
│   │   ├── services/
│   │   │   └── api.js         # API client
│   │   ├── stores/
│   │   │   └── scanner.js     # Pinia store for state
│   │   ├── App.vue            # Root component
│   │   └── main.js            # Entry point
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile             # Frontend container
│
├── docker-compose.yml          # Multi-container setup
├── .dockerignore
└── README.md
```

## API Endpoints

### Scanner Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scanner/status` | Check scanner connection status |
| GET | `/api/scanner/capabilities` | Get printer capabilities |
| POST | `/api/scanner/scan` | Start a new scan job |
| GET | `/api/scanner/progress` | Get current scan progress |
| POST | `/api/scanner/search` | Search for printers on network |

### File Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/files` | List scanned files |
| GET | `/api/files/<filename>` | Download a scanned file |
| DELETE | `/api/files/<filename>` | Delete a scanned file |
| GET | `/api/files/browse` | Browse output directory |

### Request/Response Examples

#### Start Scan
```json
// POST /api/scanner/scan
// Request
{
    "ip": "192.168.13.93",
    "dpi": 300,
    "format": "A4",
    "colormode": "RGB24",
    "pdf": true,
    "output": "scan_001",
    "output_dir": "/scandir"
}

// Response
{
    "success": true,
    "job_id": "scan_20260217_080000",
    "message": "Scan started"
}
```

#### Get Progress
```json
// GET /api/scanner/progress
// Response
{
    "scanning": true,
    "progress": 50,
    "status": "Scanning document...",
    "job_id": "scan_20260217_080000"
}
```

## Frontend Components

### ScanForm.vue
- IP address input with validation
- DPI selection (dropdown or input)
- Paper format selection (A4, A5, Letter)
- Color mode selection
- Output format toggle (PDF/JPEG)
- Filename input
- Output directory browser
- Scan button with loading state

### PrinterSearch.vue
- Search button to discover printers
- Progress bar during search
- List of discovered printers
- Click to select printer IP

### ScanProgress.vue
- Progress bar with percentage
- Status message
- Cancel button (optional)

### FileBrowser.vue
- List of scanned files
- File details (name, size, date)
- Download button
- Delete button
- Preview option (for images)

### PrinterInfo.vue
- Display printer capabilities
- Make and model
- Supported resolutions
- Supported color modes

## State Management

Using Pinia store for global state:

```javascript
// stores/scanner.js
export const useScannerStore = defineStore('scanner', {
    state: () => ({
        config: {
            ip: '192.168.13.93',
            dpi: 300,
            format: 'A4',
            colormode: 'RGB24',
            pdf: true,
            output: '',
            output_dir: '/scandir'
        },
        capabilities: null,
        isScanning: false,
        progress: 0,
        status: '',
        discoveredPrinters: [],
        scannedFiles: []
    }),
    actions: {
        async startScan() { /* ... */ },
        async searchPrinters() { /* ... */ },
        async fetchCapabilities() { /* ... */ },
        async fetchFiles() { /* ... */ }
    }
})
```

## Backend Implementation Details

### Reusing HPScanner Class

The existing [`HPScanner`](../src/hpscan.py:16) class will be reused with minimal modifications:

1. Remove Textual-specific imports (`@work`, `Worker`, `Message`)
2. Keep all core scanning logic intact
3. Add progress callback support for long operations

### Async Scan Operations

```python
# services/scan_service.py
import threading
from hpscan import HPScanner

class ScanService:
    def __init__(self):
        self._progress = 0
        self._status = ""
        self._scanning = False
    
    def start_scan(self, config: dict) -> dict:
        self._scanning = True
        self._progress = 0
        
        def scan_thread():
            try:
                scanner = HPScanner(config)
                self._status = "Connecting to printer..."
                self._progress = 10
                scanner.perform_scan()
                self._progress = 100
                self._status = "Scan complete"
            except Exception as e:
                self._status = f"Error: {str(e)}"
            finally:
                self._scanning = False
        
        thread = threading.Thread(target=scan_thread)
        thread.start()
        return {"success": True, "message": "Scan started"}
```

### Progress Tracking

Options for real-time progress updates:
1. **Polling**: Frontend polls `/api/scanner/progress` every 500ms
2. **Server-Sent Events (SSE)**: Backend pushes updates to frontend
3. **WebSockets**: Bidirectional communication

**Recommendation**: Start with polling for simplicity, can upgrade to SSE later.

## Docker Configuration

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY src/hpscan.py ./hpscan.py
COPY src/schema.py ./schema.py

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

### Frontend Dockerfile
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    volumes:
      - scandir:/scandir
    environment:
      - FLASK_ENV=production
      - SCAN_DIR=/scandir

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - API_URL=http://backend:5000

volumes:
  scandir:
    driver: local
```

## Migration Strategy

### Phase 1: Backend Setup
1. Create Flask project structure
2. Copy existing [`hpscan.py`](../src/hpscan.py) and [`schema.py`](../src/schema.py)
3. Create REST API endpoints
4. Test API with curl/Postman

### Phase 2: Frontend Setup
1. Create Vue.js 3 project with Vite
2. Build components incrementally
3. Connect to backend API
4. Test all functionality

### Phase 3: Docker Deployment
1. Create Dockerfiles
2. Create docker-compose.yml
3. Test local deployment
4. Document deployment process

## Security Considerations

1. **Network Access**: App runs on local network only
2. **No Authentication**: Single-user scenario (can add later)
3. **File Access**: Limited to scan directory volume
4. **Input Validation**: Validate all user inputs on backend
5. **CORS**: Configure Flask-CORS for frontend communication

## Future Enhancements

1. User authentication (if multi-user needed)
2. Scan history database
3. Batch scanning
4. OCR integration
5. Email notifications
6. Mobile-responsive design improvements

## Questions Resolved

- ✅ Backend: Flask
- ✅ Frontend: Vue.js 3
- ✅ Deployment: Docker container
- ✅ Users: Single user (expandable)
- ✅ Storage: Docker volume

## Next Steps

1. Review and approve this architecture plan
2. Switch to Code mode to begin implementation
3. Start with backend Flask setup
4. Build frontend components
5. Create Docker configuration
6. Test and document
