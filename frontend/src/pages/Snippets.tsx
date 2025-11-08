/**
 * Snippets page for managing SSH command snippets.
 */

import React, { useState, useEffect } from 'react';
import { useSnippets, Snippet } from '../hooks/useSnippets';
import { SnippetLibrary } from '../components/snippets/SnippetLibrary';
import { SnippetForm, SnippetFormData } from '../components/snippets/SnippetForm';
import { SnippetExecutor, TerminalSession } from '../components/snippets/SnippetExecutor';

type PageMode = 'library' | 'create' | 'edit' | 'execute';

export const SnippetsPage: React.FC = () => {
  const {
    snippets,
    isLoading,
    error,
    listSnippets,
    createSnippet,
    updateSnippet,
    deleteSnippet,
    executeSnippet,
    broadcastSnippet,
    clearError,
  } = useSnippets();

  const [mode, setMode] = useState<PageMode>('library');
  const [selectedSnippet, setSelectedSnippet] = useState<Snippet | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeSessions, setActiveSessions] = useState<TerminalSession[]>([]);

  // Load snippets on mount
  useEffect(() => {
    listSnippets();
  }, []);

  // Load terminal sessions from localStorage (would be from context in real app)
  useEffect(() => {
    const loadSessions = () => {
      try {
        const stored = localStorage.getItem('terminal_sessions');
        if (stored) {
          setActiveSessions(JSON.parse(stored));
        }
      } catch (err) {
        console.error('Failed to load terminal sessions:', err);
      }
    };

    loadSessions();
    // Poll for session updates
    const interval = setInterval(loadSessions, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleCreateSnippet = async (data: SnippetFormData) => {
    setFormLoading(true);
    setFormError(null);
    try {
      await createSnippet(data);
      setSuccessMessage('Snippet created successfully');
      setMode('library');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create snippet');
    } finally {
      setFormLoading(false);
    }
  };

  const handleUpdateSnippet = async (data: SnippetFormData) => {
    if (!selectedSnippet) return;

    setFormLoading(true);
    setFormError(null);
    try {
      await updateSnippet(selectedSnippet.id, data);
      setSuccessMessage('Snippet updated successfully');
      setMode('library');
      setSelectedSnippet(null);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update snippet');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteSnippet = async (snippetId: string) => {
    if (!window.confirm('Are you sure you want to delete this snippet?')) {
      return;
    }
    try {
      await deleteSnippet(snippetId);
      setSuccessMessage('Snippet deleted successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to delete snippet');
    }
  };

  const handleExecuteSnippet = async (sessionId: string, targetHostId?: string) => {
    if (!selectedSnippet) return;

    setFormLoading(true);
    setFormError(null);
    try {
      await executeSnippet(selectedSnippet.id, {
        session_id: sessionId,
        target_host_id: targetHostId,
      });
      setSuccessMessage('Snippet execution started');
      setMode('library');
      setSelectedSnippet(null);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to execute snippet');
    } finally {
      setFormLoading(false);
    }
  };

  const handleBroadcastSnippet = async (sessionIds: string[], targetHostId?: string) => {
    if (!selectedSnippet) return;

    setFormLoading(true);
    setFormError(null);
    try {
      await broadcastSnippet(selectedSnippet.id, {
        session_ids: sessionIds,
        target_host_id: targetHostId,
      });
      setSuccessMessage(
        `Snippet broadcasted to ${sessionIds.length} session(s)`
      );
      setMode('library');
      setSelectedSnippet(null);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to broadcast snippet');
    } finally {
      setFormLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">SSH Command Snippets</h1>
          <p className="text-gray-600">Create, manage, and execute frequently used SSH commands</p>
        </div>

        {/* Success message */}
        {successMessage && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
            {successMessage}
          </div>
        )}

        {/* Page mode: Library */}
        {mode === 'library' && (
          <div className="space-y-6">
            {/* Create button */}
            <div className="flex justify-end">
              <button
                onClick={() => {
                  setMode('create');
                  setSelectedSnippet(null);
                  setFormError(null);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                + Create Snippet
              </button>
            </div>

            {/* Snippet Library with actions */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <SnippetLibrary
                  onSelectSnippet={(snippet) => {
                    setSelectedSnippet(snippet);
                    setMode('edit');
                    setFormError(null);
                  }}
                  onExecute={(snippet) => {
                    setSelectedSnippet(snippet);
                    setMode('execute');
                    setFormError(null);
                  }}
                />
              </div>

              {/* Quick actions sidebar */}
              <div className="space-y-4">
                <div className="bg-white rounded-lg shadow p-4">
                  <h3 className="font-semibold text-gray-900 mb-4">Quick Stats</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Total Snippets:</span>
                      <span className="font-semibold text-gray-900">
                        {snippets.length}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Active Sessions:</span>
                      <span className="font-semibold text-gray-900">
                        {activeSessions.length}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Tips */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-semibold text-blue-900 mb-2 text-sm">Tips</h4>
                  <ul className="text-xs text-blue-800 space-y-1">
                    <li>• Use tags to organize snippets</li>
                    <li>• Make public snippets shareable</li>
                    <li>• Execute directly to terminal</li>
                    <li>• Broadcast to multiple hosts</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Page mode: Create */}
        {mode === 'create' && (
          <SnippetForm
            onSubmit={handleCreateSnippet}
            onCancel={() => {
              setMode('library');
              setFormError(null);
            }}
            isLoading={formLoading}
            error={formError}
          />
        )}

        {/* Page mode: Edit */}
        {mode === 'edit' && selectedSnippet && (
          <SnippetForm
            snippet={selectedSnippet}
            onSubmit={handleUpdateSnippet}
            onCancel={() => {
              setMode('library');
              setSelectedSnippet(null);
              setFormError(null);
            }}
            isLoading={formLoading}
            error={formError}
          />
        )}

        {/* Page mode: Execute */}
        {mode === 'execute' && selectedSnippet && (
          <SnippetExecutor
            snippet={selectedSnippet}
            sessions={activeSessions}
            onExecute={handleExecuteSnippet}
            onBroadcast={handleBroadcastSnippet}
            onCancel={() => {
              setMode('library');
              setSelectedSnippet(null);
              setFormError(null);
            }}
            isLoading={formLoading}
            error={formError}
          />
        )}
      </div>
    </div>
  );
};
