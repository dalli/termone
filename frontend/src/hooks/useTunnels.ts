/**
 * useTunnels hook for tunnel management operations.
 *
 * Manages:
 * - Tunnel list and filtering
 * - Tunnel creation, update, deletion
 * - Tunnel status monitoring
 * - Start/stop operations
 */

import React, { useState, useCallback } from 'react';
import api from '../services/api';

export interface Tunnel {
  id: string;
  host_id: string;
  name: string;
  tunnel_type: 'local' | 'remote';
  local_port: number;
  remote_host: string;
  remote_port: number;
  bind_address: string;
  status: 'connecting' | 'connected' | 'disconnected' | 'failed' | 'reconnecting';
  connected: boolean;
  enabled: boolean;
  auto_reconnect: boolean;
  created_at: string;
  updated_at: string;
  error: string | null;
}

export interface TunnelStatus {
  status: string;
  connected: boolean;
  error?: string;
  last_error?: string;
  error_count: number;
  last_connection_time?: string;
  last_disconnection_time?: string;
  uptime_seconds: number;
}

export interface TunnelCreateRequest {
  host_id: string;
  name: string;
  tunnel_type: 'local' | 'remote';
  local_port: number;
  remote_host: string;
  remote_port: number;
  bind_address?: string;
  enabled?: boolean;
  auto_reconnect?: boolean;
}

export interface TunnelUpdateRequest {
  name?: string;
  local_port?: number;
  remote_host?: string;
  remote_port?: number;
  bind_address?: string;
  enabled?: boolean;
  auto_reconnect?: boolean;
}

export interface UseTunnelsReturn {
  // State
  tunnels: Tunnel[];
  isLoading: boolean;
  error: string | null;
  selectedTunnel: Tunnel | null;

  // Operations
  listTunnels: (hostId?: string) => Promise<void>;
  getTunnel: (tunnelId: string) => Promise<Tunnel | null>;
  createTunnel: (request: TunnelCreateRequest) => Promise<Tunnel>;
  updateTunnel: (tunnelId: string, request: TunnelUpdateRequest) => Promise<Tunnel>;
  deleteTunnel: (tunnelId: string) => Promise<void>;
  getTunnelStatus: (tunnelId: string) => Promise<TunnelStatus>;
  startTunnel: (tunnelId: string) => Promise<void>;
  stopTunnel: (tunnelId: string) => Promise<void>;
  selectTunnel: (tunnel: Tunnel | null) => void;
  clearError: () => void;
}

export function useTunnels(hostId?: string): UseTunnelsReturn {
  const [tunnels, setTunnels] = useState<Tunnel[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTunnel, setSelectedTunnel] = useState<Tunnel | null>(null);

  // List tunnels
  const listTunnels = useCallback(
    async (filterHostId?: string) => {
      setIsLoading(true);
      setError(null);
      try {
        const params = filterHostId ? { host_id: filterHostId } : undefined;
        const response = await api.get<Tunnel[]>('/tunnels', { params });
        setTunnels(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to list tunnels');
        setTunnels([]);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Get single tunnel
  const getTunnel = useCallback(
    async (tunnelId: string): Promise<Tunnel | null> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.get<Tunnel>(`/tunnels/${tunnelId}`);
        return response.data;
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to get tunnel');
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Create tunnel
  const createTunnel = useCallback(
    async (request: TunnelCreateRequest): Promise<Tunnel> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.post<Tunnel>('/tunnels', request);
        await listTunnels();
        return response.data;
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Failed to create tunnel';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [listTunnels]
  );

  // Update tunnel
  const updateTunnel = useCallback(
    async (tunnelId: string, request: TunnelUpdateRequest): Promise<Tunnel> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.put<Tunnel>(`/tunnels/${tunnelId}`, request);
        await listTunnels();
        return response.data;
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Failed to update tunnel';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [listTunnels]
  );

  // Delete tunnel
  const deleteTunnel = useCallback(
    async (tunnelId: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await api.delete(`/tunnels/${tunnelId}`);
        await listTunnels();
        if (selectedTunnel?.id === tunnelId) {
          setSelectedTunnel(null);
        }
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Failed to delete tunnel';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [listTunnels, selectedTunnel]
  );

  // Get tunnel status
  const getTunnelStatus = useCallback(
    async (tunnelId: string): Promise<TunnelStatus> => {
      try {
        const response = await api.get<TunnelStatus>(`/tunnels/${tunnelId}/status`);
        return response.data;
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to get tunnel status');
        throw err;
      }
    },
    []
  );

  // Start tunnel
  const startTunnel = useCallback(
    async (tunnelId: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await api.post(`/tunnels/${tunnelId}/start`, {});
        await listTunnels();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to start tunnel');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [listTunnels]
  );

  // Stop tunnel
  const stopTunnel = useCallback(
    async (tunnelId: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await api.post(`/tunnels/${tunnelId}/stop`, {});
        await listTunnels();
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to stop tunnel');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [listTunnels]
  );

  // Select tunnel
  const selectTunnel = useCallback((tunnel: Tunnel | null) => {
    setSelectedTunnel(tunnel);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-load tunnels on hostId change
  React.useEffect(() => {
    if (hostId) {
      listTunnels(hostId);
    }
  }, [hostId, listTunnels]);

  return {
    tunnels,
    isLoading,
    error,
    selectedTunnel,
    listTunnels,
    getTunnel,
    createTunnel,
    updateTunnel,
    deleteTunnel,
    getTunnelStatus,
    startTunnel,
    stopTunnel,
    selectTunnel,
    clearError,
  };
}
