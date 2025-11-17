import React from 'react';
import { createRoot } from 'react-dom/client';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import App from './App';

// Initialize Office.js before rendering React app
Office.onReady((info) => {
  if (info.host === Office.HostType.Word) {
    const container = document.getElementById('root');
    if (container) {
      const root = createRoot(container);
      root.render(
        <React.StrictMode>
          <FluentProvider theme={webLightTheme}>
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
        <div style="padding: 20px; text-align: center;">
          <h2>AI Legal Assistant</h2>
          <p>This add-in is designed to run in Microsoft Word.</p>
          <p>Please open this add-in from within Word to use its features.</p>
        </div>
      `;
    }
  }
});
