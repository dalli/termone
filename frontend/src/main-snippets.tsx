/**
 * Main entry point for the Snippets page.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import { SnippetsPage } from './pages/Snippets';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SnippetsPage />
  </React.StrictMode>,
);
