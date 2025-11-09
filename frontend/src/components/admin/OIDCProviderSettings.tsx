/**
 * OIDCProviderSettings component for admin panel.
 */

import React, { useState, useEffect } from 'react';
import { OIDCProvider } from '../../hooks/useAdmin';

interface OIDCProviderSettingsProps {
  providers: OIDCProvider[];
  isLoading: boolean;
  error: string | null;
  onRefresh: () => Promise<void>;
  onCreate: (data: any) => Promise<void>;
  onUpdate: (providerId: string, data: any) => Promise<void>;
  onDelete: (providerId: string) => Promise<void>;
}

export const OIDCProviderSettings: React.FC<OIDCProviderSettingsProps> = ({
  providers,
  isLoading,
  error,
  onRefresh,
  onCreate,
  onUpdate,
  onDelete,
}) => {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    display_name: '',
    client_id: '',
    client_secret: '',
    discovery_url: '',
    scopes: ['openid', 'profile', 'email'],
  });

  useEffect(() => {
    onRefresh();
  }, []);

  const handleReset = () => {
    setFormData({
      name: '',
      display_name: '',
      client_id: '',
      client_secret: '',
      discovery_url: '',
      scopes: ['openid', 'profile', 'email'],
    });
    setEditingId(null);
    setShowForm(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        await onUpdate(editingId, formData);
      } else {
        await onCreate(formData);
      }
      handleReset();
      await onRefresh();
    } catch (err) {
      console.error('Failed to save provider:', err);
    }
  };

  const handleDelete = async (providerId: string) => {
    if (window.confirm('Are you sure you want to delete this provider?')) {
      try {
        await onDelete(providerId);
        await onRefresh();
      } catch (err) {
        console.error('Failed to delete provider:', err);
      }
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900">OIDC Providers</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          {showForm ? 'Cancel' : '+ Add Provider'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Display Name *
              </label>
              <input
                type="text"
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Client ID *
              </label>
              <input
                type="text"
                value={formData.client_id}
                onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Client Secret *
              </label>
              <input
                type="password"
                value={formData.client_secret}
                onChange={(e) => setFormData({ ...formData, client_secret: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                required
              />
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Discovery URL *
            </label>
            <input
              type="url"
              value={formData.discovery_url}
              onChange={(e) => setFormData({ ...formData, discovery_url: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              required
            />
          </div>

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Saving...' : 'Save Provider'}
            </button>
          </div>
        </form>
      )}

      {/* Providers List */}
      {isLoading ? (
        <div className="text-center py-8">
          <div className="animate-spin inline-block">⟳</div>
          <p className="mt-2 text-gray-600">Loading providers...</p>
        </div>
      ) : providers.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No OIDC providers configured
        </div>
      ) : (
        <div className="space-y-3">
          {providers.map((provider) => (
            <div
              key={provider.id}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-medium text-gray-900">
                    {provider.display_name}
                  </h3>
                  <p className="text-xs text-gray-500">{provider.name}</p>
                </div>
                <span className={`inline-flex px-2 py-1 rounded-full text-xs font-semibold ${
                  provider.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {provider.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-sm mb-3">
                <div>
                  <p className="text-gray-500">Client ID:</p>
                  <p className="font-mono text-xs text-gray-600">{provider.client_id}</p>
                </div>
                <div>
                  <p className="text-gray-500">Discovery URL:</p>
                  <p className="font-mono text-xs text-gray-600 truncate">
                    {provider.discovery_url}
                  </p>
                </div>
              </div>

              <div className="mb-3">
                <p className="text-sm text-gray-500 mb-1">Scopes:</p>
                <div className="flex flex-wrap gap-1">
                  {provider.scopes.map((scope) => (
                    <span
                      key={scope}
                      className="inline-flex px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs"
                    >
                      {scope}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setEditingId(provider.id);
                    setFormData({
                      name: provider.name,
                      display_name: provider.display_name,
                      client_id: provider.client_id,
                      client_secret: '',
                      discovery_url: provider.discovery_url,
                      scopes: provider.scopes,
                    });
                    setShowForm(true);
                  }}
                  className="text-blue-600 hover:text-blue-900 font-medium text-sm"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(provider.id)}
                  className="text-red-600 hover:text-red-900 font-medium text-sm"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
