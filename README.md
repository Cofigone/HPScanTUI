# HPScan

HPScan is a multi-interface application for interacting with HP scanners through their eSCL web interfaces. It provides a **TUI (Terminal User Interface)**, a **Web Application**, and a **CLI (Command Line Interface)** for searching printers, viewing capabilities, and initiating scans.

## Features

- **Search for Printers**: Discover HP printers available in the local network
- **View Capabilities**: Retrieve and display the capabilities of a printer
- **Scan Documents**: Initiate scanning operations with customizable parameters:
  - DPI (resolution)
  - Paper format (A4, A5, Letter)
  - Color mode (Color, Grayscale, Black & White)
  - Output format (PDF, JPEG)
- **Multiple Interfaces**:
  - TUI (Terminal User Interface) - Textual-based terminal app
  - Web Application - Modern Vue.js 3 frontend with Flask backend
  - CLI (Command Line Interface) - Direct command-line usage

## Project Structure

```
HPScan/
├── src/                    # TUI application (original)
│   ├── main.py            # TUI entry point
│   ├── tui.py             # Textual TUI implementation
│   ├── hpscan.py          # Core scanner logic
│   └── schema.py          # XML schema for scan settings
├── backend/               # Flask REST API
│   ├── app/
│   │   ├── routes/        # API endpoints
│   │   └── services/      # Business logic
│   ├── hpscan.py          # Scanner logic (copy)
│   ├── schema.py          # XML schema (copy)
│   └── Dockerfile         # Backend container
├── frontend/              # Vue.js 3 web application
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── services/      # API client
│   │   └── stores/        # Pinia state management
│   └── Dockerfile         # Frontend container
├── docker-compose.yml     # Multi-container deployment
└── plans/                 # Architecture documentation
```

---

## Web Application (Docker Deployment)

The web application provides a modern, user-friendly interface for scanner operations.

### Prerequisites

- Docker and Docker Compose
- Network access to HP printer

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/prasannareddych/HPScanCLI.git
   cd HPScanCLI
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Open your browser and navigate to `http://localhost`

4. **Stop the application**:
   ```bash
   docker-compose down
   ```

### Configuration

Environment variables can be set in a `.env` file:

```env
SECRET_KEY=your-secret-key-here
```

### Volume Management

Scanned files are stored in a Docker volume named `hpscan-scandir`. To access the files:

```bash
# List volume contents
docker run --rm -v hpscan-scandir:/data alpine ls -la /data

# Copy files from volume
docker cp hpscan-backend:/scandir ./scans
```

### Development Mode

For development, you can run the backend and frontend separately:

**Backend (Flask)**:
```bash
cd backend
pip install -r requirements.txt
python run.py
```

**Frontend (Vue.js)**:
```bash
cd frontend
npm install
npm run dev
```

---

## TUI Application (Terminal)

The TUI provides a terminal-based interface using the Textual framework.

### Prerequisites

- Python 3.8+
- Required packages (see requirements.txt)

### Installation

```bash
pip install -r requirements.txt
```

### Usage

```bash
cd src
python main.py
```

### TUI Controls

- `s` - Search for printers on the network
- `c` - Show printer capabilities
- `q` - Quit the application

---

## CLI Usage

For command-line usage without the TUI:

```bash
hpscancli [options]
```

### Command-line Options

| Option | Description |
|--------|-------------|
| `-i, --ip` | IP address of the HP scanner |
| `-s, --searchprinter` | Search for available printers |
| `-c, --capabilities` | Show printer capabilities |
| `--height` | Set scan height (pixels) |
| `--width` | Set scan width (pixels) |
| `--dpi` | Set scan DPI (150, 200, 300, 600) |
| `--colormode` | Set color mode (RGB24, Grayscale8, BlackAndWhite1) |
| `--pdf` | Output as PDF (default: JPEG) |
| `-o, --output` | Output filename |
| `-b, --bulkscan` | Enable bulk scan mode |

### CLI Examples

1. **Search for printers**:
   ```bash
   hpscancli -s
   ```

2. **Show printer capabilities**:
   ```bash
   hpscancli -i 192.168.1.100 -c
   ```

3. **Scan with custom settings**:
   ```bash
   hpscancli -i 192.168.1.100 --dpi 300 --colormode RGB24 --pdf -o document
   ```

---

## API Endpoints

The Flask backend provides the following REST API endpoints:

### Scanner Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scanner/status` | Get current scanner status |
| GET | `/api/scanner/capabilities?ip=<ip>` | Get printer capabilities |
| POST | `/api/scanner/scan` | Start a new scan job |
| GET | `/api/scanner/progress` | Get scan progress |
| POST | `/api/scanner/search` | Search for printers |
| GET | `/api/scanner/check?ip=<ip>` | Check printer reachability |

### File Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/files` | List scanned files |
| GET | `/api/files/<filename>` | Download a file |
| DELETE | `/api/files/<filename>` | Delete a file |
| GET | `/api/files/browse` | Browse directory structure |

---

## Technology Stack

### Backend
- **Flask** - Python web framework
- **Flask-CORS** - Cross-origin resource sharing
- **Gunicorn** - WSGI HTTP Server

### Frontend
- **Vue.js 3** - JavaScript framework
- **Pinia** - State management
- **Axios** - HTTP client
- **Vite** - Build tool

### Deployment
- **Docker** - Containerization
- **Nginx** - Web server (frontend)

---

## Troubleshooting

### Printer Not Found

1. Ensure the printer is powered on and connected to the network
2. Check that your computer is on the same network as the printer
3. Try searching for printers using the web interface or CLI

### Scan Fails

1. Verify the printer IP address is correct
2. Check that the printer is not busy with another job
3. Ensure the scanner lid is closed properly

### Docker Issues

1. Check container logs:
   ```bash
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. Restart containers:
   ```bash
   docker-compose restart
   ```

3. Rebuild containers:
   ```bash
   docker-compose up -d --build
   ```

---

## Author

Prasanna Reddy. Ch

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
