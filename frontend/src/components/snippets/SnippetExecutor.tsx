/**
 * SnippetExecutor component for executing command snippets in terminal sessions.
 */

import React, { useState, useEffect } from 'react';
import { Snippet } from '../../hooks/useSnippets';

export interface TerminalSession {
  id: string;
  host_id: string;
  host_name: string;
  created_at: string;
  status: 'active' | 'inactive';
}

interface SnippetExecutorProps {
  snippet: Snippet;
  sessions: TerminalSession[];
  onExecute: (sessionId: string, targetHostId?: string) => Promise<void>;
  onBroadcast: (sessionIds: string[], targetHostId?: string) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string;
}

interface ExecutionResult {
  status: 'pending' | 'success' | 'error';
  message?: string;
  executionId?: string;
}

export const SnippetExecutor: React.FC<SnippetExecutorProps> = ({
  snippet,
  sessions,
  onExecute,
  onBroadcast,
  onCancel,
  isLoading = false,
  error,
}) => {
  const [selectedSessions, setSelectedSessions] = useState<string[]>([]);
  const [executionMode, setExecutionMode] = useState<'single' | 'broadcast'>('single');
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Group sessions by host for display
  const sessionsByHost = sessions.reduce(
    (acc, session) => {
      if (!acc[session.host_name]) {
        acc[session.host_name] = [];
      }
      acc[session.host_name].push(session);
      return acc;
    },
    {} as Record<string, TerminalSession[]>
  );

  const handleSessionToggle = (sessionId: string) => {
    setSelectedSessions((prev) =>
      prev.includes(sessionId)
        ? prev.filter((id) => id !== sessionId)
        : [...prev, sessionId]
    );
  };

  const handleSelectAllForHost = (hostName: string) => {
    const hostSessions = sessionsByHost[hostName];
    const allSelected = hostSessions.every((s) => selectedSessions.includes(s.id));

    if (allSelected) {
      setSelectedSessions(
        selectedSessions.filter(
          (id) => !hostSessions.find((s) => s.id === id)
        )
      );
    } else {
      setSelectedSessions([
        ...selectedSessions,
        ...hostSessions.filter((s) => !selectedSessions.includes(s.id)),
      ]);
    }
  };

  const handleExecute = async () => {
    setFormError(null);
    setExecutionResult(null);

    if (executionMode === 'single' && selectedSessions.length !== 1) {
      setFormError('Please select exactly one session');
      return;
    }

    if (executionMode === 'broadcast' && selectedSessions.length === 0) {
      setFormError('Please select at least one session');
      return;
    }

    try {
      setExecutionResult({ status: 'pending', message: 'Executing snippet...' });

      if (executionMode === 'single') {
        const targetSession = sessions.find((s) => s.id === selectedSessions[0]);
        await onExecute(selectedSessions[0], targetSession?.host_id);
      } else {
        // Get the host_id from the first selected session
        const firstSession = sessions.find((s) => s.id === selectedSessions[0]);
        await onBroadcast(selectedSessions, firstSession?.host_id);
      }

      setExecutionResult({
        status: 'success',
        message:
          executionMode === 'single'
            ? 'Snippet executed successfully'
            : `Snippet broadcasted to ${selectedSessions.length} session(s)`,
      });
    } catch (err) {
      setExecutionResult({
        status: 'error',
        message: err instanceof Error ? err.message : 'Execution failed',
      });
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <h2 className="text-xl font-semibold mb-2">Execute Snippet</h2>
      <p className="text-gray-600 text-sm mb-6">
        <code className="bg-gray-100 px-2 py-1 rounded">{snippet.name}</code>
      </p>

      {/* Execution mode selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Execution Mode
        </label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              checked={executionMode === 'single'}
              onChange={() => {
                setExecutionMode('single');
                setSelectedSessions(selectedSessions.slice(0, 1));
              }}
              disabled={isLoading}
              className="w-4 h-4"
            />
            <span className="text-sm">Single Session</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              checked={executionMode === 'broadcast'}
              onChange={() => setExecutionMode('broadcast')}
              disabled={isLoading}
              className="w-4 h-4"
            />
            <span className="text-sm">Broadcast to Multiple</span>
          </label>
        </div>
      </div>

      {/* Session selection */}
      {sessions.length === 0 ? (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded text-blue-700 text-sm">
          No active terminal sessions available. Please open a terminal session first.
        </div>
      ) : (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select {executionMode === 'single' ? 'Session' : 'Sessions'}
            {executionMode === 'broadcast' && selectedSessions.length > 0 && (
              <span className="ml-2 text-xs text-gray-500">
                ({selectedSessions.length} selected)
              </span>
            )}
          </label>
          <div className="space-y-4 max-h-48 overflow-y-auto border border-gray-200 rounded p-3">
            {Object.entries(sessionsByHost).map(([hostName, hostSessions]) => {
              const allHostSessionsSelected = hostSessions.every((s) =>
                selectedSessions.includes(s.id)
              );
              const someHostSessionsSelected = hostSessions.some((s) =>
                selectedSessions.includes(s.id)
              );

              return (
                <div key={hostName} className="space-y-2">
                  {/* Host header */}
                  <label className="flex items-center gap-2 font-medium text-gray-700">
                    <input
                      type="checkbox"
                      checked={allHostSessionsSelected}
                      onChange={() => handleSelectAllForHost(hostName)}
                      disabled={isLoading || executionMode === 'single'}
                      className="w-4 h-4 rounded"
                      indeterminate={
                        someHostSessionsSelected && !allHostSessionsSelected
                      }
                    />
                    <span className="text-sm font-semibold">{hostName}</span>
                  </label>

                  {/* Sessions for this host */}
                  <div className="ml-6 space-y-1">
                    {hostSessions.map((session) => (
                      <label
                        key={session.id}
                        className="flex items-center gap-2 text-sm"
                      >
                        <input
                          type={executionMode === 'single' ? 'radio' : 'checkbox'}
                          checked={selectedSessions.includes(session.id)}
                          onChange={() => handleSessionToggle(session.id)}
                          disabled={
                            isLoading ||
                            (executionMode === 'single' &&
                              selectedSessions.length === 1 &&
                              !selectedSessions.includes(session.id))
                          }
                          name={
                            executionMode === 'single' ? 'single-session' : undefined
                          }
                          className="w-4 h-4 rounded"
                        />
                        <span className="text-gray-600">
                          {session.id}
                          {session.status === 'active' && (
                            <span className="ml-2 text-xs text-green-600 font-medium">
                              ● Active
                            </span>
                          )}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Error and result messages */}
      {(formError || error) && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {formError || error}
        </div>
      )}

      {executionResult && (
        <div
          className={`mb-4 p-3 rounded text-sm ${
            executionResult.status === 'success'
              ? 'bg-green-50 border border-green-200 text-green-700'
              : executionResult.status === 'error'
              ? 'bg-red-50 border border-red-200 text-red-700'
              : 'bg-blue-50 border border-blue-200 text-blue-700'
          }`}
        >
          <div className="flex items-center gap-2">
            {executionResult.status === 'pending' && (
              <span className="animate-spin">⟳</span>
            )}
            {executionResult.status === 'success' && <span>✓</span>}
            {executionResult.status === 'error' && <span>✕</span>}
            <span>{executionResult.message}</span>
          </div>
        </div>
      )}

      {/* Command preview */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Command
        </label>
        <div className="bg-gray-900 text-gray-100 p-3 rounded font-mono text-sm overflow-x-auto">
          {snippet.command}
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleExecute}
          disabled={isLoading || sessions.length === 0}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <span className="animate-spin">⟳</span>
              Executing...
            </>
          ) : (
            `Execute on ${selectedSessions.length > 0 ? selectedSessions.length : 0} Session${selectedSessions.length !== 1 ? 's' : ''}`
          )}
        </button>
      </div>
    </div>
  );
};
