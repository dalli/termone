/**
 * TunnelStatus component for displaying real-time tunnel status.
 */

import React, { useEffect, useState } from 'react';
import { useTunnels, Tunnel, TunnelStatus } from '../../hooks/useTunnels';

interface TunnelStatusProps {
  tunnel?: Tunnel;
  autoRefresh?: number; // refresh interval in seconds
}

export const TunnelStatusComponent: React.FC<TunnelStatusProps> = ({
  tunnel,
  autoRefresh = 5,
}) => {
  const { getTunnelStatus } = useTunnels();
  const [status, setStatus] = useState<TunnelStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-refresh status
  useEffect(() => {
    if (!tunnel) return;

    const fetchStatus = async () => {
      setIsLoading(true);
      try {
        const result = await getTunnelStatus(tunnel.id);
        setStatus(result);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch status');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, autoRefresh * 1000);
    return () => clearInterval(interval);
  }, [tunnel, getTunnelStatus, autoRefresh]);

  if (!tunnel) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-gray-500 text-center py-8">
          Select a tunnel to view its status
        </div>
      </div>
    );
  }

  const statusIcon = {
    connected: '🟢',
    disconnected: '⚪',
    connecting: '🔵',
    reconnecting: '🟡',
    failed: '🔴',
  }[status?.status || 'disconnected'];

  const statusColor = {
    connected: 'text-green-700',
    disconnected: 'text-gray-700',
    connecting: 'text-blue-700',
    reconnecting: 'text-yellow-700',
    failed: 'text-red-700',
  }[status?.status || 'disconnected'];

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    }
    if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">{tunnel.name}</h2>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Status overview */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Status indicator */}
        <div className="bg-gray-50 rounded p-4">
          <div className="text-xs font-semibold text-gray-600 mb-2">CONNECTION STATUS</div>
          {isLoading ? (
            <div className="text-gray-500">Loading...</div>
          ) : (
            <div className={`flex items-center gap-2 text-lg font-semibold ${statusColor}`}>
              {statusIcon}
              {status?.status || 'unknown'}
            </div>
          )}
        </div>

        {/* Uptime */}
        <div className="bg-gray-50 rounded p-4">
          <div className="text-xs font-semibold text-gray-600 mb-2">UPTIME</div>
          {status ? (
            <div className="text-lg font-semibold text-gray-900">
              {formatUptime(status.uptime_seconds)}
            </div>
          ) : (
            <div className="text-gray-500">—</div>
          )}
        </div>

        {/* Error count */}
        <div className="bg-gray-50 rounded p-4">
          <div className="text-xs font-semibold text-gray-600 mb-2">ERROR COUNT</div>
          {status ? (
            <div
              className={`text-lg font-semibold ${
                status.error_count > 0 ? 'text-red-600' : 'text-green-600'
              }`}
            >
              {status.error_count}
            </div>
          ) : (
            <div className="text-gray-500">—</div>
          )}
        </div>

        {/* Configuration */}
        <div className="bg-gray-50 rounded p-4">
          <div className="text-xs font-semibold text-gray-600 mb-2">CONFIGURATION</div>
          <div className="text-xs font-mono text-gray-700">
            {tunnel.tunnel_type === 'local'
              ? `${tunnel.bind_address}:${tunnel.local_port}`
              : `${tunnel.remote_host}:${tunnel.remote_port}`}
          </div>
        </div>
      </div>

      {/* Detailed info */}
      <div className="bg-gray-50 rounded p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">DETAILED INFORMATION</h3>

        <div className="space-y-2 text-sm">
          {/* Connected status */}
          <div className="flex justify-between">
            <span className="text-gray-600">Connected:</span>
            <span className="font-semibold text-gray-900">
              {status?.connected ? 'Yes' : 'No'}
            </span>
          </div>

          {/* Last connection time */}
          {status?.last_connection_time && (
            <div className="flex justify-between">
              <span className="text-gray-600">Last Connected:</span>
              <span className="font-mono text-gray-900 text-xs">
                {new Date(status.last_connection_time).toLocaleString()}
              </span>
            </div>
          )}

          {/* Last disconnection time */}
          {status?.last_disconnection_time && (
            <div className="flex justify-between">
              <span className="text-gray-600">Last Disconnected:</span>
              <span className="font-mono text-gray-900 text-xs">
                {new Date(status.last_disconnection_time).toLocaleString()}
              </span>
            </div>
          )}

          {/* Current error */}
          {status?.error && (
            <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-xs">
              <div className="font-semibold">Current Error:</div>
              <div>{status.error}</div>
            </div>
          )}

          {/* Last error */}
          {status?.last_error && status.last_error !== status?.error && (
            <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-700 text-xs">
              <div className="font-semibold">Last Error:</div>
              <div>{status.last_error}</div>
            </div>
          )}
        </div>
      </div>

      {/* Configuration details */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded p-4 text-xs">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">TUNNEL CONFIGURATION</h3>
        <div className="space-y-1 font-mono text-blue-800">
          <div>
            <span className="font-semibold">Type:</span> {tunnel.tunnel_type}
          </div>
          <div>
            <span className="font-semibold">Local:</span> {tunnel.bind_address}:{tunnel.local_port}
          </div>
          <div>
            <span className="font-semibold">Remote:</span> {tunnel.remote_host}:{tunnel.remote_port}
          </div>
          <div>
            <span className="font-semibold">Auto-reconnect:</span> {tunnel.auto_reconnect ? 'enabled' : 'disabled'}
          </div>
        </div>
      </div>
    </div>
  );
};
