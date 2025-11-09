/**
 * SessionManager component for admin panel.
 */

import React, { useEffect } from 'react';
import { Session } from '../../hooks/useAdmin';

interface SessionManagerProps {
  sessions: Session[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => Promise<void>;
  onDeleteSession: (sessionId: string) => Promise<void>;
}

export const SessionManager: React.FC<SessionManagerProps> = ({
  sessions,
  isLoading,
  error,
  onRefresh,
  onDeleteSession,
}) => {
  useEffect(() => {
    onRefresh();
  }, []);

  const handleDeleteSession = async (sessionId: string) => {
    if (window.confirm('Are you sure you want to terminate this session?')) {
      await onDeleteSession(sessionId);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Active Sessions</h2>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-8">
          <div className="animate-spin inline-block">⟳</div>
          <p className="mt-2 text-gray-600">Loading sessions...</p>
        </div>
      ) : sessions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No active sessions
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 rounded p-4">
              <div className="text-3xl font-bold text-blue-600">
                {sessions.length}
              </div>
              <div className="text-sm text-gray-600 mt-1">Total Sessions</div>
            </div>
            <div className="bg-green-50 rounded p-4">
              <div className="text-3xl font-bold text-green-600">
                {sessions.filter((s) => s.status === 'active').length}
              </div>
              <div className="text-sm text-gray-600 mt-1">Active</div>
            </div>
            <div className="bg-gray-50 rounded p-4">
              <div className="text-3xl font-bold text-gray-600">
                {new Set(sessions.map((s) => s.user_id)).size}
              </div>
              <div className="text-sm text-gray-600 mt-1">Unique Users</div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Session ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Host
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Last Activity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sessions.map((session) => (
                  <tr key={session.session_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-600">
                      {session.session_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {session.user_email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="inline-flex px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                        {session.session_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {session.host_name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {new Date(session.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {new Date(session.last_activity).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <button
                        onClick={() => handleDeleteSession(session.session_id)}
                        className="text-red-600 hover:text-red-900 font-medium"
                      >
                        Terminate
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};
