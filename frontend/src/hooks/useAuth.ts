/**
 * useAuth hook for managing authentication state
 */

import { useState, useCallback, useEffect } from 'react';
import authService from '@/services/auth';

interface User {
  id: string;
  username: string;
  email: string;
  is_admin: boolean;
  is_active: boolean;
}

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  clearError: () => void;
}

/**
 * Hook for managing authentication state and operations
 */
export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize user from localStorage on mount
  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    if (currentUser && authService.isAuthenticated()) {
      setUser(currentUser);
    }
  }, []);

  const login = useCallback(
    async (username: string, password: string): Promise<void> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await authService.login({ username, password });
        setUser(response.user);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Login failed';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.logout();
      setUser(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Logout failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshToken = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await authService.refreshToken();
      // Token is stored automatically, verify it's still valid
      const currentUser = authService.getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Token refresh failed';
      setError(errorMessage);
      // If refresh fails, logout the user
      await logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  const clearError = useCallback((): void => {
    setError(null);
  }, []);

  return {
    user,
    isAuthenticated: user !== null && authService.isAuthenticated(),
    isAdmin: user?.is_admin ?? false,
    isLoading,
    error,
    login,
    logout,
    refreshToken,
    clearError,
  };
}

export default useAuth;
