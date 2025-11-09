/**
 * SnippetLibrary component for displaying and managing snippets.
 */

import React, { useEffect, useState } from 'react';
import { useSnippets, Snippet } from '../../hooks/useSnippets';

interface SnippetLibraryProps {
  onSelectSnippet?: (snippet: Snippet) => void;
  onExecute?: (snippet: Snippet) => void;
  compactMode?: boolean;
}

export const SnippetLibrary: React.FC<SnippetLibraryProps> = ({
  onSelectSnippet,
  onExecute,
  compactMode = false,
}) => {
  const { snippets, isLoading, error, listSnippets, deleteSnippet, tags, clearError } = useSnippets();
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  // Filter snippets by selected tags
  const filteredSnippets = selectedTags.length > 0
    ? snippets.filter((s) => s.tags?.some((tag) => selectedTags.includes(tag)))
    : snippets;

  const handleToggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleDelete = async (e: React.MouseEvent, snippetId: string) => {
    e.stopPropagation();
    if (!window.confirm('Delete this snippet?')) return;
    try {
      await deleteSnippet(snippetId);
    } catch (err) {
      console.error('Failed to delete snippet:', err);
    }
  };

  if (compactMode) {
    return (
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-700">Quick Snippets</h3>
        {isLoading ? (
          <div className="text-xs text-gray-500">Loading...</div>
        ) : filteredSnippets.length === 0 ? (
          <div className="text-xs text-gray-500">No snippets</div>
        ) : (
          <div className="space-y-1">
            {filteredSnippets.slice(0, 5).map((snippet) => (
              <button
                key={snippet.id}
                onClick={() => onExecute?.(snippet)}
                className="w-full text-left text-xs px-2 py-1 rounded bg-gray-100 hover:bg-blue-100 text-gray-700 truncate"
                title={snippet.command}
              >
                {snippet.name}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="border-b p-4">
        <h2 className="text-lg font-semibold">Snippet Library</h2>
      </div>

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 p-4 text-red-700 text-sm flex justify-between items-center">
          <span>{error}</span>
          <button onClick={clearError} className="text-red-500 hover:text-red-700">
            ✕
          </button>
        </div>
      )}

      {/* Tags filter */}
      {tags.length > 0 && (
        <div className="border-b p-4">
          <div className="text-xs font-semibold text-gray-600 mb-2">FILTER BY TAGS</div>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <button
                key={tag}
                onClick={() => handleToggleTag(tag)}
                className={`text-xs px-3 py-1 rounded-full transition-colors ${
                  selectedTags.includes(tag)
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Snippet list */}
      <div className="overflow-y-auto max-h-96">
        {isLoading ? (
          <div className="flex items-center justify-center p-8 text-gray-500">
            Loading snippets...
          </div>
        ) : filteredSnippets.length === 0 ? (
          <div className="flex items-center justify-center p-8 text-gray-500">
            {selectedTags.length > 0 ? 'No snippets with selected tags' : 'No snippets'}
          </div>
        ) : (
          <div className="divide-y">
            {filteredSnippets.map((snippet) => (
              <div
                key={snippet.id}
                onClick={() => onSelectSnippet?.(snippet)}
                className="p-4 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{snippet.name}</h3>
                    {snippet.description && (
                      <p className="text-xs text-gray-600 mt-1">{snippet.description}</p>
                    )}
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, snippet.id)}
                    className="text-red-500 hover:text-red-700 text-sm"
                    title="Delete snippet"
                  >
                    🗑️
                  </button>
                </div>

                {/* Command preview */}
                <div className="bg-gray-50 rounded p-2 text-xs font-mono text-gray-700 mb-2 truncate">
                  {snippet.command}
                </div>

                {/* Tags */}
                {snippet.tags && snippet.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-2">
                    {snippet.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* Usage count */}
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span>Used {snippet.usage_count} times</span>
                  {snippet.public && <span className="text-blue-600">Public</span>}
                </div>

                {/* Action buttons */}
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onExecute?.(snippet);
                    }}
                    className="flex-1 text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Execute
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Status bar */}
      <div className="border-t p-3 bg-gray-50 text-xs text-gray-600">
        {filteredSnippets.length} snippet(s) {selectedTags.length > 0 && `(filtered)`}
      </div>
    </div>
  );
};
