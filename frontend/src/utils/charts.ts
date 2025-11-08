/**
 * Chart utilities for formatting stats data
 */

export interface ChartDataPoint {
  timestamp: number;
  label: string;
  value: number;
}

export interface ChartDataset {
  label: string;
  data: number[];
  borderColor?: string;
  backgroundColor?: string;
  tension?: number;
  fill?: boolean;
}

/**
 * Format timestamp to readable label
 */
export function formatTimestamp(timestamp: string | number): string {
  const date = typeof timestamp === 'string' ? new Date(timestamp) : new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Format bytes to human readable format
 */
export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Format percentage value
 */
export function formatPercent(value: number): string {
  return Math.round(value * 100) / 100 + '%';
}

/**
 * Format uptime in human readable format
 */
export function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) {
    return `${days}d ${hours}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else {
    return `${minutes}m`;
  }
}

/**
 * Aggregate stats data over a period
 */
export function aggregateStats(
  dataPoints: any[],
  period: '1h' | '24h' | '7d' = '1h'
): ChartDataPoint[] {
  if (dataPoints.length === 0) return [];

  const aggregated: ChartDataPoint[] = [];
  let currentBucket: any[] = [];
  let lastTimestamp = 0;

  const bucketInterval = getPeriodInterval(period);

  dataPoints.forEach((point) => {
    const timestamp = typeof point.timestamp === 'string'
      ? new Date(point.timestamp).getTime()
      : point.timestamp;

    if (timestamp - lastTimestamp >= bucketInterval || currentBucket.length === 0) {
      if (currentBucket.length > 0) {
        const avgValue =
          currentBucket.reduce((sum, p) => sum + (p.cpu_usage || p.memory_used || 0), 0) /
          currentBucket.length;

        aggregated.push({
          timestamp: lastTimestamp,
          label: formatTimestamp(lastTimestamp),
          value: Math.round(avgValue * 100) / 100,
        });
      }

      currentBucket = [point];
      lastTimestamp = timestamp;
    } else {
      currentBucket.push(point);
    }
  });

  // Add last bucket
  if (currentBucket.length > 0) {
    const avgValue =
      currentBucket.reduce((sum, p) => sum + (p.cpu_usage || p.memory_used || 0), 0) /
      currentBucket.length;

    aggregated.push({
      timestamp: lastTimestamp,
      label: formatTimestamp(lastTimestamp),
      value: Math.round(avgValue * 100) / 100,
    });
  }

  return aggregated;
}

/**
 * Get interval in milliseconds for a period
 */
function getPeriodInterval(period: '1h' | '24h' | '7d'): number {
  const intervals: Record<string, number> = {
    '1h': 60 * 1000, // 1 minute
    '24h': 5 * 60 * 1000, // 5 minutes
    '7d': 30 * 60 * 1000, // 30 minutes
  };

  return intervals[period] || 60 * 1000;
}

/**
 * Create chart data from stats snapshot
 */
export function createCPUChartData(stats: any): any {
  return {
    labels: ['Usage'],
    datasets: [
      {
        label: 'CPU Usage %',
        data: [stats.cpu?.usage_percent || 0],
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        borderWidth: 2,
      },
    ],
  };
}

/**
 * Create memory chart data
 */
export function createMemoryChartData(stats: any): any {
  const memory = stats.memory || {};
  const total = memory.total || 1;
  const used = memory.used || 0;
  const free = total - used;

  return {
    labels: ['Used', 'Free'],
    datasets: [
      {
        data: [used, free],
        backgroundColor: ['#ef4444', '#10b981'],
        borderColor: ['#dc2626', '#059669'],
        borderWidth: 2,
      },
    ],
  };
}

/**
 * Create disk chart data
 */
export function createDiskChartData(stats: any): any {
  const disks = stats.disk || [];
  const primaryDisk = disks[0];

  if (!primaryDisk) {
    return {
      labels: ['No Data'],
      datasets: [],
    };
  }

  return {
    labels: [primaryDisk.mount],
    datasets: [
      {
        label: 'Disk Usage %',
        data: [primaryDisk.percent || 0],
        borderColor: '#8b5cf6',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        borderWidth: 2,
      },
    ],
  };
}

/**
 * Create network chart data
 */
export function createNetworkChartData(stats: any): any {
  const networks = stats.network || [];
  const primaryInterface = networks.find((n: any) => n.interface !== 'lo');

  if (!primaryInterface) {
    return {
      labels: ['No Data'],
      datasets: [],
    };
  }

  return {
    labels: ['Sent', 'Received'],
    datasets: [
      {
        data: [
          primaryInterface.bytes_sent,
          primaryInterface.bytes_recv,
        ],
        backgroundColor: ['#06b6d4', '#3b82f6'],
        borderColor: ['#0891b2', '#1d4ed8'],
        borderWidth: 2,
      },
    ],
  };
}

/**
 * Get status color based on percentage
 */
export function getStatusColor(
  percent: number,
  warningThreshold: number = 75,
  criticalThreshold: number = 90
): string {
  if (percent >= criticalThreshold) {
    return '#ef4444'; // Red
  } else if (percent >= warningThreshold) {
    return '#f59e0b'; // Amber
  } else {
    return '#10b981'; // Green
  }
}

/**
 * Get status label
 */
export function getStatusLabel(
  percent: number,
  warningThreshold: number = 75,
  criticalThreshold: number = 90
): string {
  if (percent >= criticalThreshold) {
    return 'Critical';
  } else if (percent >= warningThreshold) {
    return 'Warning';
  } else {
    return 'Healthy';
  }
}
