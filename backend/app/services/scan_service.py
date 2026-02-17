"""Scan service for handling scanner operations with progress tracking."""
import threading
import socket
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List

# Import the existing HPScanner class from backend root
import sys
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
from hpscan import HPScanner


class ScanService:
    """Service for managing scan operations with progress tracking."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure single scan service instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the scan service."""
        if self._initialized:
            return
            
        self._progress: int = 0
        self._status: str = ""
        self._scanning: bool = False
        self._scan_thread: Optional[threading.Thread] = None
        self._last_error: Optional[str] = None
        self._last_result: Optional[Dict[str, Any]] = None
        self._scan_dir: str = "./scandir"
        self._initialized = True
    
    def set_scan_dir(self, scan_dir: str):
        """Set the scan output directory.
        
        Args:
            scan_dir: Path to the scan output directory
        """
        self._scan_dir = scan_dir
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current scan status.
        
        Returns:
            Dictionary with scanning status, progress, and status message
        """
        return {
            "scanning": self._scanning,
            "progress": self._progress,
            "status": self._status,
            "error": self._last_error,
            "result": self._last_result
        }
    
    def start_scan(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a scan operation in a background thread.
        
        Args:
            config: Scan configuration dictionary
            
        Returns:
            Dictionary with success status and message
        """
        if self._scanning:
            return {
                "success": False,
                "message": "A scan is already in progress"
            }
        
        # Reset state
        self._progress = 0
        self._status = "Initializing..."
        self._last_error = None
        self._last_result = None
        self._scanning = True
        
        # Ensure output directory is set
        config["output_dir"] = config.get("output_dir", self._scan_dir)
        
        # Start scan thread
        self._scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(config.copy(),),
            daemon=True
        )
        self._scan_thread.start()
        
        return {
            "success": True,
            "message": "Scan started"
        }
    
    def _scan_worker(self, config: Dict[str, Any]):
        """Worker thread for performing the scan.
        
        Args:
            config: Scan configuration dictionary
        """
        try:
            self._status = "Connecting to printer..."
            self._progress = 10
            
            # Create scanner instance
            scanner = HPScanner(config)
            
            self._status = "Starting scan..."
            self._progress = 20
            
            # Perform the scan
            scanner.perform_scan()
            
            self._status = "Scan complete"
            self._progress = 100
            
            # Generate result
            output_file = config.get("output", datetime.now().strftime("SCAN_%Y%m%d_%H%M%S"))
            output_file += ".pdf" if config.get("pdf", True) else ".jpg"
            
            self._last_result = {
                "filename": output_file,
                "output_dir": str(config.get("output_dir", self._scan_dir))
            }
            
        except Exception as e:
            self._last_error = str(e)
            self._status = f"Error: {str(e)}"
            self._progress = 0
        finally:
            self._scanning = False
    
    def check_printer(self, ip: str) -> bool:
        """Check if a printer is reachable at the given IP.
        
        Args:
            ip: IP address of the printer
            
        Returns:
            True if printer is reachable, False otherwise
        """
        try:
            for _ in range(10):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.01)
                result = sock.connect_ex((ip, 9100))
                if result == 0:
                    sock.close()
                    return True
                sock.close()
        except:
            pass
        return False
    
    def get_printer_capabilities(self, ip: str) -> Dict[str, Any]:
        """Get printer capabilities.
        
        Args:
            ip: IP address of the printer
            
        Returns:
            Dictionary with printer capabilities
        """
        try:
            config = {"ip": ip}
            scanner = HPScanner(config)
            capabilities = scanner.get_capabilities()
            
            return {
                "success": True,
                "capabilities": {
                    "make_and_model": capabilities.make_and_model,
                    "serial_number": capabilities.serial_number,
                    "manufacturer": capabilities.manufacturer,
                    "firmware_version": capabilities.firmware_version,
                    "min_width": capabilities.min_width,
                    "max_width": capabilities.max_width,
                    "min_height": capabilities.min_height,
                    "max_height": capabilities.max_height,
                    "color_modes": capabilities.color_modes,
                    "document_formats": capabilities.document_formats,
                    "supported_resolutions": capabilities.supported_resolutions
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_printers(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> List[str]:
        """Search for printers on the network.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of discovered printer IP addresses
        """
        printers = []
        try:
            machine_ip = self._get_ip_address()
            if not machine_ip:
                return printers
            
            _ip = re.findall(r"\d+\.\d+\.\d+\.", machine_ip)[0]
            ip_range = [_ip + str(i) for i in range(2, 255) if _ip + str(i) != machine_ip]
            
            total = len(ip_range)
            for idx, ip in enumerate(ip_range):
                if progress_callback:
                    progress_callback(idx + 1, total)
                if self.check_printer(ip):
                    printers.append(ip)
                    
        except Exception as e:
            print(f"Error searching for printers: {e}")
        
        return printers
    
    def _get_ip_address(self) -> Optional[str]:
        """Get the local IP address of the machine.
        
        Returns:
            Local IP address or None if not found
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            return ip_address
        except socket.error:
            return None


# Global scan service instance
scan_service = ScanService()
