"""Pydantic schemas for stats API."""

from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


class CPUStats(BaseModel):
    """CPU statistics."""

    usage_percent: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    user: float = Field(..., ge=0, description="User space CPU time")
    system: float = Field(..., ge=0, description="System space CPU time")
    idle: float = Field(..., ge=0, description="Idle CPU time")
    cores: int = Field(..., ge=1, description="Number of CPU cores")
    load_1: float = Field(..., ge=0, description="1-minute load average")
    load_5: float = Field(..., ge=0, description="5-minute load average")
    load_15: float = Field(..., ge=0, description="15-minute load average")


class MemoryStats(BaseModel):
    """Memory statistics."""

    total: int = Field(..., ge=0, description="Total memory in bytes")
    used: int = Field(..., ge=0, description="Used memory in bytes")
    available: int = Field(..., ge=0, description="Available memory in bytes")
    percent: float = Field(..., ge=0, le=100, description="Memory usage percentage")
    free: int = Field(..., ge=0, description="Free memory in bytes")
    cached: Optional[int] = Field(None, ge=0, description="Cached memory in bytes")
    buffers: Optional[int] = Field(None, ge=0, description="Buffered memory in bytes")


class DiskStats(BaseModel):
    """Disk statistics for a filesystem."""

    mount: str = Field(..., description="Mount point")
    device: str = Field(..., description="Device name")
    total: int = Field(..., ge=0, description="Total disk space in bytes")
    used: int = Field(..., ge=0, description="Used disk space in bytes")
    free: int = Field(..., ge=0, description="Free disk space in bytes")
    percent: float = Field(..., ge=0, le=100, description="Usage percentage")
    fstype: Optional[str] = Field(None, description="Filesystem type")


class NetworkStats(BaseModel):
    """Network interface statistics."""

    interface: str = Field(..., description="Network interface name")
    bytes_sent: int = Field(..., ge=0, description="Bytes sent")
    bytes_recv: int = Field(..., ge=0, description="Bytes received")
    packets_sent: int = Field(..., ge=0, description="Packets sent")
    packets_recv: int = Field(..., ge=0, description="Packets received")
    errin: int = Field(..., ge=0, description="Errors in")
    errout: int = Field(..., ge=0, description="Errors out")
    dropin: int = Field(..., ge=0, description="Drops in")
    dropout: int = Field(..., ge=0, description="Drops out")


class SystemInfo(BaseModel):
    """System information."""

    hostname: str = Field(..., description="Hostname")
    os: str = Field(..., description="Operating system")
    kernel: str = Field(..., description="Kernel version")
    uptime_seconds: int = Field(..., ge=0, description="Uptime in seconds")
    boot_time: datetime = Field(..., description="Last boot time")
    python_version: Optional[str] = Field(None, description="Python version")
    timezone: Optional[str] = Field(None, description="System timezone")


class StatsSnapshot(BaseModel):
    """Current system statistics snapshot."""

    timestamp: datetime = Field(..., description="Collection timestamp")
    cpu: CPUStats = Field(..., description="CPU statistics")
    memory: MemoryStats = Field(..., description="Memory statistics")
    disk: List[DiskStats] = Field(..., description="Disk statistics for all mountpoints")
    network: List[NetworkStats] = Field(..., description="Network interface statistics")
    system: SystemInfo = Field(..., description="System information")


class StatsMessage(BaseModel):
    """WebSocket stats message."""

    type: str = Field(..., description="Message type (stats, error, ping, pong)")
    timestamp: datetime = Field(..., description="Message timestamp")
    data: Optional[dict] = Field(None, description="Message data")
    error: Optional[str] = Field(None, description="Error message if applicable")


class StatsHistoryPoint(BaseModel):
    """A single point in stats history."""

    timestamp: datetime = Field(..., description="Timestamp")
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    memory_used: int = Field(..., ge=0, description="Memory used in bytes")
    memory_total: int = Field(..., ge=0, description="Total memory in bytes")
    disk_used: Optional[int] = Field(None, ge=0, description="Disk used in bytes")
    disk_total: Optional[int] = Field(None, ge=0, description="Total disk in bytes")


class StatsHistory(BaseModel):
    """Historical stats data."""

    host_id: str = Field(..., description="Host ID")
    period: str = Field(..., description="Period (1h, 24h, 7d)")
    points: List[StatsHistoryPoint] = Field(..., description="Historical data points")
    start_time: datetime = Field(..., description="Start time of period")
    end_time: datetime = Field(..., description="End time of period")


class CPUAlert(BaseModel):
    """CPU usage alert."""

    level: str = Field(..., description="Alert level (warning, critical)")
    threshold: float = Field(..., ge=0, le=100, description="Threshold percentage")
    current: float = Field(..., ge=0, le=100, description="Current value")


class MemoryAlert(BaseModel):
    """Memory usage alert."""

    level: str = Field(..., description="Alert level (warning, critical)")
    threshold: float = Field(..., ge=0, le=100, description="Threshold percentage")
    current: float = Field(..., ge=0, le=100, description="Current value")


class DiskAlert(BaseModel):
    """Disk usage alert."""

    level: str = Field(..., description="Alert level (warning, critical)")
    mount: str = Field(..., description="Mount point")
    threshold: float = Field(..., ge=0, le=100, description="Threshold percentage")
    current: float = Field(..., ge=0, le=100, description="Current value")


class StatsAlerts(BaseModel):
    """Collection of active stats alerts."""

    host_id: str = Field(..., description="Host ID")
    timestamp: datetime = Field(..., description="Alert collection time")
    cpu_alerts: List[CPUAlert] = Field(..., description="CPU alerts")
    memory_alerts: List[MemoryAlert] = Field(..., description="Memory alerts")
    disk_alerts: List[DiskAlert] = Field(..., description="Disk alerts")


class StatsPreferences(BaseModel):
    """Stats monitoring preferences."""

    update_interval: int = Field(5, ge=1, le=60, description="Update interval in seconds")
    cpu_warning: float = Field(75, ge=0, le=100, description="CPU warning threshold")
    cpu_critical: float = Field(90, ge=0, le=100, description="CPU critical threshold")
    memory_warning: float = Field(80, ge=0, le=100, description="Memory warning threshold")
    memory_critical: float = Field(95, ge=0, le=100, description="Memory critical threshold")
    disk_warning: float = Field(80, ge=0, le=100, description="Disk warning threshold")
    disk_critical: float = Field(95, ge=0, le=100, description="Disk critical threshold")
    enable_alerts: bool = Field(True, description="Enable alerting")
    retention_days: int = Field(7, ge=1, le=365, description="Stats retention period in days")
