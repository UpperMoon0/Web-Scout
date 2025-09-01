#!/usr/bin/env python3
"""
Monitoring models for Web-Scout
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class ServiceStatus(BaseModel):
    """Model for individual service status."""
    
    name: str
    status: str  # "healthy", "degraded", "down"
    details: Optional[Dict[str, Any]] = None
    last_updated: str


class SystemMetrics(BaseModel):
    """Model for system metrics."""
    
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    uptime: Optional[str] = None


class MonitoringResponse(BaseModel):
    """Response model for system monitoring."""
    
    status: str  # "healthy", "degraded", "down"
    service_name: str
    version: str
    timestamp: str
    metrics: Optional[SystemMetrics] = None
    services: Optional[List[ServiceStatus]] = None
    details: Optional[Dict[str, Any]] = None