"""Bulk scan service for managing multi-page scan sessions."""
import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import threading

import img2pdf
from PIL import Image
import io

# Import the existing HPScanner class
import sys
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
from hpscan import HPScanner


class BulkScanSession:
    """Manages a single bulk scan session."""
    
    def __init__(self, session_id: str, config: Dict[str, Any], scan_dir: str):
        """Initialize the bulk scan session.
        
        Args:
            session_id: Unique session identifier
            config: Scan configuration dictionary
            scan_dir: Base directory for scanned files
        """
        self.session_id = session_id
        self.config = config
        self.scan_dir = scan_dir
        self.pages: List[Path] = []
        self.created_at = datetime.now()
        self.temp_dir = tempfile.mkdtemp(prefix=f'bulk_scan_{session_id}_')
        self._lock = threading.Lock()
    
    def add_page(self, page_data: bytes) -> Dict[str, Any]:
        """Add a scanned page to the session.
        
        Args:
            page_data: Raw image data from scanner
            
        Returns:
            Dictionary with page info
        """
        with self._lock:
            page_num = len(self.pages) + 1
            page_path = Path(self.temp_dir) / f"page_{page_num:03d}.jpg"
            
            # Convert to JPEG if needed and save
            img = Image.open(io.BytesIO(page_data))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(page_path, format='JPEG', quality=95)
            
            self.pages.append(page_path)
            
            return {
                "page_number": page_num,
                "path": str(page_path),
                "size": page_path.stat().st_size
            }
    
    def get_page_preview(self, page_num: int) -> Optional[bytes]:
        """Get preview image for a page.
        
        Args:
            page_num: Page number (1-indexed)
            
        Returns:
            Image data or None if not found
        """
        with self._lock:
            if 1 <= page_num <= len(self.pages):
                page_path = self.pages[page_num - 1]
                # Create a smaller preview
                img = Image.open(page_path)
                img.thumbnail((300, 400))  # Thumbnail size
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=85)
                return buffer.getvalue()
        return None
    
    def get_page_count(self) -> int:
        """Get the number of pages in the session."""
        return len(self.pages)
    
    def delete_page(self, page_num: int) -> bool:
        """Delete a page from the session.
        
        Args:
            page_num: Page number to delete (1-indexed)
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if 1 <= page_num <= len(self.pages):
                page_path = self.pages.pop(page_num - 1)
                if page_path.exists():
                    page_path.unlink()
                # Rename remaining pages to maintain order
                for i, path in enumerate(self.pages):
                    new_path = Path(self.temp_dir) / f"page_{i+1:03d}.jpg"
                    if path != new_path:
                        path.rename(new_path)
                        self.pages[i] = new_path
                return True
        return False
    
    def finish(self, output_filename: str) -> Dict[str, Any]:
        """Merge all pages into a PDF and save.
        
        Args:
            output_filename: Name for the output file (without extension)
            
        Returns:
            Dictionary with result info
        """
        with self._lock:
            if not self.pages:
                return {
                    "success": False,
                    "error": "No pages to save"
                }
            
            # Generate output path
            output_dir = Path(self.config.get("output_dir", self.scan_dir))
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / f"{output_filename}.pdf"
            
            # Handle duplicate filenames
            suffix = 1
            temp = output_path
            while output_path.exists():
                output_path = temp.parent / f"{temp.stem}_{suffix}{temp.suffix}"
                suffix += 1
            
            # Convert all pages to JPEG bytes for img2pdf
            jpeg_pages = []
            for page_path in self.pages:
                with open(page_path, 'rb') as f:
                    jpeg_pages.append(f.read())
            
            # Merge into PDF
            with open(output_path, 'wb') as f:
                f.write(img2pdf.convert(jpeg_pages))
            
            return {
                "success": True,
                "filename": output_path.name,
                "path": str(output_path),
                "pages": len(self.pages),
                "size": output_path.stat().st_size
            }
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temp directory: {e}")
        self.pages = []


class BulkScanService:
    """Service for managing bulk scan sessions."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure single service instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the bulk scan service."""
        if self._initialized:
            return
        
        self._sessions: Dict[str, BulkScanSession] = {}
        self._scan_dir: str = "./scandir"
        self._session_lock = threading.Lock()
        self._initialized = True
    
    def set_scan_dir(self, scan_dir: str):
        """Set the scan output directory.
        
        Args:
            scan_dir: Path to the scan output directory
        """
        self._scan_dir = scan_dir
    
    def start_session(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new bulk scan session.
        
        Args:
            config: Scan configuration dictionary
            
        Returns:
            Dictionary with session info
        """
        # Generate session ID
        session_id = f"bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Create session
        session = BulkScanSession(session_id, config, self._scan_dir)
        
        with self._session_lock:
            # Clean up old sessions (keep only latest 5)
            if len(self._sessions) >= 5:
                oldest = min(self._sessions.items(), key=lambda x: x[1].created_at)
                oldest[1].cleanup()
                del self._sessions[oldest[0]]
            
            self._sessions[session_id] = session
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Bulk scan session started"
        }
    
    def get_session(self, session_id: str) -> Optional[BulkScanSession]:
        """Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            BulkScanSession or None if not found
        """
        with self._session_lock:
            return self._sessions.get(session_id)
    
    def scan_page(self, session_id: str) -> Dict[str, Any]:
        """Scan and add a page to a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with scan result
        """
        session = self.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        try:
            # Create scanner and perform scan
            scanner = HPScanner(session.config)
            
            # Get the scan data
            URL_CREATE_SCAN = f'http://{scanner.host}/eSCL/ScanJobs'
            capability = scanner.get_capabilities()
            
            height = session.config.get("height") or capability.max_height
            width = session.config.get("width") or capability.max_width
            xdpi, ydpi = 300, 300
            colormode = session.config.get("colormode")
            if colormode not in capability.color_modes:
                colormode = capability.color_modes[-1]
            
            from schema import scan_xml_schema
            data = scan_xml_schema.format(
                height=height,
                width=width,
                xdpi=xdpi,
                ydpi=ydpi,
                format="image/jpeg",  # Always use JPEG for bulk scan
                colormode=colormode
            )
            
            res = scanner.session.post(URL_CREATE_SCAN, data=data)
            if res.status_code != 201:
                return {
                    "success": False,
                    "error": f"Scan failed with status {res.status_code}"
                }
            
            job = scanner.get_job()
            if not job:
                return {
                    "success": False,
                    "error": "No scan job found"
                }
            
            url = f'http://{scanner.host}{job}/NextDocument'
            page_data = scanner.session.get(url).content
            
            # Add to session
            page_info = session.add_page(page_data)
            
            return {
                "success": True,
                "page_number": page_info["page_number"],
                "preview_url": f"/api/scanner/bulk/preview/{session_id}/{page_info['page_number']}",
                "message": f"Page {page_info['page_number']} scanned"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_preview(self, session_id: str, page_num: int) -> Optional[bytes]:
        """Get preview image for a page.
        
        Args:
            session_id: Session identifier
            page_num: Page number
            
        Returns:
            Image data or None
        """
        session = self.get_session(session_id)
        if session:
            return session.get_page_preview(page_num)
        return None
    
    def delete_page(self, session_id: str, page_num: int) -> Dict[str, Any]:
        """Delete a page from a session.
        
        Args:
            session_id: Session identifier
            page_num: Page number to delete
            
        Returns:
            Dictionary with result
        """
        session = self.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        if session.delete_page(page_num):
            return {
                "success": True,
                "message": f"Page {page_num} deleted",
                "remaining_pages": session.get_page_count()
            }
        else:
            return {
                "success": False,
                "error": "Page not found"
            }
    
    def finish_session(self, session_id: str, output_filename: str) -> Dict[str, Any]:
        """Finish a session and save the merged PDF.
        
        Args:
            session_id: Session identifier
            output_filename: Name for the output file
            
        Returns:
            Dictionary with result
        """
        session = self.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        result = session.finish(output_filename)
        
        # Clean up session
        if result["success"]:
            with self._session_lock:
                session.cleanup()
                del self._sessions[session_id]
        
        return result
    
    def cancel_session(self, session_id: str) -> Dict[str, Any]:
        """Cancel a session and discard all pages.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with result
        """
        session = self.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        page_count = session.get_page_count()
        
        with self._session_lock:
            session.cleanup()
            del self._sessions[session_id]
        
        return {
            "success": True,
            "message": f"Session cancelled, {page_count} pages discarded"
        }
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the status of a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session status
        """
        session = self.get_session(session_id)
        if not session:
            return {
                "success": False,
                "error": "Session not found"
            }
        
        return {
            "success": True,
            "session_id": session_id,
            "pages": session.get_page_count(),
            "created_at": session.created_at.isoformat()
        }


# Global bulk scan service instance
bulk_scan_service = BulkScanService()
