"""
Configuration file for Web Scout MCP Server

This file contains configuration settings and environment variable definitions.
"""

import os
from typing import Any, Dict

# Default configuration
DEFAULT_CONFIG = {
    # Server settings
    "server_name": "web-scout-server",
    "server_version": "0.1.0",
    
    # Web scraping settings
    "user_agent": "Web-Scout-MCP/0.1.0",
    "max_retries": 3,
    "timeout": 30,
    "enable_headless": True,
    
    # Cache settings
    "cache_dir": ".web_scout_cache",
    "cache_ttl": 3600,  # 1 hour
    
    # Rate limiting
    "requests_per_minute": 60,
    "burst_requests": 10,
    
    # Content limits
    "max_content_length": 1024 * 1024,  # 1MB
    "max_results_per_search": 100,
    
    # Monitoring
    "monitoring_enabled": True,
    "monitoring_interval": 300,  # 5 minutes
    
    # Logging
    "log_level": "INFO",
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}


def get_config() -> Dict[str, Any]:
    """
    Get configuration from environment variables with defaults.
    
    Returns:
        Dictionary containing all configuration values
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables
    config.update({
        "user_agent": os.getenv("WEB_SCOUT_USER_AGENT", config["user_agent"]),
        "max_retries": int(os.getenv("WEB_SCOUT_MAX_RETRIES", str(config["max_retries"]))),
        "timeout": int(os.getenv("WEB_SCOUT_TIMEOUT", str(config["timeout"]))),
        "enable_headless": os.getenv("WEB_SCOUT_HEADLESS", "true").lower() != "false",
        "cache_dir": os.getenv("WEB_SCOUT_CACHE_DIR", config["cache_dir"]),
        "cache_ttl": int(os.getenv("WEB_SCOUT_CACHE_TTL", str(config["cache_ttl"]))),
        "requests_per_minute": int(os.getenv("WEB_SCOUT_RATE_LIMIT", str(config["requests_per_minute"]))),
        "max_content_length": int(os.getenv("WEB_SCOUT_MAX_CONTENT", str(config["max_content_length"]))),
        "monitoring_enabled": os.getenv("WEB_SCOUT_MONITORING", "true").lower() == "true",
        "log_level": os.getenv("WEB_SCOUT_LOG_LEVEL", config["log_level"]),
    })
    
    # API keys (optional)
    config.update({
        "google_api_key": os.getenv("GOOGLE_API_KEY"),
        "google_cse_id": os.getenv("GOOGLE_CSE_ID"),
        "bing_api_key": os.getenv("BING_API_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
    })
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration values.
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        True if configuration is valid, False otherwise
    """
    # Check required string values
    if not config.get("user_agent"):
        return False
    
    # Check numeric values
    if config.get("max_retries", 0) <= 0:
        return False
    
    if config.get("timeout", 0) <= 0:
        return False
    
    if config.get("cache_ttl", 0) <= 0:
        return False
    
    # Check cache directory can be created
    cache_dir = config.get("cache_dir")
    if cache_dir:
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except (OSError, PermissionError):
            return False
    
    return True


# Environment-specific configurations
DEVELOPMENT_CONFIG = {
    "log_level": "DEBUG",
    "enable_headless": False,  # Show browser in development
    "timeout": 60,  # Longer timeout for development
}

PRODUCTION_CONFIG = {
    "log_level": "INFO",
    "enable_headless": True,
    "timeout": 30,
    "monitoring_enabled": True,
}

TESTING_CONFIG = {
    "log_level": "WARNING",
    "cache_dir": ".test_cache",
    "timeout": 10,  # Shorter timeout for tests
    "max_retries": 1,
    "monitoring_enabled": False,
}


def get_environment_config(environment: str = None) -> Dict[str, Any]:
    """
    Get configuration for a specific environment.
    
    Args:
        environment: Environment name ('development', 'production', 'testing')
                   If None, uses WEB_SCOUT_ENV environment variable
    
    Returns:
        Configuration dictionary for the specified environment
    """
    if environment is None:
        environment = os.getenv("WEB_SCOUT_ENV", "production").lower()
    
    base_config = get_config()
    
    if environment == "development":
        base_config.update(DEVELOPMENT_CONFIG)
    elif environment == "production":
        base_config.update(PRODUCTION_CONFIG)
    elif environment == "testing":
        base_config.update(TESTING_CONFIG)
    
    return base_config