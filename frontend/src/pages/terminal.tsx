/**
 * Terminal Page - SSH terminal interface
 */

import React, { useState } from 'react';
import useTerminal from '@/hooks/useTerminal';
import XTerminal from '@/components/terminal/XTerminal';

export default function TerminalPage() {
  const {
    sessions,
    activeSessionId,
    isLoading,
    error,
    createSession,
    deleteSession,
    setActiveSession,
    sendInput,
    resizeTerminal,
    terminalOutput,
    clearOutput,
    clearError,
  } = useTerminal();

  const [selectedHostId, setSelectedHostId] = useState('');

  const handleCreateSession = async () => {
    if (!selectedHostId) {
      alert('Please select a host');
      return;
    }

    try {
      await createSession(selectedHostId);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">SSH Terminal</h1>
          <p className="text-gray-600 mt-2">Interactive SSH shell access</p>
        </div>

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

        {/* Session Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Terminal Sessions</h2>

          <div className="flex gap-4 mb-6">
            <input
              type="text"
              placeholder="Enter host ID or select from list"
              value={selectedHostId}
              onChange={e => setSelectedHostId(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleCreateSession}
              disabled={isLoading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Creating...' : 'New Session'}
            </button>
            <button
              onClick={clearOutput}
              className="bg-gray-300 text-gray-800 px-6 py-2 rounded-lg font-medium hover:bg-gray-400"
            >
              Clear
            </button>
          </div>

          {/* Active Sessions List */}
          {sessions.length > 0 && (
            <div className="mb-6">
              <p className="text-sm font-medium text-gray-700 mb-2">Active Sessions</p>
              <div className="flex flex-wrap gap-2">
                {sessions.map(session => (
                  <div
                    key={session.session_id}
                    className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
                      activeSessionId === session.session_id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 cursor-pointer hover:bg-gray-200'
                    }`}
                  >
                    <button
                      onClick={() => setActiveSession(session.session_id)}
                      className="flex-1"
                    >
                      {session.host_id}
                    </button>
                    <button
                      onClick={() => deleteSession(session.session_id)}
                      className="text-sm opacity-75 hover:opacity-100"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Terminal Area */}
        {activeSessionId ? (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">
              Terminal: {activeSessionId}
            </h3>
            <div className="h-96">
              <XTerminal
                sessionId={activeSessionId}
                onInput={sendInput}
                onResize={resizeTerminal}
                output={terminalOutput}
              />
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <p className="text-gray-500 text-lg">
              Create or select a session to start
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
