/**
 * useStats hook for managing server statistics
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import api from '@/services/api';
import useWebSocket from './useWebSocket';

export interface StatsSnapshot {
  timestamp: string;
  cpu: {
    usage_percent: number;
    cores: number;
    load_1: number;
    load_5: number;
    load_15: number;
  };
  memory: {
    total: number;
    used: number;
    available: number;
    percent: number;
    free: number;
  };
  disk: Array<{
    mount: string;
    device: string;
    total: number;
    used: number;
    free: number;
    percent: number;
  }>;
  network: Array<{
    interface: string;
    bytes_sent: number;
    bytes_recv: number;
    packets_sent: number;
    packets_recv: number;
  }>;
  system: {
    hostname: string;
    os: string;
    kernel: string;
    uptime_seconds: number;
    boot_time: string;
  };
}

interface UseStatsReturn {
  stats: StatsSnapshot | null;
  isLoading: boolean;
  isConnected: boolean;
  error: string | null;

  // Operations
  loadCurrentStats: (hostId: string) => Promise<void>;
  startCollection: (hostId: string) => Promise<void>;
  stopCollection: (hostId: string) => Promise<void>;

  // History
  statsHistory: StatsSnapshot[];
  addToHistory: (stat: StatsSnapshot) => void;
  clearHistory: () => void;

  // Error handling
  clearError: () => void;
}

/**
 * Hook for managing server statistics
 */
export function useStats(hostId?: string): UseStatsReturn {
  const [stats, setStats] = useState<StatsSnapshot | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statsHistory, setStatsHistory] = useState<StatsSnapshot[]>([]);
  const maxHistoryRef = useRef(100);

  // WebSocket connection for stats stream
  const wsUrl = hostId
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/stats/ws/${hostId}`
    : '';

  const { isConnected, send } = useWebSocket({
    url: wsUrl,
    onMessage: (data) => {
      if (data.type === 'stats' && data.data) {
        setStats(data.data);
        addToHistory(data.data);
      } else if (data.type === 'error') {
        setError(data.error);
      }
    },
    onError: (event) => {
      setError('WebSocket connection error');
    },
    autoConnect: !!hostId,
  });

  const loadCurrentStats = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get<StatsSnapshot>(`/stats/${id}/current`);
      setStats(response.data);
      addToHistory(response.data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load stats';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const startCollection = useCallback(async (id: string) => {
    try {
      await api.post(`/stats/${id}/start-collection`, { interval: 5 });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start collection';
      setError(errorMessage);
    }
  }, []);

  const stopCollection = useCallback(async (id: string) => {
    try {
      await api.post(`/stats/${id}/stop-collection`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to stop collection';
      setError(errorMessage);
    }
  }, []);

  const addToHistory = useCallback((stat: StatsSnapshot) => {
    setStatsHistory(prev => {
      const updated = [stat, ...prev];
      if (updated.length > maxHistoryRef.current) {
        return updated.slice(0, maxHistoryRef.current);
      }
      return updated;
    });
  }, []);

  const clearHistory = useCallback(() => {
    setStatsHistory([]);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Load current stats on mount if hostId is provided
  useEffect(() => {
    if (hostId) {
      loadCurrentStats(hostId);
    }
  }, [hostId, loadCurrentStats]);

  return {
    stats,
    isLoading,
    isConnected,
    error,
    loadCurrentStats,
    startCollection,
    stopCollection,
    statsHistory,
    addToHistory,
    clearHistory,
    clearError,
  };
}

export default useStats;
