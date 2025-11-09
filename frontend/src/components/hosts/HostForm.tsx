/**
 * HostForm Component - Form for creating and editing SSH hosts
 */

import React, { useState, useEffect } from 'react';
import useHosts, { Host, HostCreateData, HostUpdateData } from '@/hooks/useHosts';

interface HostFormProps {
  host?: Host;
  onSuccess?: (host: Host) => void;
  onCancel?: () => void;
}

type CredentialType = 'password' | 'ssh_key';

interface FormData {
  hostname: string;
  port: number;
  username: string;
  tags: string;
  folder: string;
  description: string;
  credentialType: CredentialType;
  credentialValue: string;
}

export const HostForm: React.FC<HostFormProps> = ({ host, onSuccess, onCancel }) => {
  const { createHost, updateHost, error, isLoading, clearError } = useHosts();

  const [formData, setFormData] = useState<FormData>({
    hostname: host?.hostname ?? '',
    port: host?.port ?? 22,
    username: host?.username ?? '',
    tags: host?.tags.join(', ') ?? '',
    folder: host?.folder ?? '',
    description: host?.description ?? '',
    credentialType: (host?.credential_type as CredentialType) ?? 'password',
    credentialValue: '',
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.hostname.trim()) {
      errors.hostname = 'Hostname is required';
    }

    if (formData.port < 1 || formData.port > 65535) {
      errors.port = 'Port must be between 1 and 65535';
    }

    if (!formData.username.trim()) {
      errors.username = 'Username is required';
    }

    if (!host && !formData.credentialValue.trim()) {
      errors.credentialValue = 'Credential value is required for new hosts';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      const tagArray = formData.tags
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      if (host) {
        // Update existing host
        const updateData: HostUpdateData = {
          hostname: formData.hostname,
          port: formData.port,
          username: formData.username,
          tags: tagArray,
          folder: formData.folder || undefined,
          description: formData.description || undefined,
        };

        if (formData.credentialValue) {
          updateData.credential = {
            type: formData.credentialType,
            value: formData.credentialValue,
          };
        }

        const result = await updateHost(host.host_id, updateData);
        if (onSuccess) {
          onSuccess(result);
        }
      } else {
        // Create new host
        const createData: HostCreateData = {
          hostname: formData.hostname,
          port: formData.port,
          username: formData.username,
          tags: tagArray,
          folder: formData.folder || undefined,
          description: formData.description || undefined,
          credential: {
            type: formData.credentialType,
            value: formData.credentialValue,
          },
        };

        const result = await createHost(createData);
        if (onSuccess) {
          onSuccess(result);
        }
      }
    } catch (err) {
      console.error('Form submission error:', err);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    if (name === 'port') {
      setFormData(prev => ({
        ...prev,
        [name]: parseInt(value) || 22,
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value,
      }));
    }

    // Clear validation error for this field
    setValidationErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[name];
      return newErrors;
    });
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-6">
        {host ? 'Edit Host' : 'Register New SSH Host'}
      </h2>

      {/* Error message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex justify-between items-center">
            <p className="text-red-800">{error}</p>
            <button
              onClick={clearError}
              type="button"
              className="text-red-600 hover:text-red-800 font-semibold"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {/* Hostname */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Hostname or IP Address *
          </label>
          <input
            type="text"
            name="hostname"
            value={formData.hostname}
            onChange={handleChange}
            placeholder="server.example.com or 192.168.1.10"
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              validationErrors.hostname ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {validationErrors.hostname && (
            <p className="text-red-500 text-sm mt-1">{validationErrors.hostname}</p>
          )}
        </div>

        {/* Port and Username */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              SSH Port *
            </label>
            <input
              type="number"
              name="port"
              value={formData.port}
              onChange={handleChange}
              min="1"
              max="65535"
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.port ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {validationErrors.port && (
              <p className="text-red-500 text-sm mt-1">{validationErrors.port}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Username *
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="ubuntu, root, etc."
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                validationErrors.username ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {validationErrors.username && (
              <p className="text-red-500 text-sm mt-1">{validationErrors.username}</p>
            )}
          </div>
        </div>

        {/* Folder and Tags */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Folder
            </label>
            <input
              type="text"
              name="folder"
              value={formData.folder}
              onChange={handleChange}
              placeholder="e.g., production, development"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              name="tags"
              value={formData.tags}
              onChange={handleChange}
              placeholder="web, production, monitored"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Optional description for this host"
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Credential Type */}
        <div className="border-t pt-4">
          <h3 className="text-lg font-semibold mb-3">Authentication</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Credential Type
            </label>
            <select
              name="credentialType"
              value={formData.credentialType}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="password">Password</option>
              <option value="ssh_key">SSH Private Key</option>
            </select>
          </div>

          {/* Credential Value */}
          <div className="mt-3">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {formData.credentialType === 'password' ? 'Password' : 'Private Key'} {!host && '*'}
            </label>
            <textarea
              name="credentialValue"
              value={formData.credentialValue}
              onChange={handleChange}
              placeholder={
                formData.credentialType === 'password'
                  ? 'Enter SSH password'
                  : 'Paste your SSH private key (PEM format)'
              }
              rows={6}
              className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm ${
                validationErrors.credentialValue ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {validationErrors.credentialValue && (
              <p className="text-red-500 text-sm mt-1">{validationErrors.credentialValue}</p>
            )}
            {formData.credentialType === 'ssh_key' && (
              <p className="text-gray-500 text-xs mt-1">
                Private keys are encrypted and stored securely
              </p>
            )}
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex gap-3 pt-4 border-t">
          <button
            type="submit"
            disabled={isLoading}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Saving...' : host ? 'Update Host' : 'Register Host'}
          </button>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={isLoading}
              className="flex-1 bg-gray-200 text-gray-800 py-2 px-4 rounded-lg font-medium hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </form>
  );
};

export default HostForm;
