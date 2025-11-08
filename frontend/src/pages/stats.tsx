/**
 * Stats Page - Server monitoring and statistics
 */

import React, { useState } from 'react';
import useStats from '@/hooks/useStats';
import {
  CPUChart,
  MemoryChart,
  DiskChart,
  NetworkChart,
  SystemInfo,
} from '@/components/stats/StatsDisplay';

interface StatsPageProps {
  hostId?: string;
}

export default function StatsPage({ hostId: initialHostId }: StatsPageProps) {
  const [selectedHostId, setSelectedHostId] = useState(initialHostId || '');
  const {
    stats,
    isLoading,
    isConnected,
    error,
    loadCurrentStats,
    startCollection,
    stopCollection,
    clearError,
  } = useStats(selectedHostId);

  const handleHostSelect = async (id: string) => {
    if (selectedHostId) {
      await stopCollection(selectedHostId);
    }
    setSelectedHostId(id);
    await loadCurrentStats(id);
    await startCollection(id);
  };

  const handleRefresh = async () => {
    if (selectedHostId) {
      await loadCurrentStats(selectedHostId);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Server Monitoring</h1>
          <p className="text-gray-600 mt-2">Real-time system statistics and performance metrics</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex justify-between items-center">
              <p className="text-red-800">{error}</p>
              <button
                onClick={clearError}
                className="text-red-600 hover:text-red-800 font-semibold"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Host Selection */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Select Host</h2>

          <div className="flex gap-4">
            <input
              type="text"
              placeholder="Enter host ID or select from list"
              value={selectedHostId}
              onChange={e => setSelectedHostId(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={() => handleHostSelect(selectedHostId)}
              disabled={!selectedHostId || isLoading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Loading...' : 'Connect'}
            </button>
            <button
              onClick={handleRefresh}
              disabled={!selectedHostId || isLoading}
              className="bg-gray-300 text-gray-800 px-6 py-2 rounded-lg font-medium hover:bg-gray-400 disabled:opacity-50"
            >
              Refresh
            </button>
          </div>

          {/* Connection Status */}
          {selectedHostId && (
            <div className="mt-4 flex items-center gap-2">
              <div
                className={`w-3 h-3 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-sm">
                {isConnected ? 'Connected (Live)' : 'Disconnected (Manual refresh)'}
              </span>
            </div>
          )}
        </div>

        {/* Stats Display */}
        {selectedHostId && stats ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {/* CPU */}
            <CPUChart stats={stats} isLoading={isLoading} />

            {/* Memory */}
            <MemoryChart stats={stats} isLoading={isLoading} />

            {/* Disk */}
            <DiskChart stats={stats} isLoading={isLoading} />

            {/* Network */}
            <NetworkChart stats={stats} isLoading={isLoading} />

            {/* System Info */}
            <SystemInfo stats={stats} isLoading={isLoading} />
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-12 text-center mb-8">
            <p className="text-gray-500 text-lg">
              Select a host to view statistics
            </p>
          </div>
        )}

        {/* Last Update */}
        {stats && (
          <div className="text-center text-sm text-gray-500">
            <p>
              Last updated:{' '}
              {new Date(stats.timestamp).toLocaleTimeString()}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
