/**
 * Terminal service for managing terminal sessions
 */

import api from './api';

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

export interface TerminalMessage {
  type: string;
  session_id: string;
  data: string;
  timestamp?: string;
}

/**
 * Terminal service
 */
export const terminalService = {
  /**
   * Create a new terminal session
   */
  async createSession(
    hostId: string,
    rows: number = 24,
    cols: number = 80,
    env?: Record<string, string>
  ): Promise<TerminalSession> {
    try {
      const response = await api.post<TerminalSession>(`/terminal/sessions/${hostId}`, {
        rows,
        cols,
        env,
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create terminal session: ${error}`);
    }
  },

  /**
   * List all active terminal sessions
   */
  async listSessions(): Promise<TerminalSession[]> {
    try {
      const response = await api.get<{ items: TerminalSession[]; total: number }>(
        '/terminal/sessions'
      );
      return response.data.items;
    } catch (error) {
      throw new Error(`Failed to list terminal sessions: ${error}`);
    }
  },

  /**
   * Get a specific terminal session
   */
  async getSession(sessionId: string): Promise<TerminalSession> {
    try {
      const response = await api.get<TerminalSession>(`/terminal/sessions/${sessionId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get terminal session: ${error}`);
    }
  },

  /**
   * Delete/close a terminal session
   */
  async deleteSession(sessionId: string): Promise<void> {
    try {
      await api.delete(`/terminal/sessions/${sessionId}`);
    } catch (error) {
      throw new Error(`Failed to delete terminal session: ${error}`);
    }
  },

  /**
   * Resize terminal
   */
  async resizeTerminal(
    sessionId: string,
    rows: number,
    cols: number
  ): Promise<void> {
    try {
      await api.post(`/terminal/sessions/${sessionId}/resize`, {
        rows,
        cols,
      });
    } catch (error) {
      throw new Error(`Failed to resize terminal: ${error}`);
    }
  },

  /**
   * Execute a command in terminal
   */
  async executeCommand(
    sessionId: string,
    command: string,
    timeout?: number
  ): Promise<void> {
    try {
      await api.post(`/terminal/sessions/${sessionId}/execute`, {
        command,
        timeout,
      });
    } catch (error) {
      throw new Error(`Failed to execute command: ${error}`);
    }
  },

  /**
   * Get terminal preferences
   */
  async getPreferences(): Promise<any> {
    try {
      const preferences = localStorage.getItem('termone_terminal_preferences');
      return preferences ? JSON.parse(preferences) : getDefaultPreferences();
    } catch (error) {
      return getDefaultPreferences();
    }
  },

  /**
   * Save terminal preferences
   */
  async savePreferences(preferences: any): Promise<void> {
    try {
      localStorage.setItem('termone_terminal_preferences', JSON.stringify(preferences));
    } catch (error) {
      throw new Error(`Failed to save terminal preferences: ${error}`);
    }
  },

  /**
   * Get theme
   */
  async getTheme(): Promise<string> {
    try {
      const theme = localStorage.getItem('termone_terminal_theme');
      return theme || 'dracula';
    } catch (error) {
      return 'dracula';
    }
  },

  /**
   * Set theme
   */
  async setTheme(theme: string): Promise<void> {
    try {
      localStorage.setItem('termone_terminal_theme', theme);
    } catch (error) {
      throw new Error(`Failed to set terminal theme: ${error}`);
    }
  },

  /**
   * Get font size
   */
  async getFontSize(): Promise<number> {
    try {
      const size = localStorage.getItem('termone_terminal_font_size');
      return size ? parseInt(size) : 14;
    } catch (error) {
      return 14;
    }
  },

  /**
   * Set font size
   */
  async setFontSize(size: number): Promise<void> {
    try {
      localStorage.setItem('termone_terminal_font_size', size.toString());
    } catch (error) {
      throw new Error(`Failed to set font size: ${error}`);
    }
  },

  /**
   * Get font family
   */
  async getFontFamily(): Promise<string> {
    try {
      const family = localStorage.getItem('termone_terminal_font_family');
      return family || "'Courier New', monospace";
    } catch (error) {
      return "'Courier New', monospace";
    }
  },

  /**
   * Set font family
   */
  async setFontFamily(family: string): Promise<void> {
    try {
      localStorage.setItem('termone_terminal_font_family', family);
    } catch (error) {
      throw new Error(`Failed to set font family: ${error}`);
    }
  },
};

function getDefaultPreferences() {
  return {
    theme: 'dracula',
    fontSize: 14,
    fontFamily: "'Courier New', monospace",
    bellEnabled: true,
    bellType: 'visual',
  };
}

export default terminalService;
