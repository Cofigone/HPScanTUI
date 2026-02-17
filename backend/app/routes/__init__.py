"""Routes package for the Flask backend."""
from .scanner import scanner_bp
from .files import files_bp

__all__ = ['scanner_bp', 'files_bp']
