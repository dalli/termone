/**
 * FileExplorer component for browsing remote directories and managing files.
 */

import React, { useEffect, useState } from 'react';
import { useFiles } from '../../hooks/useFiles';
import {
  formatBytes,
  formatModifiedTime,
  getFileIcon,
  formatPermissions,
  joinPath,
} from '../../utils/files';

interface FileExplorerProps {
  hostId: string;
  onFileSelect?: (path: string) => void;
  initialPath?: string;
}

interface BreadcrumbItem {
  name: string;
  path: string;
}

export const FileExplorer: React.FC<FileExplorerProps> = ({
  hostId,
  onFileSelect,
  initialPath = '/',
}) => {
  const {
    entries,
    currentPath,
    isLoading,
    error,
    selectedFiles,
    listDirectory,
    navigateTo,
    goBack,
    deleteFile,
    toggleSelect,
    selectAll,
    deselectAll,
    clearError,
  } = useFiles(hostId);

  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([]);

  // Initialize directory listing
  useEffect(() => {
    listDirectory(hostId, initialPath);
  }, [hostId, initialPath, listDirectory]);

  // Update breadcrumbs
  useEffect(() => {
    const parts = currentPath.split('/').filter(Boolean);
    const newBreadcrumbs: BreadcrumbItem[] = [{ name: '/', path: '/' }];

    let currentBuildPath = '';
    parts.forEach((part) => {
      currentBuildPath += '/' + part;
      newBreadcrumbs.push({ name: part, path: currentBuildPath });
    });

    setBreadcrumbs(newBreadcrumbs);
  }, [currentPath]);

  const handleNavigate = (path: string) => {
    navigateTo(path);
  };

  const handleDoubleClick = (entry) => {
    if (entry.type === 'directory') {
      const newPath = joinPath(currentPath, entry.name);
      handleNavigate(newPath);
    } else if (onFileSelect) {
      const filePath = joinPath(currentPath, entry.name);
      onFileSelect(filePath);
    }
  };

  const handleDelete = async (name: string) => {
    if (!window.confirm(`Are you sure you want to delete ${name}?`)) {
      return;
    }
    const filePath = joinPath(currentPath, name);
    try {
      await deleteFile(hostId, filePath);
    } catch {
      // Error already set in state
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow">
      {/* Header */}
      <div className="border-b p-4">
        <h2 className="text-lg font-semibold mb-3">File Explorer</h2>

        {/* Breadcrumbs */}
        <div className="flex items-center gap-1 text-sm mb-3">
          {breadcrumbs.map((item, index) => (
            <React.Fragment key={item.path}>
              <button
                onClick={() => handleNavigate(item.path)}
                className="text-blue-600 hover:text-blue-800 underline"
              >
                {item.name}
              </button>
              {index < breadcrumbs.length - 1 && (
                <span className="text-gray-400">/</span>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Controls */}
        <div className="flex gap-2">
          <button
            onClick={goBack}
            disabled={isLoading || currentPath === '/'}
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 disabled:opacity-50 rounded text-sm"
          >
            ← Back
          </button>
          <button
            onClick={selectAll}
            disabled={isLoading}
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 disabled:opacity-50 rounded text-sm"
          >
            Select All
          </button>
          <button
            onClick={deselectAll}
            disabled={isLoading}
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 disabled:opacity-50 rounded text-sm"
          >
            Deselect
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 p-4 text-red-700 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button
            onClick={clearError}
            className="text-red-500 hover:text-red-700"
          >
            ✕
          </button>
        </div>
      )}

      {/* File list */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Loading...
          </div>
        ) : entries.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Empty directory
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 sticky top-0 border-b">
              <tr>
                <th className="p-2 text-left w-6">
                  <input
                    type="checkbox"
                    checked={selectedFiles.size === entries.length && entries.length > 0}
                    onChange={(e) => (e.target.checked ? selectAll() : deselectAll())}
                    className="rounded"
                  />
                </th>
                <th className="p-2 text-left font-semibold text-gray-700">Name</th>
                <th className="p-2 text-right font-semibold text-gray-700 w-24">Size</th>
                <th className="p-2 text-left font-semibold text-gray-700 w-24">Permissions</th>
                <th className="p-2 text-left font-semibold text-gray-700 w-32">Modified</th>
                <th className="p-2 text-center w-16">Actions</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr
                  key={entry.name}
                  className="border-b hover:bg-gray-50 cursor-pointer"
                  onDoubleClick={() => handleDoubleClick(entry)}
                >
                  <td className="p-2">
                    <input
                      type="checkbox"
                      checked={selectedFiles.has(entry.name)}
                      onChange={() => toggleSelect(entry.name)}
                      onClick={(e) => e.stopPropagation()}
                      className="rounded"
                    />
                  </td>
                  <td className="p-2 font-medium text-gray-900">
                    <span className="mr-2">{getFileIcon(entry.name, entry.type)}</span>
                    <span
                      className={
                        entry.type === 'directory' ? 'font-semibold text-blue-600' : ''
                      }
                    >
                      {entry.name}
                    </span>
                  </td>
                  <td className="p-2 text-right text-gray-600">
                    {entry.type === 'directory' ? '-' : formatBytes(entry.size)}
                  </td>
                  <td className="p-2 text-gray-600 font-mono text-xs">
                    {formatPermissions(entry.mode)}
                  </td>
                  <td className="p-2 text-gray-600 text-xs">
                    {formatModifiedTime(entry.modified)}
                  </td>
                  <td className="p-2 text-center">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(entry.name);
                      }}
                      disabled={isLoading}
                      className="text-red-600 hover:text-red-800 disabled:opacity-50 text-sm"
                      title="Delete file"
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Status bar */}
      <div className="border-t p-2 bg-gray-50 text-xs text-gray-600">
        {selectedFiles.size > 0
          ? `${selectedFiles.size} file(s) selected`
          : `${entries.length} item(s)`}
      </div>
    </div>
  );
};
