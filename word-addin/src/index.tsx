import React from 'react';
import { createRoot } from 'react-dom/client';
import { FluentProvider } from '@fluentui/react-components';
import App from './App';
import { cirillaTheme } from './theme';

// Initialize Office.js before rendering React app
Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    const container = document.getElementById('root');
    if (container) {
      const root = createRoot(container);
      root.render(
        <React.StrictMode>
          <FluentProvider theme={cirillaTheme}>
            <App />
          </FluentProvider>
        </React.StrictMode>
      );
    }
  } else {
    // Not running in Word
    const container = document.getElementById('root');
    if (container) {
      container.innerHTML = `
        <div style="padding: 20px; text-align: center; background: linear-gradient(to bottom right, #FFFAEB, #FEF3C7, #FDE68A); min-height: 100vh; font-family: 'Segoe UI', sans-serif;">
          <div style="max-width: 400px; margin: 100px auto; padding: 32px; background: rgba(254, 243, 199, 0.7); backdrop-filter: blur(10px); border-radius: 16px; box-shadow: 0 4px 8px rgba(217, 119, 6, 0.12);">
            <h2 style="color: #78350F; margin-bottom: 16px;">Cirilla AI Legal Assistant</h2>
            <p style="color: #92400E; margin-bottom: 12px;">This add-in is designed to run in Microsoft Word.</p>
            <p style="color: #92400E;">Please open this add-in from within Word to use its features.</p>
          </div>
        </div>
      `;
    }
  }
});
