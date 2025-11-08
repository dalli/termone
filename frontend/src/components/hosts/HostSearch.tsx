/**
 * HostSearch Component - Search and filter hosts
 */

import React, { useState, useCallback } from 'react';
import useHosts from '@/hooks/useHosts';

interface HostSearchProps {
  onSearch?: (query: string) => void;
  onFilterChange?: (filters: any) => void;
}

export const HostSearch: React.FC<HostSearchProps> = ({ onSearch, onFilterChange }) => {
  const { searchHosts } = useHosts();
  const [searchQuery, setSearchQuery] = useState('');
  const [tagFilter, setTagFilter] = useState('');
  const [folderFilter, setFolderFilter] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!searchQuery.trim()) {
        return;
      }

      setIsSearching(true);
      try {
        await searchHosts(searchQuery.trim());
        if (onSearch) {
          onSearch(searchQuery);
        }
      } catch (error) {
        console.error('Search failed:', error);
      } finally {
        setIsSearching(false);
      }
    },
    [searchQuery, searchHosts, onSearch]
  );

  const handleFilterChange = useCallback(() => {
    const filters: any = {};

    if (tagFilter.trim()) {
      filters.tags = tagFilter
        .split(',')
        .map(t => t.trim())
        .filter(t => t);
    }

    if (folderFilter.trim()) {
      filters.folder = folderFilter.trim();
    }

    if (onFilterChange) {
      onFilterChange(filters);
    }
  }, [tagFilter, folderFilter, onFilterChange]);

  const handleClearFilters = () => {
    setSearchQuery('');
    setTagFilter('');
    setFolderFilter('');

    if (onFilterChange) {
      onFilterChange({});
    }
  };

  return (
    <div className="w-full bg-white rounded-lg shadow p-4 mb-6">
      <h3 className="text-lg font-semibold mb-4">Search & Filter Hosts</h3>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-4">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search by hostname or description..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching || !searchQuery.trim()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Filters */}
      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Filter by Tags (comma-separated)
          </label>
          <input
            type="text"
            value={tagFilter}
            onChange={e => {
              setTagFilter(e.target.value);
              handleFilterChange();
            }}
            placeholder="production, web, api..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Filter by Folder
          </label>
          <input
            type="text"
            value={folderFilter}
            onChange={e => {
              setFolderFilter(e.target.value);
              handleFilterChange();
            }}
            placeholder="e.g., production, development..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          onClick={handleClearFilters}
          className="text-sm text-gray-600 hover:text-gray-800 underline"
        >
          Clear all filters
        </button>
      </div>

      {/* Active filters display */}
      {(searchQuery || tagFilter || folderFilter) && (
        <div className="mt-4 pt-4 border-t">
          <p className="text-sm text-gray-600 mb-2">Active filters:</p>
          <div className="flex flex-wrap gap-2">
            {searchQuery && (
              <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                Search: {searchQuery}
              </span>
            )}
            {tagFilter && (
              <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                Tags: {tagFilter}
              </span>
            )}
            {folderFilter && (
              <span className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">
                Folder: {folderFilter}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default HostSearch;
