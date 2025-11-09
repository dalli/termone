/**
 * SnippetForm component for creating and editing command snippets.
 */

import React, { useState, useEffect } from 'react';
import { Snippet } from '../../hooks/useSnippets';

interface SnippetFormProps {
  snippet?: Snippet;
  onSubmit: (data: SnippetFormData) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  error?: string;
}

export interface SnippetFormData {
  name: string;
  description?: string;
  command: string;
  tags?: string[];
  public?: boolean;
}

export const SnippetForm: React.FC<SnippetFormProps> = ({
  snippet,
  onSubmit,
  onCancel,
  isLoading = false,
  error,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [command, setCommand] = useState('');
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [isPublic, setIsPublic] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // Initialize form with existing snippet data
  useEffect(() => {
    if (snippet) {
      setName(snippet.name);
      setDescription(snippet.description || '');
      setCommand(snippet.command);
      setTags(snippet.tags || []);
      setIsPublic(snippet.public || false);
    }
  }, [snippet]);

  const handleAddTag = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const trimmedTag = tagInput.trim();
      if (trimmedTag && !tags.includes(trimmedTag)) {
        setTags([...tags, trimmedTag]);
        setTagInput('');
      }
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // Validation
    if (!name.trim()) {
      setFormError('Name is required');
      return;
    }
    if (!command.trim()) {
      setFormError('Command is required');
      return;
    }

    try {
      await onSubmit({
        name: name.trim(),
        description: description.trim() || undefined,
        command: command.trim(),
        tags: tags.length > 0 ? tags : undefined,
        public: isPublic,
      });
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to save snippet');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <h2 className="text-xl font-semibold mb-6">
        {snippet ? 'Edit Snippet' : 'Create Snippet'}
      </h2>

      {/* Error messages */}
      {(formError || error) && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {formError || error}
        </div>
      )}

      {/* Name field */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Name *
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Check Disk Space"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-gray-500">
          A descriptive name for your command snippet
        </p>
      </div>

      {/* Description field */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What does this command do?"
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans"
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-gray-500">
          Optional: Explain what this snippet does
        </p>
      </div>

      {/* Command field */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Command *
        </label>
        <textarea
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="e.g., df -h | grep -E '/$'"
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-gray-500">
          The SSH command to execute
        </p>
      </div>

      {/* Tags field */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Tags
        </label>
        <div className="flex flex-wrap gap-2 mb-2">
          {tags.map((tag) => (
            <div
              key={tag}
              className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
            >
              <span>{tag}</span>
              <button
                type="button"
                onClick={() => handleRemoveTag(tag)}
                className="text-blue-600 hover:text-blue-800 font-bold"
                title="Remove tag"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
        <input
          type="text"
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          onKeyDown={handleAddTag}
          placeholder="Type tag and press Enter or comma"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-gray-500">
          Add tags to organize your snippets (press Enter or comma to add)
        </p>
      </div>

      {/* Public toggle */}
      <div className="mb-6">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            disabled={isLoading}
            className="w-4 h-4 rounded border-gray-300"
          />
          Make this snippet public
        </label>
        <p className="mt-1 text-xs text-gray-500">
          Public snippets can be viewed by other users
        </p>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isLoading ? (
            <>
              <span className="animate-spin">⟳</span>
              Saving...
            </>
          ) : (
            'Save Snippet'
          )}
        </button>
      </div>
    </form>
  );
};
