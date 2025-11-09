import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
  showSidebar?: boolean;
}

export const Layout: React.FC<LayoutProps> = ({ children, showSidebar = true }) => {
  return (
    <div className="flex h-screen bg-gray-100">
      {showSidebar && (
        <nav className="w-64 bg-gray-900 text-white p-6">
          <h1 className="text-2xl font-bold mb-8">Termone</h1>
          <ul className="space-y-4">
            <li><a href="/dashboard" className="hover:text-gray-300">Dashboard</a></li>
            <li><a href="/hosts" className="hover:text-gray-300">Hosts</a></li>
            <li><a href="/terminal" className="hover:text-gray-300">Terminal</a></li>
            <li><a href="/files" className="hover:text-gray-300">Files</a></li>
            <li><a href="/stats" className="hover:text-gray-300">Stats</a></li>
          </ul>
        </nav>
      )}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
};
