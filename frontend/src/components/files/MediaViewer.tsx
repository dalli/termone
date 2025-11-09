/**
 * MediaViewer component for viewing images, audio, and video files.
 */

import React, { useEffect, useState } from 'react';
import { useFiles } from '../../hooks/useFiles';
import { getMimeType, getFileCategory } from '../../utils/files';

interface MediaViewerProps {
  hostId: string;
  filePath?: string;
  onClose?: () => void;
}

export const MediaViewer: React.FC<MediaViewerProps> = ({
  hostId,
  filePath,
  onClose,
}) => {
  const { downloadFile, isLoading, error, clearError } = useFiles(hostId);
  const [mediaUrl, setMediaUrl] = useState<string>('');
  const [loadError, setLoadError] = useState<string>('');

  useEffect(() => {
    if (!filePath) {
      setMediaUrl('');
      return;
    }

    const loadMedia = async () => {
      try {
        clearError();
        setLoadError('');

        const response = await fetch(
          `/api/files/${hostId}/download?path=${encodeURIComponent(filePath)}`,
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to load file');
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setMediaUrl(url);
      } catch (err: any) {
        setLoadError(err.message || 'Failed to load media');
      }
    };

    loadMedia();

    return () => {
      if (mediaUrl) {
        URL.revokeObjectURL(mediaUrl);
      }
    };
  }, [hostId, filePath, downloadFile, clearError]);

  if (!filePath) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-center h-64 text-gray-500">
          Select a file to view
        </div>
      </div>
    );
  }

  const mimeType = getMimeType(filePath);
  const category = getFileCategory(mimeType);
  const filename = filePath.split('/').pop() || 'file';

  return (
    <div className="bg-white rounded-lg shadow flex flex-col h-full">
      {/* Header */}
      <div className="border-b p-4 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">{filename}</h3>
          <p className="text-xs text-gray-600 mt-1">{filePath}</p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
          title="Close viewer"
        >
          ✕
        </button>
      </div>

      {/* Error message */}
      {(error || loadError) && (
        <div className="bg-red-50 border-b border-red-200 p-3 text-red-700 text-sm">
          {error || loadError}
        </div>
      )}

      {/* Media viewer */}
      <div className="flex-1 overflow-auto flex items-center justify-center bg-gray-50">
        {isLoading ? (
          <div className="text-gray-500">Loading...</div>
        ) : !mediaUrl ? (
          <div className="text-gray-500">Failed to load media</div>
        ) : category === 'image' ? (
          <img
            src={mediaUrl}
            alt={filename}
            className="max-w-full max-h-full object-contain"
          />
        ) : category === 'audio' ? (
          <div className="flex flex-col items-center gap-4">
            <div className="text-4xl">🎵</div>
            <audio
              controls
              src={mediaUrl}
              className="w-80"
            >
              Your browser does not support the audio element.
            </audio>
          </div>
        ) : category === 'video' ? (
          <video
            controls
            src={mediaUrl}
            className="max-w-full max-h-full"
          >
            Your browser does not support the video element.
          </video>
        ) : (
          <div className="text-gray-500">Preview not available for this file type</div>
        )}
      </div>

      {/* Download button */}
      <div className="border-t p-4 bg-gray-50">
        <button
          onClick={() => downloadFile(hostId, filePath)}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
        >
          📥 Download
        </button>
      </div>
    </div>
  );
};
