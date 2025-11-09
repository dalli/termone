/**
 * HostList Component - Displays a paginated list of SSH hosts
 */

import React, { useEffect, useState } from 'react';
import useHosts, { Host } from '@/hooks/useHosts';

interface HostListProps {
  onHostSelect?: (host: Host) => void;
  onHostDelete?: (hostId: string) => void;
  onHostEdit?: (host: Host) => void;
  filters?: {
    tags?: string[];
    folder?: string;
    is_active?: boolean;
  };
}

export const HostList: React.FC<HostListProps> = ({
  onHostSelect,
  onHostDelete,
  onHostEdit,
  filters,
}) => {
  const { hosts, isLoading, error, total, listHosts, deleteHost, clearError } = useHosts();
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(20);

  // Load hosts on mount and when filters change
  useEffect(() => {
    const loadHosts = async () => {
      await listHosts(currentPage * pageSize, pageSize, filters);
    };

    loadHosts();
  }, [currentPage, pageSize, filters, listHosts]);

  const handleDeleteHost = async (hostId: string) => {
    if (window.confirm('Are you sure you want to delete this host?')) {
      try {
        await deleteHost(hostId);
        if (onHostDelete) {
          onHostDelete(hostId);
        }
      } catch (err) {
        console.error('Failed to delete host:', err);
      }
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="w-full">
      {/* Error message */}
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

      {/* Loading state */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-block">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
          <p className="mt-2 text-gray-600">Loading hosts...</p>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && hosts.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No hosts found</p>
          <p className="text-gray-400 text-sm">Try adjusting your filters or create a new host</p>
        </div>
      )}

      {/* Hosts table */}
      {!isLoading && hosts.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100 border-b">
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-800">
                  Hostname
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-800">
                  Port
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-800">
                  Username
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-800">
                  Tags
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-800">
                  Status
                </th>
                <th className="px-4 py-3 text-center text-sm font-semibold text-gray-800">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {hosts.map((host) => (
                <tr
                  key={host.host_id}
                  className="border-b hover:bg-gray-50 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="font-semibold text-gray-900">{host.hostname}</div>
                    {host.folder && <div className="text-xs text-gray-500">{host.folder}</div>}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{host.port}</td>
                  <td className="px-4 py-3 text-gray-700">{host.username}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {host.tags.slice(0, 2).map((tag) => (
                        <span
                          key={tag}
                          className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {host.tags.length > 2 && (
                        <span className="text-xs text-gray-500">
                          +{host.tags.length - 2} more
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                        host.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {host.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => onHostSelect && onHostSelect(host)}
                      className="text-blue-600 hover:text-blue-800 mr-3 text-sm font-medium"
                      title="View/Connect"
                    >
                      Connect
                    </button>
                    <button
                      onClick={() => onHostEdit && onHostEdit(host)}
                      className="text-gray-600 hover:text-gray-800 mr-3 text-sm font-medium"
                      title="Edit"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteHost(host.host_id)}
                      className="text-red-600 hover:text-red-800 text-sm font-medium"
                      title="Delete"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {!isLoading && hosts.length > 0 && totalPages > 1 && (
        <div className="mt-6 flex justify-center items-center gap-2">
          <button
            onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
            disabled={currentPage === 0}
            className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
          >
            Previous
          </button>

          <div className="flex gap-1">
            {Array.from({ length: totalPages }).map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentPage(index)}
                className={`px-3 py-1 border rounded ${
                  currentPage === index
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'hover:bg-gray-100'
                }`}
              >
                {index + 1}
              </button>
            ))}
          </div>

          <button
            onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
            disabled={currentPage === totalPages - 1}
            className="px-3 py-1 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
          >
            Next
          </button>

          <span className="ml-4 text-sm text-gray-600">
            Showing {currentPage * pageSize + 1}-
            {Math.min((currentPage + 1) * pageSize, total)} of {total}
          </span>
        </div>
      )}
    </div>
  );
};

export default HostList;
