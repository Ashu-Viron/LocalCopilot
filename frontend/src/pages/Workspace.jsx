import React, { useEffect, useState } from 'react';
import App from '../App';
import api from '../services/api';

export default function Workspace() {
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Initialize workspace on mount
    const initializeWorkspace = async () => {
      try {
        // Test backend connection
        const health = await api.getSystemHealth();
        
        if (health && health.status === 'healthy') {
          setIsReady(true);
        } else {
          setError('Backend service is not responding');
        }
      } catch (err) {
        console.error('Workspace initialization error:', err);
        setError(`Failed to connect to backend: ${err.message}`);
      }
    };

    initializeWorkspace();
  }, []);

  if (error) {
    return (
      <div className="h-screen w-full bg-dark-900 text-dark-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold mb-2">Connection Error</h1>
          <p className="text-dark-400 mb-4">{error}</p>
          <p className="text-sm text-dark-500">
            Make sure the backend server is running on port 8000
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  if (!isReady) {
    return (
      <div className="h-screen w-full bg-dark-900 text-dark-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-dark-600 border-t-blue-400 rounded-full animate-spin mx-auto mb-4"></div>
          <h1 className="text-lg font-semibold mb-2">Initializing Workspace</h1>
          <p className="text-dark-400 text-sm">Connecting to backend server...</p>
        </div>
      </div>
    );
  }

  return <App />;
}
