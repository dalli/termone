"""Stats collector for gathering system statistics from remote hosts."""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

from src.services.ssh_client import SSHClient
from src.exceptions import ValidationException

logger = logging.getLogger(__name__)


class StatsCollector:
    """Collects system statistics from remote hosts via SSH."""

    def __init__(self, ssh_client: SSHClient):
        """Initialize stats collector.

        Args:
            ssh_client: Connected SSH client
        """
        self.ssh_client = ssh_client

    async def collect_cpu_stats(self) -> dict:
        """Collect CPU statistics.

        Returns:
            Dictionary with CPU stats

        Raises:
            Exception: If stats collection fails
        """
        try:
            # Get CPU usage with top command
            stdout, stderr, code = await self.ssh_client.execute_command(
                "top -bn1 | grep 'Cpu(s)' | sed 's/.*, *\\([0-9.]*\\)%* id.*/\\1/' | awk '{print 100 - $1}'"
            )

            cpu_usage = float(stdout.strip()) if stdout.strip() else 0.0

            # Get load averages
            stdout, stderr, code = await self.ssh_client.execute_command(
                "cat /proc/loadavg | awk '{print $1, $2, $3}'"
            )

            load_avg = stdout.strip().split()
            load_1 = float(load_avg[0]) if len(load_avg) > 0 else 0.0
            load_5 = float(load_avg[1]) if len(load_avg) > 1 else 0.0
            load_15 = float(load_avg[2]) if len(load_avg) > 2 else 0.0

            # Get number of CPUs
            stdout, stderr, code = await self.ssh_client.execute_command(
                "nproc"
            )
            cores = int(stdout.strip()) if stdout.strip() else 1

            return {
                "usage_percent": min(100.0, max(0.0, cpu_usage)),
                "user": 0.0,
                "system": 0.0,
                "idle": 100.0 - cpu_usage,
                "cores": cores,
                "load_1": load_1,
                "load_5": load_5,
                "load_15": load_15,
            }
        except Exception as e:
            logger.error(f"Failed to collect CPU stats: {e}")
            raise

    async def collect_memory_stats(self) -> dict:
        """Collect memory statistics.

        Returns:
            Dictionary with memory stats

        Raises:
            Exception: If stats collection fails
        """
        try:
            # Get memory info from /proc/meminfo
            stdout, stderr, code = await self.ssh_client.execute_command(
                "grep -E 'MemTotal|MemAvailable|MemFree|Cached|Buffers' /proc/meminfo"
            )

            meminfo = {}
            for line in stdout.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = int(value.split()[0]) * 1024  # Convert KB to bytes
                    meminfo[key] = value

            total = meminfo.get('memtotal', 0)
            available = meminfo.get('memavailable', 0)
            free = meminfo.get('memfree', 0)
            used = total - available

            percent = (used / total * 100) if total > 0 else 0.0

            return {
                "total": total,
                "used": used,
                "available": available,
                "percent": min(100.0, max(0.0, percent)),
                "free": free,
                "cached": meminfo.get('cached', 0),
                "buffers": meminfo.get('buffers', 0),
            }
        except Exception as e:
            logger.error(f"Failed to collect memory stats: {e}")
            raise

    async def collect_disk_stats(self) -> list:
        """Collect disk statistics.

        Returns:
            List of dictionaries with disk stats per filesystem

        Raises:
            Exception: If stats collection fails
        """
        try:
            # Get disk usage from df command
            stdout, stderr, code = await self.ssh_client.execute_command(
                "df -B1 | tail -n +2"
            )

            disks = []
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue

                parts = line.split()
                if len(parts) >= 6:
                    device = parts[0]
                    total = int(parts[1])
                    used = int(parts[2])
                    available = int(parts[3])
                    percent = int(parts[4].rstrip('%'))
                    mount = parts[5]

                    disks.append({
                        "mount": mount,
                        "device": device,
                        "total": total,
                        "used": used,
                        "free": available,
                        "percent": percent,
                        "fstype": None,
                    })

            return disks
        except Exception as e:
            logger.error(f"Failed to collect disk stats: {e}")
            raise

    async def collect_network_stats(self) -> list:
        """Collect network statistics.

        Returns:
            List of dictionaries with network stats per interface

        Raises:
            Exception: If stats collection fails
        """
        try:
            # Get network stats from /proc/net/dev
            stdout, stderr, code = await self.ssh_client.execute_command(
                "cat /proc/net/dev | tail -n +3"
            )

            networks = []
            for line in stdout.strip().split('\n'):
                if ':' not in line:
                    continue

                interface, data = line.split(':', 1)
                interface = interface.strip()

                # Skip loopback
                if interface == 'lo':
                    continue

                parts = data.split()
                if len(parts) >= 8:
                    networks.append({
                        "interface": interface,
                        "bytes_recv": int(parts[0]),
                        "packets_recv": int(parts[1]),
                        "errin": int(parts[2]),
                        "dropin": int(parts[3]),
                        "bytes_sent": int(parts[8]),
                        "packets_sent": int(parts[9]),
                        "errout": int(parts[10]),
                        "dropout": int(parts[11]),
                    })

            return networks
        except Exception as e:
            logger.error(f"Failed to collect network stats: {e}")
            raise

    async def collect_system_info(self) -> dict:
        """Collect system information.

        Returns:
            Dictionary with system info

        Raises:
            Exception: If stats collection fails
        """
        try:
            # Get hostname
            stdout, stderr, code = await self.ssh_client.execute_command(
                "hostname"
            )
            hostname = stdout.strip()

            # Get OS info
            stdout, stderr, code = await self.ssh_client.execute_command(
                "cat /etc/os-release | grep -E '^NAME=' | cut -d= -f2 | tr -d '\"'"
            )
            os_name = stdout.strip() if stdout.strip() else "Unknown"

            # Get kernel version
            stdout, stderr, code = await self.ssh_client.execute_command(
                "uname -r"
            )
            kernel = stdout.strip()

            # Get uptime
            stdout, stderr, code = await self.ssh_client.execute_command(
                "cat /proc/uptime | awk '{print $1}'"
            )
            uptime_seconds = int(float(stdout.strip())) if stdout.strip() else 0

            # Get boot time
            now = datetime.utcnow()
            boot_time = now - timedelta(seconds=uptime_seconds)

            return {
                "hostname": hostname,
                "os": os_name,
                "kernel": kernel,
                "uptime_seconds": uptime_seconds,
                "boot_time": boot_time.isoformat(),
                "python_version": None,
                "timezone": None,
            }
        except Exception as e:
            logger.error(f"Failed to collect system info: {e}")
            raise

    async def collect_all_stats(self) -> dict:
        """Collect all system statistics.

        Returns:
            Dictionary with all stats

        Raises:
            Exception: If any stats collection fails
        """
        try:
            cpu = await self.collect_cpu_stats()
            memory = await self.collect_memory_stats()
            disk = await self.collect_disk_stats()
            network = await self.collect_network_stats()
            system = await self.collect_system_info()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": cpu,
                "memory": memory,
                "disk": disk,
                "network": network,
                "system": system,
            }
        except Exception as e:
            logger.error(f"Failed to collect all stats: {e}")
            raise
