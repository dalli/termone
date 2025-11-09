/**
 * FileUpload component with drag-drop support.
 */

import React, { useRef, useState } from 'react';
import { useFiles } from '../../hooks/useFiles';
import { formatBytes, isValidUploadSize } from '../../utils/files';

interface FileUploadProps {
  hostId: string;
  currentPath: string;
  onUploadComplete?: (path: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  hostId,
  currentPath,
  onUploadComplete,
}) => {
  const { uploadFile, isLoading, error, clearError } = useFiles(hostId);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  const handleFiles = async (files: FileList) => {
    clearError();
    setUploadedFiles([]);

    for (const file of Array.from(files)) {
      // Validate file size
      if (!isValidUploadSize(file.size)) {
        alert(
          `File ${file.name} exceeds maximum size of 500 MB`
        );
        continue;
      }

      try {
        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: 0,
        }));

        const result = await uploadFile(hostId, file, currentPath);

        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: 100,
        }));

        setUploadedFiles((prev) => [...prev, file.name]);

        if (onUploadComplete) {
          onUploadComplete(result.path);
        }
      } catch (err) {
        // Error already set in hook state
        console.error('Upload failed:', err);
      }
    }
  };

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">Upload Files</h3>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Drag and drop zone */}
      <div
        ref={dropZoneRef}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 bg-gray-50 hover:border-gray-400'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleChange}
          disabled={isLoading}
          className="hidden"
        />

        <div className="flex flex-col items-center gap-2">
          <div className="text-3xl">📤</div>
          <div className="text-gray-700 font-medium">
            Drag files here or click to select
          </div>
          <div className="text-gray-500 text-sm">
            Maximum file size: 500 MB
          </div>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Select Files
          </button>
        </div>
      </div>

      {/* Upload progress */}
      {Object.entries(uploadProgress).length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold mb-3 text-gray-700">
            Upload Progress
          </h4>
          <div className="space-y-3">
            {Object.entries(uploadProgress).map(([filename, progress]) => (
              <div key={filename}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-700 truncate">
                    {filename}
                  </span>
                  <span className="text-sm text-gray-500">{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      progress === 100 ? 'bg-green-600' : 'bg-blue-600'
                    }`}
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Uploaded files list */}
      {uploadedFiles.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold mb-3 text-gray-700">
            Uploaded Files
          </h4>
          <ul className="space-y-2">
            {uploadedFiles.map((filename) => (
              <li
                key={filename}
                className="flex items-center gap-2 text-sm text-green-700"
              >
                <span>✓</span>
                <span>{filename}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Current path info */}
      <div className="mt-4 text-xs text-gray-600">
        <span className="font-semibold">Uploading to:</span> {currentPath}
      </div>
    </div>
  );
};
