/**
 * Files page - Remote file management via SFTP
 */

import React, { useState } from 'react';
import { FileExplorer } from '../components/files/FileExplorer';
import { FileUpload } from '../components/files/FileUpload';
import { FileEditor } from '../components/files/FileEditor';
import { MediaViewer } from '../components/files/MediaViewer';
import { useFiles } from '../hooks/useFiles';
import { getMimeType, canEdit, canViewInline } from '../utils/files';

interface HostOption {
  id: string;
  hostname: string;
}

export default function FilesPage() {
  const [selectedHostId, setSelectedHostId] = useState<string>('');
  const [hostList, setHostList] = useState<HostOption[]>([]);
  const [currentPath, setCurrentPath] = useState('/');
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [viewMode, setViewMode] = useState<'explorer' | 'editor' | 'viewer'>('explorer');

  const {
    entries,
    currentPath: explorerPath,
    isLoading,
    error,
    listDirectory,
    navigateTo,
  } = useFiles(selectedHostId);

  // Load host list
  React.useEffect(() => {
    const loadHosts = async () => {
      try {
        // This would be replaced with actual API call
        const mockHosts: HostOption[] = [
          { id: '1', hostname: 'prod-server-1' },
          { id: '2', hostname: 'dev-server' },
        ];
        setHostList(mockHosts);
      } catch (err) {
        console.error('Failed to load hosts:', err);
      }
    };

    loadHosts();
  }, []);

  const handleHostSelect = (hostId: string) => {
    setSelectedHostId(hostId);
    setSelectedFile('');
    setViewMode('explorer');
    setCurrentPath('/');
  };

  const handleFileSelect = (path: string) => {
    setSelectedFile(path);

    const mimeType = getMimeType(path);
    if (canEdit(Number.MAX_SAFE_INTEGER, mimeType)) {
      setViewMode('editor');
    } else if (canViewInline(Number.MAX_SAFE_INTEGER, mimeType)) {
      setViewMode('viewer');
    }
  };

  const handleNavigate = (path: string) => {
    setCurrentPath(path);
    navigateTo(path);
  };

  if (!selectedHostId) {
    return (
      <div className="min-h-screen bg-gray-100 p-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">File Manager</h1>

          <div className="bg-white rounded-lg shadow p-6">
            <label className="block mb-4">
              <span className="text-gray-700 font-semibold mb-2 block">
                Select Host
              </span>
              <select
                value={selectedHostId}
                onChange={(e) => handleHostSelect(e.target.value)}
                className="w-full max-w-xs px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Choose a host...</option>
                {hostList.map((host) => (
                  <option key={host.id} value={host.id}>
                    {host.hostname}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold">File Manager</h1>
          <div className="flex items-center gap-4">
            <select
              value={selectedHostId}
              onChange={(e) => handleHostSelect(e.target.value)}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Choose a host...</option>
              {hostList.map((host) => (
                <option key={host.id} value={host.id}>
                  {host.hostname}
                </option>
              ))}
            </select>
            <button
              onClick={() => setViewMode('explorer')}
              className={`px-4 py-2 rounded ${
                viewMode === 'explorer'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 hover:bg-gray-300'
              }`}
            >
              📁 Explorer
            </button>
            <button
              onClick={() => setViewMode('editor')}
              className={`px-4 py-2 rounded ${
                viewMode === 'editor'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 hover:bg-gray-300'
              }`}
            >
              ✏️ Editor
            </button>
          </div>
        </div>

        {/* Main content area */}
        <div className="grid grid-cols-3 gap-6">
          {/* Explorer */}
          <div className="col-span-2">
            {viewMode === 'explorer' && (
              <FileExplorer
                hostId={selectedHostId}
                onFileSelect={handleFileSelect}
                initialPath={currentPath}
              />
            )}
            {viewMode === 'editor' && (
              <FileEditor
                hostId={selectedHostId}
                filePath={selectedFile}
                onClose={() => setViewMode('explorer')}
              />
            )}
            {viewMode === 'viewer' && (
              <MediaViewer
                hostId={selectedHostId}
                filePath={selectedFile}
                onClose={() => setViewMode('explorer')}
              />
            )}
          </div>

          {/* Upload sidebar */}
          <div>
            <FileUpload
              hostId={selectedHostId}
              currentPath={currentPath || '/'}
              onUploadComplete={(path) => {
                handleNavigate(currentPath || '/');
              }}
            />
          </div>
        </div>

        {/* Selected file info */}
        {selectedFile && (
          <div className="mt-6 bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold mb-2">Selected File</h3>
            <p className="text-gray-600 text-sm">
              {selectedFile}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
