/**
 * Hosts Page - Main page for managing SSH hosts
 */

import React, { useState } from 'react';
import HostList from '@/components/hosts/HostList';
import HostForm from '@/components/hosts/HostForm';
import HostSearch from '@/components/hosts/HostSearch';
import { Host } from '@/hooks/useHosts';

export default function HostsPage() {
  const [showForm, setShowForm] = useState(false);
  const [selectedHost, setSelectedHost] = useState<Host | undefined>();
  const [searchFilters, setSearchFilters] = useState<any>({});
  const [refreshKey, setRefreshKey] = useState(0);

  const handleHostSelect = (host: Host) => {
    // In a real app, this might navigate to a terminal or connection view
    console.log('Selected host:', host);
  };

  const handleHostEdit = (host: Host) => {
    setSelectedHost(host);
    setShowForm(true);
  };

  const handleHostDelete = (hostId: string) => {
    // Refresh the list after deletion
    setRefreshKey(prev => prev + 1);
  };

  const handleFormSuccess = () => {
    setShowForm(false);
    setSelectedHost(undefined);
    setRefreshKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Page Header */}
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">SSH Hosts</h1>
          <button
            onClick={() => {
              setSelectedHost(undefined);
              setShowForm(!showForm);
            }}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            {showForm ? 'Cancel' : '+ Register New Host'}
          </button>
        </div>

        {/* Form Section */}
        {showForm && (
          <div className="mb-8">
            <HostForm
              host={selectedHost}
              onSuccess={handleFormSuccess}
              onCancel={() => {
                setShowForm(false);
                setSelectedHost(undefined);
              }}
            />
          </div>
        )}

        {/* Search and Filter Section */}
        <HostSearch
          onSearch={(query) => {
            setSearchFilters((prev: any) => ({ ...prev, search: query }));
          }}
          onFilterChange={(filters) => {
            setSearchFilters(filters);
          }}
        />

        {/* Hosts List Section */}
        <div key={refreshKey}>
          <HostList
            filters={searchFilters}
            onHostSelect={handleHostSelect}
            onHostEdit={handleHostEdit}
            onHostDelete={handleHostDelete}
          />
        </div>
      </div>
    </div>
  );
}
