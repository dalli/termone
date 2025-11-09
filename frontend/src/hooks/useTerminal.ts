/**
 * useTerminal hook for managing terminal sessions and WebSocket connections
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import api from '@/services/api';
import useWebSocket from './useWebSocket';

export interface TerminalSession {
  session_id: string;
  host_id: string;
  user_id: string;
  state: string;
  rows: number;
  cols: number;
  created_at: string;
  last_activity: string;
  connected: boolean;
}

interface UseTerminalReturn {
  sessions: TerminalSession[];
  activeSessionId: string | null;
  isLoading: boolean;
  error: string | null;

  // Session management
  createSession: (hostId: string, rows?: number, cols?: number) => Promise<TerminalSession>;
  listSessions: () => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  setActiveSession: (sessionId: string) => void;

  // Terminal operations
  sendInput: (data: string) => void;
  resizeTerminal: (rows: number, cols: number) => Promise<void>;
  reconnectSession: (sessionId: string) => Promise<void>;

  // WebSocket state
  isConnected: boolean;
  isConnecting: boolean;
  terminalOutput: string;
  clearOutput: () => void;

  // Error handling
  clearError: () => void;
}

/**
 * Hook for managing terminal sessions
 */
export function useTerminal(autoConnect = true): UseTerminalReturn {
  const [sessions, setSessions] = useState<TerminalSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [terminalOutput, setTerminalOutput] = useState('');
  const outputBufferRef = useRef('');

  // WebSocket connection for active session
  const wsUrl = activeSessionId
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/terminal/ws/${activeSessionId}`
    : '';

  const { isConnected, isConnecting, send } = useWebSocket({
    url: wsUrl,
    onMessage: (data) => {
      if (data.type === 'output') {
        outputBufferRef.current += data.data;
        setTerminalOutput(outputBufferRef.current);
      } else if (data.type === 'error') {
        setError(data.message);
      }
    },
    onError: (event) => {
      setError('WebSocket connection error');
    },
    autoConnect: autoConnect && !!activeSessionId,
  });

  const createSession = useCallback(
    async (hostId: string, rows = 24, cols = 80): Promise<TerminalSession> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.post<TerminalSession>(`/terminal/sessions/${hostId}`, {
          rows,
          cols,
        });

        const newSession = response.data;
        setSessions(prev => [newSession, ...prev]);
        setActiveSessionId(newSession.session_id);
        setTerminalOutput('');
        outputBufferRef.current = '';

        return newSession;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to create session';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const listSessions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get<{ items: TerminalSession[]; total: number }>(
        '/terminal/sessions'
      );
      setSessions(response.data.items);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to list sessions';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteSession = useCallback(
    async (sessionId: string) => {
      setIsLoading(true);
      setError(null);

      try {
        await api.delete(`/terminal/sessions/${sessionId}`);

        setSessions(prev => prev.filter(s => s.session_id !== sessionId));
        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          setTerminalOutput('');
          outputBufferRef.current = '';
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to delete session';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [activeSessionId]
  );

  const sendInput = useCallback(
    (data: string) => {
      if (!isConnected) {
        setError('Not connected to terminal');
        return;
      }

      send({
        type: 'input',
        data,
      });
    },
    [isConnected, send]
  );

  const resizeTerminal = useCallback(
    async (rows: number, cols: number) => {
      if (!activeSessionId) {
        return;
      }

      try {
        await api.post(`/terminal/sessions/${activeSessionId}/resize`, {
          rows,
          cols,
        });

        // Also send via WebSocket
        send({
          type: 'resize',
          rows,
          cols,
        });
      } catch (err) {
        console.error('Failed to resize terminal:', err);
      }
    },
    [activeSessionId, send]
  );

  const reconnectSession = useCallback(
    async (sessionId: string) => {
      setActiveSessionId(sessionId);
      setTerminalOutput('');
      outputBufferRef.current = '';
    },
    []
  );

  const clearOutput = useCallback(() => {
    setTerminalOutput('');
    outputBufferRef.current = '';
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load sessions on mount
  useEffect(() => {
    listSessions();
  }, [listSessions]);

  return {
    sessions,
    activeSessionId,
    isLoading,
    error,
    createSession,
    listSessions,
    deleteSession,
    setActiveSession: setActiveSessionId,
    sendInput,
    resizeTerminal,
    reconnectSession,
    isConnected,
    isConnecting,
    terminalOutput,
    clearOutput,
    clearError,
  };
}

export default useTerminal;
