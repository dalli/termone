/**
 * Dashboard Page - Overview of infrastructure and quick statistics
 */

import React from 'react';
import Dashboard from '@/components/common/Dashboard';

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <Dashboard />
      </div>
    </div>
  );
}
