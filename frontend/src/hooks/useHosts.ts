/**
 * useHosts hook for managing SSH hosts
 */

import { useState, useCallback } from 'react';
import api from '@/services/api';

export interface Host {
  host_id: string;
  hostname: string;
  port: number;
  username: string;
  tags: string[];
  folder?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by_user_id: string;
  last_accessed?: string;
  credential_type?: string;
}

export interface HostCreateData {
  hostname: string;
  port: number;
  username: string;
  tags?: string[];
  folder?: string;
  description?: string;
  credential: {
    type: 'password' | 'ssh_key';
    value: string;
  };
}

export interface HostUpdateData {
  hostname?: string;
  port?: number;
  username?: string;
  tags?: string[];
  folder?: string;
  description?: string;
  is_active?: boolean;
  credential?: {
    type: 'password' | 'ssh_key';
    value: string;
  };
}

interface HostListResponse {
  items: Host[];
  total: number;
  skip: number;
  limit: number;
}

interface UseHostsReturn {
  hosts: Host[];
  isLoading: boolean;
  error: string | null;
  total: number;
  currentPage: number;
  pageSize: number;

  // Operations
  listHosts: (skip?: number, limit?: number, filters?: any) => Promise<void>;
  getHost: (hostId: string) => Promise<Host>;
  createHost: (data: HostCreateData) => Promise<Host>;
  updateHost: (hostId: string, data: HostUpdateData) => Promise<Host>;
  deleteHost: (hostId: string) => Promise<void>;
  searchHosts: (query: string, skip?: number, limit?: number) => Promise<void>;
  addTag: (hostId: string, tag: string) => Promise<Host>;
  removeTag: (hostId: string, tag: string) => Promise<Host>;
  deployPublicKey: (hostId: string, publicKey: string) => Promise<void>;

  // State management
  clearError: () => void;
  setHosts: (hosts: Host[]) => void;
}

/**
 * Hook for managing SSH hosts
 */
export function useHosts(): UseHostsReturn {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize, setPageSize] = useState(20);

  const listHosts = useCallback(
    async (skip = 0, limit = 20, filters?: any): Promise<void> => {
      setIsLoading(true);
      setError(null);

      try {
        const params: any = { skip, limit };

        if (filters?.tags) {
          params.tags = Array.isArray(filters.tags)
            ? filters.tags.join(',')
            : filters.tags;
        }
        if (filters?.folder) {
          params.folder = filters.folder;
        }
        if (filters?.is_active !== undefined) {
          params.is_active = filters.is_active;
        }

        const response = await api.get<HostListResponse>('/hosts', { params });

        setHosts(response.data.items);
        setTotal(response.data.total);
        setCurrentPage(Math.floor(skip / limit));
        setPageSize(limit);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch hosts';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const getHost = useCallback(async (hostId: string): Promise<Host> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get<Host>(`/hosts/${hostId}`);
      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch host';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const createHost = useCallback(async (data: HostCreateData): Promise<Host> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<Host>('/hosts', data);

      // Add to local list
      setHosts(prev => [response.data, ...prev]);
      setTotal(prev => prev + 1);

      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create host';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const updateHost = useCallback(
    async (hostId: string, data: HostUpdateData): Promise<Host> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.put<Host>(`/hosts/${hostId}`, data);

        // Update in local list
        setHosts(prev =>
          prev.map(h => (h.host_id === hostId ? response.data : h))
        );

        return response.data;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update host';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const deleteHost = useCallback(async (hostId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await api.delete(`/hosts/${hostId}`);

      // Remove from local list
      setHosts(prev => prev.filter(h => h.host_id !== hostId));
      setTotal(prev => Math.max(0, prev - 1));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete host';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const searchHosts = useCallback(
    async (query: string, skip = 0, limit = 20): Promise<void> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.get<HostListResponse>('/hosts/search', {
          params: { q: query, skip, limit },
        });

        setHosts(response.data.items);
        setTotal(response.data.total);
        setCurrentPage(Math.floor(skip / limit));
        setPageSize(limit);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Search failed';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const addTag = useCallback(async (hostId: string, tag: string): Promise<Host> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<Host>(`/hosts/${hostId}/tags/${tag}`);

      // Update in local list
      setHosts(prev =>
        prev.map(h => (h.host_id === hostId ? response.data : h))
      );

      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add tag';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const removeTag = useCallback(async (hostId: string, tag: string): Promise<Host> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.delete<Host>(`/hosts/${hostId}/tags/${tag}`);

      // Update in local list
      setHosts(prev =>
        prev.map(h => (h.host_id === hostId ? response.data : h))
      );

      return response.data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to remove tag';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deployPublicKey = useCallback(
    async (hostId: string, publicKey: string): Promise<void> => {
      setIsLoading(true);
      setError(null);

      try {
        await api.post(`/hosts/${hostId}/deploy-public-key`, {
          public_key: publicKey,
        });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to deploy key';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  return {
    hosts,
    isLoading,
    error,
    total,
    currentPage,
    pageSize,
    listHosts,
    getHost,
    createHost,
    updateHost,
    deleteHost,
    searchHosts,
    addTag,
    removeTag,
    deployPublicKey,
    clearError,
    setHosts,
  };
}

export default useHosts;
