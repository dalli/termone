/**
 * TunnelList component for displaying active SSH tunnels.
 */

import React, { useEffect } from 'react';
import { useTunnels, Tunnel } from '../../hooks/useTunnels';

interface TunnelListProps {
  hostId?: string;
  onSelectTunnel?: (tunnel: Tunnel) => void;
}

const statusColors = {
  connected: 'bg-green-100 text-green-800',
  disconnected: 'bg-gray-100 text-gray-800',
  connecting: 'bg-blue-100 text-blue-800',
  reconnecting: 'bg-yellow-100 text-yellow-800',
  failed: 'bg-red-100 text-red-800',
};

const statusIcons = {
  connected: '🟢',
  disconnected: '⚪',
  connecting: '🔵',
  reconnecting: '🟡',
  failed: '🔴',
};

export const TunnelList: React.FC<TunnelListProps> = ({ hostId, onSelectTunnel }) => {
  const { tunnels, isLoading, error, listTunnels, startTunnel, stopTunnel, deleteTunnel, clearError } = useTunnels(hostId);

  useEffect(() => {
    if (hostId) {
      listTunnels(hostId);
    }
  }, [hostId, listTunnels]);

  const handleStart = async (e: React.MouseEvent, tunnelId: string) => {
    e.stopPropagation();
    try {
      await startTunnel(tunnelId);
    } catch (err) {
      console.error('Failed to start tunnel:', err);
    }
  };

  const handleStop = async (e: React.MouseEvent, tunnelId: string) => {
    e.stopPropagation();
    try {
      await stopTunnel(tunnelId);
    } catch (err) {
      console.error('Failed to stop tunnel:', err);
    }
  };

  const handleDelete = async (e: React.MouseEvent, tunnelId: string) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this tunnel?')) {
      return;
    }
    try {
      await deleteTunnel(tunnelId);
    } catch (err) {
      console.error('Failed to delete tunnel:', err);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="border-b p-4">
        <h2 className="text-lg font-semibold">SSH Tunnels</h2>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 p-4 text-red-700 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button onClick={clearError} className="text-red-500 hover:text-red-700">
            ✕
          </button>
        </div>
      )}

      {/* Tunnel list */}
      <div className="overflow-x-auto">
        {isLoading ? (
          <div className="flex items-center justify-center p-8 text-gray-500">
            Loading tunnels...
          </div>
        ) : tunnels.length === 0 ? (
          <div className="flex items-center justify-center p-8 text-gray-500">
            No tunnels configured
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="p-3 text-left font-semibold text-gray-700">Name</th>
                <th className="p-3 text-left font-semibold text-gray-700">Type</th>
                <th className="p-3 text-left font-semibold text-gray-700">Configuration</th>
                <th className="p-3 text-center font-semibold text-gray-700 w-24">Status</th>
                <th className="p-3 text-center font-semibold text-gray-700 w-32">Actions</th>
              </tr>
            </thead>
            <tbody>
              {tunnels.map((tunnel) => (
                <tr
                  key={tunnel.id}
                  className="border-b hover:bg-gray-50 cursor-pointer"
                  onClick={() => onSelectTunnel?.(tunnel)}
                >
                  <td className="p-3 font-medium text-gray-900">
                    {tunnel.name}
                  </td>
                  <td className="p-3 text-gray-600">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                      tunnel.tunnel_type === 'local'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-purple-100 text-purple-800'
                    }`}>
                      {tunnel.tunnel_type.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-3 text-gray-600 text-xs font-mono">
                    <div>
                      {tunnel.tunnel_type === 'local'
                        ? `${tunnel.bind_address}:${tunnel.local_port} → ${tunnel.remote_host}:${tunnel.remote_port}`
                        : `${tunnel.remote_host}:${tunnel.remote_port} → ${tunnel.bind_address}:${tunnel.local_port}`}
                    </div>
                    {tunnel.error && (
                      <div className="text-red-600 mt-1">Error: {tunnel.error}</div>
                    )}
                  </td>
                  <td className="p-3 text-center">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${
                      statusColors[tunnel.status as keyof typeof statusColors]
                    }`}>
                      {statusIcons[tunnel.status as keyof typeof statusIcons]}
                      {tunnel.status}
                    </span>
                  </td>
                  <td className="p-3 text-center">
                    <div className="flex gap-2 justify-center">
                      {tunnel.connected ? (
                        <button
                          onClick={(e) => handleStop(e, tunnel.id)}
                          disabled={isLoading}
                          className="text-red-600 hover:text-red-800 disabled:opacity-50"
                          title="Stop tunnel"
                        >
                          ⏹️
                        </button>
                      ) : (
                        <button
                          onClick={(e) => handleStart(e, tunnel.id)}
                          disabled={isLoading}
                          className="text-green-600 hover:text-green-800 disabled:opacity-50"
                          title="Start tunnel"
                        >
                          ▶️
                        </button>
                      )}
                      <button
                        onClick={(e) => handleDelete(e, tunnel.id)}
                        disabled={isLoading}
                        className="text-gray-600 hover:text-gray-800 disabled:opacity-50"
                        title="Delete tunnel"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Status bar */}
      <div className="border-t p-3 bg-gray-50 text-xs text-gray-600">
        {tunnels.length} tunnel(s) · {tunnels.filter(t => t.connected).length} connected
      </div>
    </div>
  );
};
