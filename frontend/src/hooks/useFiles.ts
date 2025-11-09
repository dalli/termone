/**
 * useFiles hook for file management operations.
 *
 * Manages:
 * - Directory listing and navigation
 * - File uploads, downloads, deletes
 * - File content reading and editing
 * - Permission changes
 */

import { useState, useCallback } from 'react';
import api from '../services/api';

export interface FileInfo {
  name: string;
  type: 'file' | 'directory' | 'symlink';
  size: number;
  mode: number;
  modified: string;
  owner: string;
}

export interface DirectoryListing {
  entries: FileInfo[];
  path: string;
}

export interface UploadResult {
  path: string;
  size: number;
  message: string;
}

export interface FileContent {
  path: string;
  content: string;
  message: string;
}

export interface UseFilesReturn {
  // State
  entries: FileInfo[];
  currentPath: string;
  isLoading: boolean;
  error: string | null;
  selectedFiles: Set<string>;

  // Operations
  listDirectory: (hostId: string, path?: string) => Promise<void>;
  navigateTo: (path: string) => Promise<void>;
  goBack: () => Promise<void>;
  uploadFile: (hostId: string, file: File, path: string) => Promise<UploadResult>;
  downloadFile: (hostId: string, path: string) => Promise<void>;
  deleteFile: (hostId: string, path: string) => Promise<void>;
  readFile: (hostId: string, path: string) => Promise<string>;
  writeFile: (hostId: string, path: string, content: string) => Promise<FileContent>;
  chmodFile: (hostId: string, path: string, mode: number) => Promise<void>;
  moveFile: (hostId: string, oldPath: string, newPath: string) => Promise<void>;
  createDirectory: (hostId: string, path: string) => Promise<void>;

  // Selection
  toggleSelect: (name: string) => void;
  selectAll: () => void;
  deselectAll: () => void;

  // Utilities
  clearError: () => void;
}

export function useFiles(hostId?: string): UseFilesReturn {
  const [entries, setEntries] = useState<FileInfo[]>([]);
  const [currentPath, setCurrentPath] = useState('/');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());

  // List directory contents
  const listDirectory = useCallback(
    async (id: string, path = '/') => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.get<DirectoryListing>(`/files/${id}/list`, {
          params: { path },
        });
        setEntries(response.data.entries);
        setCurrentPath(response.data.path || path);
        setSelectedFiles(new Set()); // Clear selection on new directory
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to list directory');
        setEntries([]);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  // Navigate to directory
  const navigateTo = useCallback(
    async (path: string) => {
      if (!hostId) {
        setError('No host selected');
        return;
      }
      await listDirectory(hostId, path);
    },
    [hostId, listDirectory]
  );

  // Go back to parent directory
  const goBack = useCallback(async () => {
    if (!hostId) {
      setError('No host selected');
      return;
    }
    const parentPath = currentPath === '/' ? '/' : currentPath.substring(0, currentPath.lastIndexOf('/')) || '/';
    await listDirectory(hostId, parentPath);
  }, [hostId, currentPath, listDirectory]);

  // Upload file
  const uploadFile = useCallback(
    async (id: string, file: File, path: string): Promise<UploadResult> => {
      setIsLoading(true);
      setError(null);
      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post<UploadResult>(`/files/${id}/upload`, formData, {
          params: { path },
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        // Refresh directory
        await listDirectory(id, path);
        return response.data;
      } catch (err: any) {
        const message = err.response?.data?.detail || 'Failed to upload file';
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [listDirectory]
  );

  // Download file
  const downloadFile = useCallback(async (id: string, path: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get(`/files/${id}/download`, {
        params: { path },
        responseType: 'blob',
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', path.split('/').pop() || 'file');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to download file');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Delete file
  const deleteFile = useCallback(
    async (id: string, path: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await api.post(`/files/${id}/delete`, { path });
        // Refresh directory
        await listDirectory(id, currentPath);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to delete file');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [currentPath, listDirectory]
  );

  // Read file content
  const readFile = useCallback(async (id: string, path: string): Promise<string> => {
    setIsLoading(true);
    setError(null);
    try {
      // For text files, we would use edit endpoint with mode=read
      // For now, download and return content
      const response = await api.get(`/files/${id}/download`, {
        params: { path },
        responseType: 'text',
      });
      return response.data;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to read file');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Write file content
  const writeFile = useCallback(
    async (id: string, path: string, content: string): Promise<FileContent> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.post<FileContent>(`/files/${id}/edit`, {
          path,
          content,
        });
        // Refresh directory if file was created/modified
        await listDirectory(id, currentPath);
        return response.data;
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to write file');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [currentPath, listDirectory]
  );

  // Change file permissions
  const chmodFile = useCallback(
    async (id: string, path: string, mode: number) => {
      setIsLoading(true);
      setError(null);
      try {
        await api.post(`/files/${id}/chmod`, { path, mode });
        // Refresh directory
        await listDirectory(id, currentPath);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to change permissions');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [currentPath, listDirectory]
  );

  // Move/rename file
  const moveFile = useCallback(
    async (id: string, oldPath: string, newPath: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await api.post(`/files/${id}/move`, {
          old_path: oldPath,
          new_path: newPath,
        });
        // Refresh directory
        await listDirectory(id, currentPath);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to move file');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [currentPath, listDirectory]
  );

  // Create directory
  const createDirectory = useCallback(
    async (id: string, path: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await api.post(`/files/${id}/mkdir`, { path });
        // Refresh directory
        await listDirectory(id, currentPath);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to create directory');
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [currentPath, listDirectory]
  );

  // Toggle file selection
  const toggleSelect = useCallback((name: string) => {
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  }, []);

  // Select all files
  const selectAll = useCallback(() => {
    setSelectedFiles(new Set(entries.map((e) => e.name)));
  }, [entries]);

  // Deselect all files
  const deselectAll = useCallback(() => {
    setSelectedFiles(new Set());
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    entries,
    currentPath,
    isLoading,
    error,
    selectedFiles,
    listDirectory,
    navigateTo,
    goBack,
    uploadFile,
    downloadFile,
    deleteFile,
    readFile,
    writeFile,
    chmodFile,
    moveFile,
    createDirectory,
    toggleSelect,
    selectAll,
    deselectAll,
    clearError,
  };
}
