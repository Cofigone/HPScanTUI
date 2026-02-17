"""Flask application factory."""
from flask import Flask
from flask_cors import CORS


def create_app(config_name='default'):
    """Create and configure the Flask application.
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
    
    Returns:
        Flask application instance
    """
    from config import config
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Enable CORS for frontend communication
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Ensure scan directory exists
    from pathlib import Path
    scan_dir = Path(app.config['SCAN_DIR'])
    scan_dir.mkdir(parents=True, exist_ok=True)
    
    # Register blueprints
    from app.routes.scanner import scanner_bp
    from app.routes.files import files_bp
    from app.routes.bulk_scan import bulk_scan_bp
    
    app.register_blueprint(scanner_bp, url_prefix='/api/scanner')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(bulk_scan_bp, url_prefix='/api/scanner/bulk')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'hpscan-backend'}
    
    return app
