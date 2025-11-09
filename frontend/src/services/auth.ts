/**
 * Authentication service for managing user auth workflows
 */

import api from './api';

interface LoginRequest {
  username: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    email: string;
    is_admin: boolean;
    is_active?: boolean;
  };
}

interface RefreshTokenRequest {
  refresh_token: string;
}

interface RefreshTokenResponse {
  access_token: string;
  token_type: string;
}

interface User {
  id: string;
  username: string;
  email: string;
  is_admin: boolean;
  is_active: boolean;
}

const AUTH_TOKEN_KEY = 'termone_auth_token';
const REFRESH_TOKEN_KEY = 'termone_refresh_token';
const USER_KEY = 'termone_user';

/**
 * Authentication service
 */
export const authService = {
  /**
   * Login with username and password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await api.post<LoginResponse>('/auth/login', credentials);

      // Store tokens and user data
      if (response.data.access_token) {
        localStorage.setItem(AUTH_TOKEN_KEY, response.data.access_token);
        localStorage.setItem(AUTH_TOKEN_KEY + '_expires', String(Date.now() + 3600000)); // 1 hour
      }

      if (response.data.user) {
        localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
      }

      return response.data;
    } catch (error) {
      throw new Error(`Login failed: ${error}`);
    }
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      // Call logout endpoint if it exists
      await api.post('/auth/logout');
    } catch (error) {
      // Continue logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      // Clear local storage
      this.clearAuthData();
    }
  },

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await api.post<RefreshTokenResponse>('/auth/refresh', {
        refresh_token: refreshToken,
      });

      if (response.data.access_token) {
        localStorage.setItem(AUTH_TOKEN_KEY, response.data.access_token);
        localStorage.setItem(AUTH_TOKEN_KEY + '_expires', String(Date.now() + 3600000));
      }

      return response.data.access_token;
    } catch (error) {
      this.clearAuthData();
      throw new Error('Token refresh failed');
    }
  },

  /**
   * Get current auth token
   */
  getToken(): string | null {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    const expires = localStorage.getItem(AUTH_TOKEN_KEY + '_expires');

    if (!token || !expires) {
      return null;
    }

    // Check if token has expired
    if (parseInt(expires) < Date.now()) {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_TOKEN_KEY + '_expires');
      return null;
    }

    return token;
  },

  /**
   * Get current user
   */
  getCurrentUser(): User | null {
    const userJson = localStorage.getItem(USER_KEY);

    if (!userJson) {
      return null;
    }

    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getToken() && !!this.getCurrentUser();
  },

  /**
   * Check if current user is admin
   */
  isAdmin(): boolean {
    const user = this.getCurrentUser();
    return user?.is_admin ?? false;
  },

  /**
   * Verify token with backend
   */
  async verifyToken(): Promise<boolean> {
    const token = this.getToken();

    if (!token) {
      return false;
    }

    try {
      const response = await api.get('/auth/verify');
      return response.status === 200;
    } catch (error) {
      this.clearAuthData();
      return false;
    }
  },

  /**
   * Set auth data (used for storing login response)
   */
  setAuthData(token: string, user: User, refreshToken?: string): void {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    localStorage.setItem(AUTH_TOKEN_KEY + '_expires', String(Date.now() + 3600000));
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
  },

  /**
   * Clear all auth data
   */
  clearAuthData(): void {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_TOKEN_KEY + '_expires');
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  /**
   * Update user profile
   */
  async updateProfile(updates: Partial<User>): Promise<User> {
    try {
      const response = await api.put<User>('/auth/profile', updates);

      // Update local storage
      const currentUser = this.getCurrentUser();
      if (currentUser) {
        const updatedUser = { ...currentUser, ...response.data };
        localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
      }

      return response.data;
    } catch (error) {
      throw new Error(`Profile update failed: ${error}`);
    }
  },

  /**
   * Change password
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    try {
      await api.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword,
      });
    } catch (error) {
      throw new Error(`Password change failed: ${error}`);
    }
  },

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<void> {
    try {
      await api.post('/auth/password-reset-request', { email });
    } catch (error) {
      throw new Error(`Password reset request failed: ${error}`);
    }
  },

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    try {
      await api.post('/auth/password-reset', {
        token,
        new_password: newPassword,
      });
    } catch (error) {
      throw new Error(`Password reset failed: ${error}`);
    }
  },

  /**
   * Get TOTP setup (for 2FA)
   */
  async getTOTPSetup(): Promise<{ secret: string; qr_code: string }> {
    try {
      const response = await api.get<{ secret: string; qr_code: string }>(
        '/auth/totp-setup'
      );
      return response.data;
    } catch (error) {
      throw new Error(`TOTP setup failed: ${error}`);
    }
  },

  /**
   * Verify and enable TOTP
   */
  async enableTOTP(code: string): Promise<void> {
    try {
      await api.post('/auth/totp-enable', { code });
    } catch (error) {
      throw new Error(`TOTP enable failed: ${error}`);
    }
  },

  /**
   * Disable TOTP
   */
  async disableTOTP(code: string): Promise<void> {
    try {
      await api.post('/auth/totp-disable', { code });
    } catch (error) {
      throw new Error(`TOTP disable failed: ${error}`);
    }
  },
};

export default authService;
