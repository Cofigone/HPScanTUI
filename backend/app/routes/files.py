"""File management API routes."""
import os
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app

files_bp = Blueprint('files', __name__)


def get_scan_dir() -> Path:
    """Get the scan directory path.
    
    Returns:
        Path object for the scan directory
    """
    scan_dir = current_app.config.get('SCAN_DIR', './scandir')
    return Path(scan_dir)


def get_file_info(file_path: Path) -> dict:
    """Get file information.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    stat = file_path.stat()
    return {
        "name": file_path.name,
        "size": stat.st_size,
        "size_formatted": format_file_size(stat.st_size),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": file_path.suffix.lower()
    }


def format_file_size(size: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size: File size in bytes
        
    Returns:
        Formatted file size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


@files_bp.route('', methods=['GET'])
def list_files():
    """List all scanned files.
    
    Query Parameters:
        sort: Sort field (name, size, modified)
        order: Sort order (asc, desc)
        
    Returns:
        JSON with list of scanned files
    ---
    parameters:
        - name: sort
          in: query
          type: string
          enum: [name, size, modified]
          default: modified
        - name: order
          in: query
          type: string
          enum: [asc, desc]
          default: desc
    responses:
        200:
            description: List of scanned files
    """
    scan_dir = get_scan_dir()
    
    if not scan_dir.exists():
        return jsonify({
            "success": True,
            "files": [],
            "directory": str(scan_dir)
        })
    
    # Get supported file extensions
    supported_extensions = {'.pdf', '.jpg', '.jpeg', '.png'}
    
    # Get all files
    files = []
    for file_path in scan_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            files.append(get_file_info(file_path))
    
    # Sort files
    sort_field = request.args.get('sort', 'modified')
    order = request.args.get('order', 'desc')
    
    if sort_field in ['name', 'size', 'modified']:
        files.sort(key=lambda x: x[sort_field], reverse=(order == 'desc'))
    
    return jsonify({
        "success": True,
        "files": files,
        "directory": str(scan_dir),
        "count": len(files)
    })


@files_bp.route('/<path:filename>', methods=['GET'])
def download_file(filename: str):
    """Download a scanned file.
    
    Path Parameters:
        filename: Name of the file to download
        
    Returns:
        File download response
    ---
    parameters:
        - name: filename
          in: path
          type: string
          required: true
    responses:
        200:
            description: File download
        404:
            description: File not found
    """
    scan_dir = get_scan_dir()
    file_path = scan_dir / filename
    
    # Security check: ensure file is within scan directory
    try:
        file_path.resolve().relative_to(scan_dir.resolve())
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Invalid file path"
        }), 403
    
    if not file_path.exists() or not file_path.is_file():
        return jsonify({
            "success": False,
            "error": "File not found"
        }), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=filename
    )


@files_bp.route('/<path:filename>', methods=['DELETE'])
def delete_file(filename: str):
    """Delete a scanned file.
    
    Path Parameters:
        filename: Name of the file to delete
        
    Returns:
        JSON with success status
    ---
    parameters:
        - name: filename
          in: path
          type: string
          required: true
    responses:
        200:
            description: File deleted successfully
        404:
            description: File not found
    """
    scan_dir = get_scan_dir()
    file_path = scan_dir / filename
    
    # Security check: ensure file is within scan directory
    try:
        file_path.resolve().relative_to(scan_dir.resolve())
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Invalid file path"
        }), 403
    
    if not file_path.exists() or not file_path.is_file():
        return jsonify({
            "success": False,
            "error": "File not found"
        }), 404
    
    try:
        file_path.unlink()
        return jsonify({
            "success": True,
            "message": f"File '{filename}' deleted successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@files_bp.route('/browse', methods=['GET'])
def browse_directory():
    """Browse the output directory structure.
    
    Query Parameters:
        path: Subdirectory path (optional)
        
    Returns:
        JSON with directory contents
    ---
    parameters:
        - name: path
          in: query
          type: string
          description: Subdirectory path to browse
    responses:
        200:
            description: Directory contents
    """
    scan_dir = get_scan_dir()
    
    # Get subdirectory if specified
    sub_path = request.args.get('path', '')
    if sub_path:
        browse_path = scan_dir / sub_path
    else:
        browse_path = scan_dir
    
    # Security check: ensure path is within scan directory
    try:
        browse_path.resolve().relative_to(scan_dir.resolve())
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Invalid directory path"
        }), 403
    
    if not browse_path.exists():
        return jsonify({
            "success": False,
            "error": "Directory not found"
        }), 404
    
    if not browse_path.is_dir():
        return jsonify({
            "success": False,
            "error": "Path is not a directory"
        }), 400
    
    # Get directory contents
    directories = []
    files = []
    
    for item in browse_path.iterdir():
        if item.is_dir():
            directories.append({
                "name": item.name,
                "type": "directory"
            })
        elif item.is_file():
            files.append(get_file_info(item))
    
    # Sort directories and files
    directories.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['modified'], reverse=True)
    
    # Get parent directory
    parent = None
    if browse_path != scan_dir:
        try:
            parent = str(browse_path.parent.relative_to(scan_dir))
            if parent == '.':
                parent = ''
        except ValueError:
            parent = None
    
    return jsonify({
        "success": True,
        "current_path": str(browse_path.relative_to(scan_dir)) if browse_path != scan_dir else "",
        "parent_path": parent,
        "directories": directories,
        "files": files
    })


@files_bp.route('/preview/<path:filename>', methods=['GET'])
def preview_file(filename: str):
    """Preview a scanned file (for images).
    
    Path Parameters:
        filename: Name of the file to preview
        
    Returns:
        File content for preview
    ---
    parameters:
        - name: filename
          in: path
          type: string
          required: true
    responses:
        200:
            description: File preview
        404:
            description: File not found
    """
    scan_dir = get_scan_dir()
    file_path = scan_dir / filename
    
    # Security check: ensure file is within scan directory
    try:
        file_path.resolve().relative_to(scan_dir.resolve())
    except ValueError:
        return jsonify({
            "success": False,
            "error": "Invalid file path"
        }), 403
    
    if not file_path.exists() or not file_path.is_file():
        return jsonify({
            "success": False,
            "error": "File not found"
        }), 404
    
    # Only allow image previews
    image_extensions = {'.jpg', '.jpeg', '.png'}
    if file_path.suffix.lower() not in image_extensions:
        return jsonify({
            "success": False,
            "error": "Preview only available for image files"
        }), 400
    
    return send_file(file_path)
