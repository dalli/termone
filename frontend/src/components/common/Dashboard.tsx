/**
 * Dashboard Component - Overview of SSH infrastructure
 */

import React, { useEffect, useState } from 'react';
import useAuth from '@/hooks/useAuth';
import useHosts, { Host } from '@/hooks/useHosts';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const { hosts, listHosts, total } = useHosts();
  const [recentHosts, setRecentHosts] = useState<Host[]>([]);
  const [stats, setStats] = useState({
    totalHosts: 0,
    activeHosts: 0,
    inactiveHosts: 0,
    totalTags: 0,
  });

  useEffect(() => {
    const loadData = async () => {
      await listHosts(0, 100);
    };

    loadData();
  }, [listHosts]);

  // Calculate stats and recent hosts
  useEffect(() => {
    if (hosts.length > 0) {
      const activeCount = hosts.filter(h => h.is_active).length;
      const inactiveCount = hosts.filter(h => !h.is_active).length;
      const allTags = new Set<string>();
      hosts.forEach(h => h.tags.forEach(tag => allTags.add(tag)));

      setStats({
        totalHosts: total,
        activeHosts: activeCount,
        inactiveHosts: inactiveCount,
        totalTags: allTags.size,
      });

      // Get 5 most recently updated hosts
      const recent = [...hosts]
        .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
        .slice(0, 5);

      setRecentHosts(recent);
    }
  }, [hosts, total]);

  const StatCard: React.FC<{
    title: string;
    value: number | string;
    icon: string;
    color: string;
  }> = ({ title, value, icon, color }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-gray-600 text-sm font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <span className={`text-2xl ${color}`}>{icon}</span>
      </div>
    </div>
  );

  return (
    <div className="w-full">
      {/* Welcome section */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.username}!
        </h1>
        <p className="text-gray-600 mt-2">
          Here's an overview of your SSH infrastructure
        </p>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Hosts"
          value={stats.totalHosts}
          icon="🖥️"
          color="text-blue-600"
        />
        <StatCard
          title="Active Hosts"
          value={stats.activeHosts}
          icon="✅"
          color="text-green-600"
        />
        <StatCard
          title="Inactive Hosts"
          value={stats.inactiveHosts}
          icon="⏸️"
          color="text-yellow-600"
        />
        <StatCard
          title="Tags in Use"
          value={stats.totalTags}
          icon="🏷️"
          color="text-purple-600"
        />
      </div>

      {/* Recent Hosts Section */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Recently Updated Hosts</h2>
        </div>

        {recentHosts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                    Hostname
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                    Port
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">
                    Last Updated
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {recentHosts.map(host => (
                  <tr key={host.host_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{host.hostname}</div>
                      {host.folder && (
                        <div className="text-sm text-gray-500">{host.folder}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 text-gray-700">{host.username}</td>
                    <td className="px-6 py-4 text-gray-700">{host.port}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
                          host.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {host.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(host.updated_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-12 text-center">
            <p className="text-gray-600">No hosts yet. Register your first SSH host to get started!</p>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-bold text-blue-900 mb-3">🚀 Quick Start</h3>
        <ul className="space-y-2 text-blue-900 text-sm">
          <li>• Register your first SSH host</li>
          <li>• Connect to a host using the terminal</li>
          <li>• Organize hosts with folders and tags</li>
          <li>• Deploy SSH public keys for passwordless access</li>
          <li>• Monitor host status and activity logs</li>
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;
