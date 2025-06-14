"""
Configuration for the ENGRAM Memory System.

This allows easy toggling of the engram features without impacting
the core BitterBot functionality.
"""

import os
from typing import Dict, Any

# Master feature flag - set to False to completely disable engrams
ENGRAM_ENABLED = os.getenv("ENGRAM_ENABLED", "true").lower() == "true"

# Performance tuning
ENGRAM_CONFIG: Dict[str, Any] = {
    # Feature flags
    "enabled": ENGRAM_ENABLED,
    "auto_consolidation": True,  # Automatic consolidation on token threshold
    "surprise_detection": True,  # Enable surprise-based consolidation
    "dashboard_enabled": True,   # Enable real-time dashboard
    
    # Thresholds
    "chunk_size": 5000,         # Tokens per engram
    "min_messages": 3,          # Minimum messages for consolidation
    "surprise_threshold": 0.7,  # Surprise score trigger
    "max_context_engrams": 5,   # Max engrams in context
    
    # Performance
    "async_creation": True,     # Create engrams asynchronously
    "broadcast_events": True,   # Send events to dashboard
    "cleanup_days": 30,         # Days before cleanup
    "cleanup_relevance": 0.1,   # Min relevance to keep
    
    # Resource limits
    "max_summary_tokens": 300,  # Max tokens per engram summary
    "max_buffer_size": 100,     # Max messages in buffer
    "consolidation_timeout": 30, # Seconds before timeout
}

def is_engram_enabled() -> bool:
    """Check if engram system is enabled."""
    return ENGRAM_CONFIG["enabled"]

def get_engram_setting(key: str, default: Any = None) -> Any:
    """Get a specific engram configuration setting."""
    return ENGRAM_CONFIG.get(key, default)