"""Configuration settings for the Flask backend."""
import os
from pathlib import Path


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SCAN_DIR = os.environ.get('SCAN_DIR', './scandir')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SCAN_DIR = '/tmp/test_scans'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
