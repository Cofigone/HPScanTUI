"""Scanner API routes."""
from flask import Blueprint, request, jsonify, current_app
from app.services.scan_service import scan_service

scanner_bp = Blueprint('scanner', __name__)


@scanner_bp.route('/status', methods=['GET'])
def get_status():
    """Get the current scanner status.
    
    Returns:
        JSON with scanning status, progress, and status message
    ---
    responses:
        200:
            description: Scanner status
            schema:
                type: object
                properties:
                    scanning:
                        type: boolean
                    progress:
                        type: integer
                    status:
                        type: string
    """
    return jsonify(scan_service.get_status())


@scanner_bp.route('/capabilities', methods=['GET'])
def get_capabilities():
    """Get printer capabilities.
    
    Query Parameters:
        ip: Printer IP address
    
    Returns:
        JSON with printer capabilities
    ---
    parameters:
        - name: ip
          in: query
          type: string
          required: true
          description: Printer IP address
    responses:
        200:
            description: Printer capabilities
        400:
            description: Missing IP parameter
        500:
            description: Error getting capabilities
    """
    ip = request.args.get('ip')
    
    if not ip:
        return jsonify({
            "success": False,
            "error": "IP parameter is required"
        }), 400
    
    result = scan_service.get_printer_capabilities(ip)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 500


@scanner_bp.route('/scan', methods=['POST'])
def start_scan():
    """Start a new scan job.
    
    Request Body:
        JSON with scan configuration:
        - ip: Printer IP address
        - dpi: Scan resolution (default: 300)
        - format: Paper format (A4, A5, Letter)
        - colormode: Color mode (RGB24, Grayscale8, etc.)
        - pdf: Output format (true for PDF, false for JPEG)
        - output: Output filename (without extension)
        - output_dir: Output directory path
    
    Returns:
        JSON with success status and message
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
                            default: A4
                        colormode:
                            type: string
                            default: RGB24
                        pdf:
                            type: boolean
                            default: true
                        output:
                            type: string
                        output_dir:
                            type: string
    responses:
        200:
            description: Scan started successfully
        400:
            description: Invalid request or scan already in progress
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
        "pdf": data.get("pdf", True),
        "output": data.get("output"),
        "output_dir": data.get("output_dir", current_app.config.get("SCAN_DIR", "./scandir")),
        "bulk": False
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
        # Default to A4
        config["height"] = 3508
        config["width"] = 2480
    
    result = scan_service.start_scan(config)
    
    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(result), 400


@scanner_bp.route('/progress', methods=['GET'])
def get_progress():
    """Get current scan progress.
    
    Returns:
        JSON with scanning status, progress percentage, and status message
    ---
    responses:
        200:
            description: Scan progress
    """
    status = scan_service.get_status()
    return jsonify({
        "scanning": status["scanning"],
        "progress": status["progress"],
        "status": status["status"],
        "error": status.get("error"),
        "result": status.get("result")
    })


@scanner_bp.route('/search', methods=['POST'])
def search_printers():
    """Search for printers on the network.
    
    This endpoint starts a network search for HP printers.
    The search progress can be tracked via the /search/progress endpoint.
    
    Returns:
        JSON with discovered printers list
    ---
    responses:
        200:
            description: List of discovered printers
    """
    from threading import Thread
    import time
    
    # Store search state
    search_state = {
        "searching": True,
        "progress": 0,
        "total": 253,
        "printers": []
    }
    
    def search_worker():
        def progress_callback(current, total):
            search_state["progress"] = current
            search_state["total"] = total
        
        printers = scan_service.search_printers(progress_callback)
        search_state["printers"] = printers
        search_state["searching"] = False
    
    # Run search in background
    thread = Thread(target=search_worker, daemon=True)
    thread.start()
    
    # Wait for search to complete (with timeout)
    timeout = 60  # 60 seconds timeout
    start_time = time.time()
    while search_state["searching"] and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    return jsonify({
        "success": True,
        "printers": search_state["printers"],
        "searched": search_state["progress"],
        "total": search_state["total"]
    })


@scanner_bp.route('/check', methods=['GET'])
def check_printer():
    """Check if a printer is reachable.
    
    Query Parameters:
        ip: Printer IP address
    
    Returns:
        JSON with reachable status
    ---
    parameters:
        - name: ip
          in: query
          type: string
          required: true
    responses:
        200:
            description: Printer reachability status
    """
    ip = request.args.get('ip')
    
    if not ip:
        return jsonify({
            "success": False,
            "error": "IP parameter is required"
        }), 400
    
    reachable = scan_service.check_printer(ip)
    
    return jsonify({
        "success": True,
        "ip": ip,
        "reachable": reachable
    })
