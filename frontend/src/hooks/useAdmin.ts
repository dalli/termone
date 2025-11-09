/**
 * useAdmin hook for admin operations (users, sessions, OIDC providers).
 */

import { useState, useCallback } from 'react';

export interface User {
  id: string;
  email: string;
  username: string;
  created_at: string;
  last_login: string | null;
  is_active: boolean;
  role: string;
  host_count: number;
  session_count: number;
}

export interface Session {
  session_id: string;
  user_id: string;
  user_email: string;
  host_id: string | null;
  host_name: string | null;
  session_type: string;
  created_at: string;
  last_activity: string;
  status: string;
}

export interface OIDCProvider {
  id: string;
  name: string;
  display_name: string;
  client_id: string;
  discovery_url: string;
  scopes: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserListResponse {
  total: number;
  users: User[];
}

export interface SessionListResponse {
  total: number;
  active_sessions: number;
  sessions: Session[];
}

export interface OIDCProviderListResponse {
  total: number;
  providers: OIDCProvider[];
}

export interface UseAdminReturn {
  // Users
  users: User[];
  usersLoading: boolean;
  usersError: string | null;
  listUsers: (skip?: number, limit?: number) => Promise<void>;
  getUser: (userId: string) => Promise<User | null>;

  // Sessions
  sessions: Session[];
  sessionsLoading: boolean;
  sessionsError: string | null;
  listSessions: () => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;

  // OIDC Providers
  providers: OIDCProvider[];
  providersLoading: boolean;
  providersError: string | null;
  listProviders: () => Promise<void>;
  getProvider: (providerId: string) => Promise<OIDCProvider | null>;
  createProvider: (data: any) => Promise<OIDCProvider>;
  updateProvider: (providerId: string, data: any) => Promise<OIDCProvider>;
  deleteProvider: (providerId: string) => Promise<void>;

  clearError: () => void;
}

const API_BASE = '/api';

export function useAdmin(): UseAdminReturn {
  // Users state
  const [users, setUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState<string | null>(null);

  // Sessions state
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [sessionsError, setSessionsError] = useState<string | null>(null);

  // OIDC Providers state
  const [providers, setProviders] = useState<OIDCProvider[]>([]);
  const [providersLoading, setProvidersLoading] = useState(false);
  const [providersError, setProvidersError] = useState<string | null>(null);

  // User operations
  const listUsers = useCallback(async (skip = 0, limit = 50) => {
    setUsersLoading(true);
    setUsersError(null);
    try {
      const response = await fetch(
        `${API_BASE}/admin/users?skip=${skip}&limit=${limit}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      if (!response.ok) throw new Error('Failed to list users');
      const data: UserListResponse = await response.json();
      setUsers(data.users);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to list users';
      setUsersError(message);
    } finally {
      setUsersLoading(false);
    }
  }, []);

  const getUser = useCallback(async (userId: string): Promise<User | null> => {
    setUsersLoading(true);
    setUsersError(null);
    try {
      const response = await fetch(`${API_BASE}/admin/users/${userId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) throw new Error('Failed to get user');
      const data: User = await response.json();
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get user';
      setUsersError(message);
      return null;
    } finally {
      setUsersLoading(false);
    }
  }, []);

  // Session operations
  const listSessions = useCallback(async () => {
    setSessionsLoading(true);
    setSessionsError(null);
    try {
      const response = await fetch(`${API_BASE}/admin/sessions`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) throw new Error('Failed to list sessions');
      const data: SessionListResponse = await response.json();
      setSessions(data.sessions);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to list sessions';
      setSessionsError(message);
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  const deleteSession = useCallback(async (sessionId: string) => {
    setSessionsLoading(true);
    setSessionsError(null);
    try {
      const response = await fetch(`${API_BASE}/admin/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) throw new Error('Failed to delete session');
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete session';
      setSessionsError(message);
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  // OIDC Provider operations
  const listProviders = useCallback(async () => {
    setProvidersLoading(true);
    setProvidersError(null);
    try {
      const response = await fetch(`${API_BASE}/admin/settings/oidc-providers`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (!response.ok) throw new Error('Failed to list providers');
      const data: OIDCProviderListResponse = await response.json();
      setProviders(data.providers);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to list providers';
      setProvidersError(message);
    } finally {
      setProvidersLoading(false);
    }
  }, []);

  const getProvider = useCallback(
    async (providerId: string): Promise<OIDCProvider | null> => {
      setProvidersLoading(true);
      setProvidersError(null);
      try {
        const response = await fetch(
          `${API_BASE}/admin/settings/oidc-providers/${providerId}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );
        if (!response.ok) throw new Error('Failed to get provider');
        const data: OIDCProvider = await response.json();
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to get provider';
        setProvidersError(message);
        return null;
      } finally {
        setProvidersLoading(false);
      }
    },
    []
  );

  const createProvider = useCallback(async (data: any): Promise<OIDCProvider> => {
    setProvidersLoading(true);
    setProvidersError(null);
    try {
      const response = await fetch(`${API_BASE}/admin/settings/oidc-providers`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to create provider');
      const provider: OIDCProvider = await response.json();
      setProviders((prev) => [...prev, provider]);
      return provider;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create provider';
      setProvidersError(message);
      throw err;
    } finally {
      setProvidersLoading(false);
    }
  }, []);

  const updateProvider = useCallback(
    async (providerId: string, data: any): Promise<OIDCProvider> => {
      setProvidersLoading(true);
      setProvidersError(null);
      try {
        const response = await fetch(
          `${API_BASE}/admin/settings/oidc-providers/${providerId}`,
          {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
          }
        );
        if (!response.ok) throw new Error('Failed to update provider');
        const provider: OIDCProvider = await response.json();
        setProviders((prev) =>
          prev.map((p) => (p.id === providerId ? provider : p))
        );
        return provider;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update provider';
        setProvidersError(message);
        throw err;
      } finally {
        setProvidersLoading(false);
      }
    },
    []
  );

  const deleteProvider = useCallback(async (providerId: string) => {
    setProvidersLoading(true);
    setProvidersError(null);
    try {
      const response = await fetch(
        `${API_BASE}/admin/settings/oidc-providers/${providerId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );
      if (!response.ok) throw new Error('Failed to delete provider');
      setProviders((prev) => prev.filter((p) => p.id !== providerId));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete provider';
      setProvidersError(message);
      throw err;
    } finally {
      setProvidersLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setUsersError(null);
    setSessionsError(null);
    setProvidersError(null);
  }, []);

  return {
    // Users
    users,
    usersLoading,
    usersError,
    listUsers,
    getUser,

    // Sessions
    sessions,
    sessionsLoading,
    sessionsError,
    listSessions,
    deleteSession,

    // OIDC Providers
    providers,
    providersLoading,
    providersError,
    listProviders,
    getProvider,
    createProvider,
    updateProvider,
    deleteProvider,

    clearError,
  };
}
