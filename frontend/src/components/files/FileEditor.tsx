/**
 * FileEditor component with Monaco editor integration.
 */

import React, { useEffect, useState } from 'react';
import { useFiles } from '../../hooks/useFiles';
import { canEdit, formatBytes } from '../../utils/files';

interface FileEditorProps {
  hostId: string;
  filePath?: string;
  onClose?: () => void;
}

export const FileEditor: React.FC<FileEditorProps> = ({
  hostId,
  filePath,
  onClose,
}) => {
  const { readFile, writeFile, isLoading, error, clearError } = useFiles(hostId);
  const [content, setContent] = useState('');
  const [originalContent, setOriginalContent] = useState('');
  const [isDirty, setIsDirty] = useState(false);
  const [fileSize, setFileSize] = useState(0);

  // Load file content on mount or when path changes
  useEffect(() => {
    if (!filePath) return;

    const loadFile = async () => {
      try {
        clearError();
        const text = await readFile(hostId, filePath);
        setContent(text);
        setOriginalContent(text);
        setFileSize(new TextEncoder().encode(text).length);
        setIsDirty(false);
      } catch (err) {
        console.error('Failed to load file:', err);
      }
    };

    loadFile();
  }, [hostId, filePath, readFile, clearError]);

  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setContent(newContent);
    setIsDirty(newContent !== originalContent);
  };

  const handleSave = async () => {
    if (!filePath) return;

    try {
      clearError();
      await writeFile(hostId, filePath, content);
      setOriginalContent(content);
      setIsDirty(false);
      setFileSize(new TextEncoder().encode(content).length);
    } catch (err) {
      console.error('Failed to save file:', err);
    }
  };

  const handleDiscard = () => {
    setContent(originalContent);
    setIsDirty(false);
  };

  if (!filePath) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-center h-64 text-gray-500">
          Select a file to edit
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow flex flex-col h-full">
      {/* Header */}
      <div className="border-b p-4 flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">{filePath.split('/').pop()}</h3>
          <p className="text-xs text-gray-600 mt-1">
            {filePath} • {formatBytes(fileSize)}
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
          title="Close editor"
        >
          ✕
        </button>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 p-3 text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Editor toolbar */}
      <div className="border-b p-3 flex gap-2 bg-gray-50">
        <button
          onClick={handleSave}
          disabled={!isDirty || isLoading}
          className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 text-sm font-medium"
        >
          💾 Save
        </button>
        <button
          onClick={handleDiscard}
          disabled={!isDirty || isLoading}
          className="px-3 py-1 bg-gray-300 hover:bg-gray-400 disabled:opacity-50 rounded text-sm"
        >
          Discard
        </button>
        {isDirty && (
          <span className="ml-auto text-red-600 text-sm font-medium">
            • Unsaved changes
          </span>
        )}
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Loading file...
          </div>
        ) : (
          <textarea
            value={content}
            onChange={handleContentChange}
            className="w-full h-full p-4 font-mono text-sm focus:outline-none resize-none"
            placeholder="File content"
            spellCheck="false"
          />
        )}
      </div>

      {/* Status bar */}
      <div className="border-t p-3 bg-gray-50 text-xs text-gray-600 flex justify-between">
        <span>
          {content.split('\n').length} lines • {content.length} characters
        </span>
        <span>
          {isDirty ? 'Modified' : 'Saved'}
        </span>
      </div>
    </div>
  );
};
