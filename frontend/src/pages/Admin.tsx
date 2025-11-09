/**
 * Admin panel page for system administration.
 */

import React, { useState } from 'react';
import { useAdmin } from '../hooks/useAdmin';
import { UserManagement } from '../components/admin/UserManagement';
import { SessionManager } from '../components/admin/SessionManager';
import { OIDCProviderSettings } from '../components/admin/OIDCProviderSettings';

type AdminTab = 'users' | 'sessions' | 'oidc';

export const AdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AdminTab>('users');
  const {
    users,
    usersLoading,
    usersError,
    listUsers,
    sessions,
    sessionsLoading,
    sessionsError,
    listSessions,
    deleteSession,
    providers,
    providersLoading,
    providersError,
    listProviders,
    createProvider,
    updateProvider,
    deleteProvider,
  } = useAdmin();

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Admin Panel</h1>
          <p className="text-gray-600">Manage users, sessions, and system settings</p>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2 font-medium border-b-2 ${
              activeTab === 'users'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Users
          </button>
          <button
            onClick={() => setActiveTab('sessions')}
            className={`px-4 py-2 font-medium border-b-2 ${
              activeTab === 'sessions'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            Sessions
          </button>
          <button
            onClick={() => setActiveTab('oidc')}
            className={`px-4 py-2 font-medium border-b-2 ${
              activeTab === 'oidc'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            OIDC Providers
          </button>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'users' && (
            <UserManagement
              users={users}
              isLoading={usersLoading}
              error={usersError}
              onRefresh={listUsers}
            />
          )}

          {activeTab === 'sessions' && (
            <SessionManager
              sessions={sessions}
              isLoading={sessionsLoading}
              error={sessionsError}
              onRefresh={listSessions}
              onDeleteSession={deleteSession}
            />
          )}

          {activeTab === 'oidc' && (
            <OIDCProviderSettings
              providers={providers}
              isLoading={providersLoading}
              error={providersError}
              onRefresh={listProviders}
              onCreate={createProvider}
              onUpdate={updateProvider}
              onDelete={deleteProvider}
            />
          )}
        </div>
      </div>
    </div>
  );
};
