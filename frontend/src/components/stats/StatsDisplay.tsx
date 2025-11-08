/**
 * StatsDisplay Component - Display system statistics
 */

import React from 'react';
import { formatBytes, formatPercent, formatUptime, getStatusColor, getStatusLabel } from '@/utils/charts';

interface StatsDisplayProps {
  stats: any | null;
  isLoading?: boolean;
}

export const CPUChart: React.FC<StatsDisplayProps> = ({ stats, isLoading }) => {
  if (isLoading || !stats?.cpu) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">CPU Usage</h3>
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  const cpu = stats.cpu;
  const color = getStatusColor(cpu.usage_percent);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">CPU Usage</h3>
      <div className="space-y-4">
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-gray-600">Usage</span>
            <span className="font-semibold">{formatPercent(cpu.usage_percent)}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="h-4 rounded-full transition-all"
              style={{
                width: `${Math.min(100, cpu.usage_percent)}%`,
                backgroundColor: color,
              }}
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 text-sm">
          <div>
            <p className="text-gray-600">1m Load</p>
            <p className="font-semibold">{cpu.load_1.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-gray-600">5m Load</p>
            <p className="font-semibold">{cpu.load_5.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-gray-600">15m Load</p>
            <p className="font-semibold">{cpu.load_15.toFixed(2)}</p>
          </div>
        </div>

        <div className="text-sm">
          <span className="text-gray-600">Cores: </span>
          <span className="font-semibold">{cpu.cores}</span>
        </div>
      </div>
    </div>
  );
};

export const MemoryChart: React.FC<StatsDisplayProps> = ({ stats, isLoading }) => {
  if (isLoading || !stats?.memory) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Memory Usage</h3>
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  const memory = stats.memory;
  const color = getStatusColor(memory.percent);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Memory Usage</h3>
      <div className="space-y-4">
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-gray-600">Usage</span>
            <span className="font-semibold">{formatPercent(memory.percent)}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="h-4 rounded-full transition-all"
              style={{
                width: `${Math.min(100, memory.percent)}%`,
                backgroundColor: color,
              }}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <p className="text-gray-600">Used</p>
            <p className="font-semibold">{formatBytes(memory.used)}</p>
          </div>
          <div>
            <p className="text-gray-600">Total</p>
            <p className="font-semibold">{formatBytes(memory.total)}</p>
          </div>
          <div>
            <p className="text-gray-600">Free</p>
            <p className="font-semibold">{formatBytes(memory.free)}</p>
          </div>
          <div>
            <p className="text-gray-600">Available</p>
            <p className="font-semibold">{formatBytes(memory.available)}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export const DiskChart: React.FC<StatsDisplayProps> = ({ stats, isLoading }) => {
  if (isLoading || !stats?.disk || stats.disk.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Disk Usage</h3>
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  const disks = stats.disk;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Disk Usage</h3>
      <div className="space-y-4">
        {disks.map((disk: any, idx: number) => {
          const color = getStatusColor(disk.percent);
          return (
            <div key={idx}>
              <div className="flex justify-between mb-1 text-sm">
                <span className="text-gray-600 font-medium">{disk.mount}</span>
                <span className="font-semibold">{formatPercent(disk.percent)}</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="h-3 rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, disk.percent)}%`,
                    backgroundColor: color,
                  }}
                />
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {formatBytes(disk.used)} / {formatBytes(disk.total)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const NetworkChart: React.FC<StatsDisplayProps> = ({ stats, isLoading }) => {
  if (isLoading || !stats?.network || stats.network.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Network</h3>
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  const networks = stats.network;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Network</h3>
      <div className="space-y-4">
        {networks.map((net: any, idx: number) => (
          <div key={idx} className="border-b pb-4 last:border-b-0">
            <p className="font-semibold text-sm mb-2">{net.interface}</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <p className="text-gray-600">Sent</p>
                <p className="font-semibold">{formatBytes(net.bytes_sent)}</p>
              </div>
              <div>
                <p className="text-gray-600">Received</p>
                <p className="font-semibold">{formatBytes(net.bytes_recv)}</p>
              </div>
              <div>
                <p className="text-gray-600">Packets Sent</p>
                <p className="font-semibold">{net.packets_sent}</p>
              </div>
              <div>
                <p className="text-gray-600">Packets Recv</p>
                <p className="font-semibold">{net.packets_recv}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const SystemInfo: React.FC<StatsDisplayProps> = ({ stats, isLoading }) => {
  if (isLoading || !stats?.system) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">System Information</h3>
        <p className="text-gray-400">Loading...</p>
      </div>
    );
  }

  const system = stats.system;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">System Information</h3>
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Hostname</span>
          <span className="font-semibold">{system.hostname}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">OS</span>
          <span className="font-semibold">{system.os}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Kernel</span>
          <span className="font-semibold">{system.kernel}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Uptime</span>
          <span className="font-semibold">{formatUptime(system.uptime_seconds)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Boot Time</span>
          <span className="font-semibold text-xs">
            {new Date(system.boot_time).toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
};
