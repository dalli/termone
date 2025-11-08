/**
 * TunnelForm component for creating and editing SSH tunnels.
 */

import React, { useState, useEffect } from 'react';
import { useTunnels, Tunnel, TunnelCreateRequest } from '../../hooks/useTunnels';

interface TunnelFormProps {
  hostId: string;
  tunnel?: Tunnel;
  onSuccess?: (tunnel: Tunnel) => void;
  onCancel?: () => void;
}

export const TunnelForm: React.FC<TunnelFormProps> = ({
  hostId,
  tunnel,
  onSuccess,
  onCancel,
}) => {
  const { createTunnel, updateTunnel, isLoading, error, clearError } = useTunnels();

  const [formData, setFormData] = useState({
    name: tunnel?.name || '',
    tunnel_type: (tunnel?.tunnel_type || 'local') as 'local' | 'remote',
    local_port: tunnel?.local_port || 8888,
    remote_host: tunnel?.remote_host || 'localhost',
    remote_port: tunnel?.remote_port || 3306,
    bind_address: tunnel?.bind_address || '127.0.0.1',
    enabled: tunnel?.enabled !== false,
    auto_reconnect: tunnel?.auto_reconnect !== false,
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        type === 'checkbox' ? (e.target as HTMLInputElement).checked : type === 'number' ? parseInt(value) : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      if (tunnel) {
        // Update
        const { name, tunnel_type, ...updateData } = formData;
        await updateTunnel(tunnel.id, {
          name,
          ...updateData,
        });
      } else {
        // Create
        const request: TunnelCreateRequest = {
          host_id: hostId,
          ...formData,
        };
        await createTunnel(request);
      }

      onSuccess?.(formData as any);
      // Reset form
      setFormData({
        name: '',
        tunnel_type: 'local',
        local_port: 8888,
        remote_host: 'localhost',
        remote_port: 3306,
        bind_address: '127.0.0.1',
        enabled: true,
        auto_reconnect: true,
      });
    } catch (err) {
      console.error('Failed to submit form:', err);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">
        {tunnel ? 'Edit Tunnel' : 'Create Tunnel'}
      </h2>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tunnel Name
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            placeholder="e.g., MySQL Remote"
            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Tunnel Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tunnel Type
          </label>
          <select
            name="tunnel_type"
            value={formData.tunnel_type}
            onChange={handleChange}
            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="local">Local Forwarding (localhost:local → remote:remote)</option>
            <option value="remote">Remote Forwarding (remote:remote → localhost:local)</option>
          </select>
        </div>

        {/* Configuration grid */}
        <div className="grid grid-cols-2 gap-4">
          {/* Bind Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bind Address
            </label>
            <input
              type="text"
              name="bind_address"
              value={formData.bind_address}
              onChange={handleChange}
              placeholder="127.0.0.1"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Local Port */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Local Port
            </label>
            <input
              type="number"
              name="local_port"
              value={formData.local_port}
              onChange={handleChange}
              min="1"
              max="65535"
              required
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Remote Host */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Remote Host
            </label>
            <input
              type="text"
              name="remote_host"
              value={formData.remote_host}
              onChange={handleChange}
              required
              placeholder="hostname or IP"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Remote Port */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Remote Port
            </label>
            <input
              type="number"
              name="remote_port"
              value={formData.remote_port}
              onChange={handleChange}
              min="1"
              max="65535"
              required
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Checkboxes */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              name="enabled"
              checked={formData.enabled}
              onChange={handleChange}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Enable tunnel on creation</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              name="auto_reconnect"
              checked={formData.auto_reconnect}
              onChange={handleChange}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Auto-reconnect on disconnect</span>
          </label>
        </div>

        {/* Buttons */}
        <div className="flex gap-2 pt-4">
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {tunnel ? 'Update Tunnel' : 'Create Tunnel'}
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={isLoading}
              className="px-4 py-2 bg-gray-300 hover:bg-gray-400 disabled:opacity-50 rounded font-medium"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {/* Configuration preview */}
      <div className="mt-6 p-4 bg-gray-50 rounded text-xs font-mono text-gray-600">
        <div className="font-semibold text-gray-700 mb-2">Configuration:</div>
        {formData.tunnel_type === 'local' ? (
          <div>
            Local: {formData.bind_address}:{formData.local_port} → Remote: {formData.remote_host}:
            {formData.remote_port}
          </div>
        ) : (
          <div>
            Remote: {formData.remote_host}:{formData.remote_port} → Local: {formData.bind_address}:
            {formData.local_port}
          </div>
        )}
      </div>
    </div>
  );
};
