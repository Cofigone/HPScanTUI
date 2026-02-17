"""Bulk scan API routes."""
from flask import Blueprint, request, jsonify, current_app, send_file
import io

from app.services.bulk_scan_service import bulk_scan_service

bulk_scan_bp = Blueprint('bulk_scan', __name__)


@bulk_scan_bp.route('/start', methods=['POST'])
def start_bulk_scan():
    """Start a new bulk scan session.
    
    Request Body:
        JSON with scan configuration:
        - ip: Printer IP address (required)
        - dpi: Scan resolution (default: 300)
        - format: Paper format (A4, A5, Letter)
        - colormode: Color mode (RGB24, Grayscale8, etc.)
        - output_dir: Output directory path
    
    Returns:
        JSON with session_id
    ---
    requestBody:
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        ip:
                            type: string
                            description: Printer IP address
                        dpi:
                            type: integer
                            default: 300
                        format:
                            type: string
                            enum: [A4, A5, Letter]
                        colormode:
                            type: string
                            default: RGB24
                        output_dir:
                            type: string
    responses:
        200:
            description: Bulk scan session started
        400:
            description: Invalid request
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400
    
    ip = data.get('ip')
    if not ip:
        return jsonify({
            "success": False,
            "error": "IP address is required"
        }), 400
    
    # Build scan configuration
    config = {
        "ip": ip,
        "dpi": data.get("dpi", 300),
        "colormode": data.get("colormode", "RGB24"),
        "output_dir": data.get("output_dir", current_app.config.get("SCAN_DIR", "./scandir")),
    }
    
    # Set dimensions based on paper format
    paper_format = data.get("format", "A4")
    if paper_format == "A4":
        config["height"] = 3508
        config["width"] = 2480
    elif paper_format == "A5":
        config["height"] = 2480
        config["width"] = 1748
    elif paper_format == "Letter":
        config["height"] = 3300
        config["width"] = 2550
    else:
        config["height"] = 3508
        config["width"] = 2480
    
    result = bulk_scan_service.start_session(config)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@bulk_scan_bp.route('/scan-page', methods=['POST'])
def scan_page():
    """Scan and add a page to the current bulk scan session.
    
    Request Body:
        JSON with:
        - session_id: Session identifier (required)
    
    Returns:
        JSON with page_number and preview_url
    ---
    requestBody:
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        session_id:
                            type: string
                            required: true
    responses:
        200:
            description: Page scanned successfully
        400:
            description: Invalid request or scan failed
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400
    
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({
            "success": False,
            "error": "session_id is required"
        }), 400
    
    result = bulk_scan_service.scan_page(session_id)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@bulk_scan_bp.route('/preview/<session_id>/<int:page_num>', methods=['GET'])
def get_preview(session_id: str, page_num: int):
    """Get preview image for a page.
    
    Path Parameters:
        session_id: Session identifier
        page_num: Page number (1-indexed)
    
    Returns:
        JPEG image data
    ---
    responses:
        200:
            description: Preview image
            content:
                image/jpeg:
                    schema:
                        type: string
                        format: binary
        404:
            description: Page not found
    """
    preview_data = bulk_scan_service.get_preview(session_id, page_num)
    
    if preview_data:
        return send_file(
            io.BytesIO(preview_data),
            mimetype='image/jpeg'
        )
    else:
        return jsonify({
            "success": False,
            "error": "Preview not found"
        }), 404


@bulk_scan_bp.route('/delete-page', methods=['DELETE'])
def delete_page():
    """Delete a page from the bulk scan session.
    
    Request Body:
        JSON with:
        - session_id: Session identifier (required)
        - page_num: Page number to delete (required)
    
    Returns:
        JSON with result
    ---
    requestBody:
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        session_id:
                            type: string
                            required: true
                        page_num:
                            type: integer
                            required: true
    responses:
        200:
            description: Page deleted
        400:
            description: Invalid request
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400
    
    session_id = data.get('session_id')
    page_num = data.get('page_num')
    
    if not session_id or not page_num:
        return jsonify({
            "success": False,
            "error": "session_id and page_num are required"
        }), 400
    
    result = bulk_scan_service.delete_page(session_id, page_num)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@bulk_scan_bp.route('/finish', methods=['POST'])
def finish_bulk_scan():
    """Finish the bulk scan session and save the merged PDF.
    
    Request Body:
        JSON with:
        - session_id: Session identifier (required)
        - output: Output filename without extension (optional)
    
    Returns:
        JSON with filename and page count
    ---
    requestBody:
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        session_id:
                            type: string
                            required: true
                        output:
                            type: string
                            description: Output filename (without extension)
    responses:
        200:
            description: PDF saved successfully
        400:
            description: Invalid request
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400
    
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({
            "success": False,
            "error": "session_id is required"
        }), 400
    
    # Generate output filename
    from datetime import datetime
    output = data.get('output') or datetime.now().strftime("BULK_%Y%m%d_%H%M%S")
    
    result = bulk_scan_service.finish_session(session_id, output)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@bulk_scan_bp.route('/cancel', methods=['DELETE'])
def cancel_bulk_scan():
    """Cancel the bulk scan session and discard all pages.
    
    Request Body:
        JSON with:
        - session_id: Session identifier (required)
    
    Returns:
        JSON with result
    ---
    requestBody:
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        session_id:
                            type: string
                            required: true
    responses:
        200:
            description: Session cancelled
        400:
            description: Invalid request
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "success": False,
            "error": "Request body is required"
        }), 400
    
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({
            "success": False,
            "error": "session_id is required"
        }), 400
    
    result = bulk_scan_service.cancel_session(session_id)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@bulk_scan_bp.route('/status/<session_id>', methods=['GET'])
def get_status(session_id: str):
    """Get the status of a bulk scan session.
    
    Path Parameters:
        session_id: Session identifier
    
    Returns:
        JSON with session status
    ---
    responses:
        200:
            description: Session status
        404:
            description: Session not found
    """
    result = bulk_scan_service.get_session_status(session_id)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 404
