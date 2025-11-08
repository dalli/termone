/**
 * Tunnels page - SSH tunnel management
 */

import React, { useState } from 'react';
import { TunnelList } from '../components/tunnels/TunnelList';
import { TunnelForm } from '../components/tunnels/TunnelForm';
import { TunnelStatusComponent } from '../components/tunnels/TunnelStatus';
import { Tunnel } from '../hooks/useTunnels';

interface HostOption {
  id: string;
  hostname: string;
}

export default function TunnelsPage() {
  const [selectedHostId, setSelectedHostId] = useState<string>('');
  const [hostList, setHostList] = useState<HostOption[]>([]);
  const [selectedTunnel, setSelectedTunnel] = useState<Tunnel | null>(null);
  const [showForm, setShowForm] = useState(false);

  // Load host list on mount
  React.useEffect(() => {
    const loadHosts = async () => {
      try {
        // This would be replaced with actual API call
        const mockHosts: HostOption[] = [
          { id: '1', hostname: 'prod-server-1' },
          { id: '2', hostname: 'dev-server' },
        ];
        setHostList(mockHosts);
      } catch (err) {
        console.error('Failed to load hosts:', err);
      }
    };

    loadHosts();
  }, []);

  const handleHostSelect = (hostId: string) => {
    setSelectedHostId(hostId);
    setSelectedTunnel(null);
    setShowForm(false);
  };

  const handleTunnelSelect = (tunnel: Tunnel) => {
    setSelectedTunnel(tunnel);
    setShowForm(false);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setSelectedTunnel(null);
  };

  if (!selectedHostId) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">SSH Tunnels</h1>

          <div className="bg-white rounded-lg shadow p-6">
            <label className="block mb-4">
              <span className="text-gray-700 font-semibold mb-2 block">
                Select Host
              </span>
              <select
                value={selectedHostId}
                onChange={(e) => handleHostSelect(e.target.value)}
                className="w-full max-w-xs px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Choose a host...</option>
                {hostList.map((host) => (
                  <option key={host.id} value={host.id}>
                    {host.hostname}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">SSH Tunnels</h1>
          <div className="flex items-center gap-4">
            <select
              value={selectedHostId}
              onChange={(e) => handleHostSelect(e.target.value)}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Choose a host...</option>
              {hostList.map((host) => (
                <option key={host.id} value={host.id}>
                  {host.hostname}
                </option>
              ))}
            </select>
            <button
              onClick={() => {
                setShowForm(!showForm);
                setSelectedTunnel(null);
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium"
            >
              + New Tunnel
            </button>
          </div>
        </div>

        {/* Main content */}
        <div className="grid grid-cols-3 gap-6">
          {/* Tunnel list */}
          <div className="col-span-2">
            <TunnelList hostId={selectedHostId} onSelectTunnel={handleTunnelSelect} />
          </div>

          {/* Right sidebar */}
          <div className="space-y-6">
            {/* Form or status */}
            {showForm ? (
              <TunnelForm
                hostId={selectedHostId}
                onSuccess={handleFormSuccess}
                onCancel={() => setShowForm(false)}
              />
            ) : selectedTunnel ? (
              <TunnelStatusComponent tunnel={selectedTunnel} autoRefresh={5} />
            ) : (
              <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
                Select a tunnel to view its status
              </div>
            )}
          </div>
        </div>

        {/* Info box */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
          <div className="font-semibold mb-2">SSH Tunnels</div>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>Local forwarding: Access remote services through local port</li>
            <li>Remote forwarding: Expose local services to remote network</li>
            <li>Auto-reconnect: Tunnels automatically reconnect on disconnect</li>
            <li>Real-time monitoring: View tunnel status and connection details</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
