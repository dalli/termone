/**
 * useSnippets hook for snippet management operations.
 *
 * Manages:
 * - Snippet list and filtering
 * - Snippet creation, update, deletion
 * - Snippet execution and broadcasting
 */

import { useState, useCallback } from 'react';
import api from '../services/api';

export interface Snippet {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  command: string;
  tags?: string[];
  public: boolean;
  created_at: string;
  updated_at: string;
  usage_count: number;
}

export interface SnippetCreateRequest {
  name: string;
  description?: string;
  command: string;
  tags?: string[];
  public?: boolean;
}

export interface SnippetUpdateRequest {
  name?: string;
  description?: string;
  command?: string;
  tags?: string[];
  public?: boolean;
}

export interface ExecutionResult {
  execution_id: string;
  snippet_id: string;
  session_id?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  output?: string;
  error?: string;
  started_at: string;
  completed_at?: string;
}

export interface UseSnippetsReturn {
  // State
  snippets: Snippet[];
  isLoading: boolean;
  error: string | null;
  selectedSnippet: Snippet | null;
  tags: string[];

  // Operations
  listSnippets: (tags?: string[]) => Promise<void>;
  getSnippet: (snippetId: string) => Promise<Snippet | null>;
  createSnippet: (request: SnippetCreateRequest) => Promise<Snippet>;
  updateSnippet: (snippetId: string, request: SnippetUpdateRequest) => Promise<Snippet>;
  deleteSnippet: (snippetId: string) => Promise<void>;
  executeSnippet: (snippetId: string, sessionId: string) => Promise<ExecutionResult>;
  broadcastSnippet: (snippetId: string, sessionIds: string[]) => Promise<any>;
  selectSnippet: (snippet: Snippet | null) => void;
  clearError: () => void;
}

export function useSnippets(): UseSnippetsReturn {
  const [snippets, setSnippets] = useState<Snippet[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSnippet, setSelectedSnippet] = useState<Snippet | null>(null);
  const [tags, setTags] = useState<string[]>([]);

  // List snippets
  const listSnippets = useCallback(
    async (filterTags?: string[]) => {
      setIsLoading(true);
      setError(null);
      try {
        const params = filterTags ? { tags: filterTags.join(',') } : undefined;
        const response = await api.get<Snippet[]>('/snippets', { params });
        setSnippets(response.data);

        // Extract unique tags
        const allTags = new Set<string>();
        response.data.forEach((snippet) => {
          snippet.tags?.forEach((tag) => allTags.add(tag));
        });
        setTags(Array.from(allTags).sort());
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to list snippets');
        setSnippets([]);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Get single snippet
  const getSnippet = useCallback(
    async (snippetId: string): Promise<Snippet | null> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.get<Snippet>(`/snippets/${snippetId}`);
        return response.data;
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to get snippet');
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Create snippet
  const createSnippet = useCallback(
    async (request: SnippetCreateRequest): Promise<Snippet> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.post<Snippet>('/snippets', request);
        await listSnippets();
        return response.data;
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Failed to create snippet';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [listSnippets]
  );

  // Update snippet
  const updateSnippet = useCallback(
    async (snippetId: string, request: SnippetUpdateRequest): Promise<Snippet> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.put<Snippet>(`/snippets/${snippetId}`, request);
        await listSnippets();
        return response.data;
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Failed to update snippet';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [listSnippets]
  );

  // Delete snippet
  const deleteSnippet = useCallback(
    async (snippetId: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await api.delete(`/snippets/${snippetId}`);
        await listSnippets();
        if (selectedSnippet?.id === snippetId) {
          setSelectedSnippet(null);
        }
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Failed to delete snippet';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [listSnippets, selectedSnippet]
  );

  // Execute snippet
  const executeSnippet = useCallback(
    async (snippetId: string, sessionId: string): Promise<ExecutionResult> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.post<ExecutionResult>(
          `/snippets/${snippetId}/execute`,
          { session_id: sessionId }
        );
        return response.data;
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Failed to execute snippet';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Broadcast snippet
  const broadcastSnippet = useCallback(
    async (snippetId: string, sessionIds: string[]) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.post(
          `/snippets/${snippetId}/broadcast`,
          { session_ids: sessionIds }
        );
        return response.data;
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Failed to broadcast snippet';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Select snippet
  const selectSnippet = useCallback((snippet: Snippet | null) => {
    setSelectedSnippet(snippet);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Auto-load snippets on mount
  React.useEffect(() => {
    listSnippets();
  }, [listSnippets]);

  return {
    snippets,
    isLoading,
    error,
    selectedSnippet,
    tags,
    listSnippets,
    getSnippet,
    createSnippet,
    updateSnippet,
    deleteSnippet,
    executeSnippet,
    broadcastSnippet,
    selectSnippet,
    clearError,
  };
}
