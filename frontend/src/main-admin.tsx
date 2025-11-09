/**
 * Main entry point for the Admin panel.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { AdminPage } from './pages/Admin';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AdminPage />
  </React.StrictMode>,
);
