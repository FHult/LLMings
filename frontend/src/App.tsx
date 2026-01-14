import { useEffect, useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { useSessionStore } from '@/store/sessionStore';
import { useProvidersStore } from '@/store/providersStore';
import { sessionApi } from '@/lib/api';
import { PromptInput } from '@/components/prompt/PromptInput';
import { LiveSession } from '@/components/session/LiveSession';
import ProviderSettings from '@/components/ProviderSettings';
import { ErrorBoundary } from '@/components/ErrorBoundary';

type TabType = 'council' | 'settings';

function App() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [activeTab, setActiveTab] = useState<TabType>('council');
  const { status: sessionStatus } = useSessionStore();
  const { loadProviders } = useProvidersStore();

  // Test backend connection and load providers on mount
  useEffect(() => {
    const testBackend = async () => {
      try {
        await sessionApi.testConnection();
        setBackendStatus('connected');
      } catch (error) {
        setBackendStatus('error');
      }
    };

    testBackend();
    loadProviders();
  }, [loadProviders]);

  return (
    <ErrorBoundary>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#363636',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#10b981',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">LLMings</h1>
              <p className="text-sm text-gray-600">Create a council of AI models to discuss your question and build consensus through iterations</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 text-sm">
                {backendStatus === 'checking' && (
                  <span className="text-gray-500">⚙️ Checking...</span>
                )}
                {backendStatus === 'connected' && (
                  <span className="text-green-600">✓ Backend Connected</span>
                )}
                {backendStatus === 'error' && (
                  <span className="text-red-600">✗ Backend Offline</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      {backendStatus === 'connected' && (
        <div className="border-b bg-white">
          <div className="container mx-auto px-4">
            <div className="flex gap-1">
              <button
                onClick={() => {
                  setActiveTab('council');
                  // Refresh providers when switching to council tab to pick up any Ollama model changes
                  loadProviders();
                }}
                className={`px-6 py-3 font-medium border-b-2 transition-colors ${
                  activeTab === 'council'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                Council Session
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`px-6 py-3 font-medium border-b-2 transition-colors ${
                  activeTab === 'settings'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                Provider Settings
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {backendStatus === 'error' ? (
          <div className="max-w-2xl mx-auto">
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-red-900 mb-4">
                Backend Not Running
              </h2>
              <p className="text-red-700 mb-4">
                The HiveCouncil backend server is not running. Please start it to use the application.
              </p>
              <div className="bg-white rounded border border-red-200 p-4 font-mono text-sm">
                <p className="text-gray-600 mb-2">Start the backend:</p>
                <code className="text-gray-900">
                  cd backend && source venv/bin/activate && uvicorn app.main:app --reload
                </code>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Council Tab */}
            {activeTab === 'council' && (
              <div className="max-w-4xl mx-auto space-y-6">
                {/* Info Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white rounded-lg shadow-sm border p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">🤖 Multi-Provider</h3>
                    <p className="text-sm text-gray-600">
                      OpenAI, Anthropic, Google, Grok, and Ollama work together
                    </p>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm border p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">🎯 Model Selection</h3>
                    <p className="text-sm text-gray-600">
                      Choose specific models for each provider
                    </p>
                  </div>
                  <div className="bg-white rounded-lg shadow-sm border p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">🔄 Iterative</h3>
                    <p className="text-sm text-gray-600">
                      Refine consensus through multiple cycles
                    </p>
                  </div>
                </div>

                {/* Prompt Input */}
                <PromptInput />

                {/* Live Session Display */}
                <LiveSession />
              </div>
            )}

            {/* Provider Settings Tab */}
            {activeTab === 'settings' && (
              <div className="max-w-6xl mx-auto">
                <ProviderSettings />
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t bg-white/80 backdrop-blur-sm mt-12">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-gray-600">
          <p>LLMings - Built with React, FastAPI, and AI</p>
          <p className="mt-1">
            <a
              href="https://github.com/FHult/HiveCouncil"
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-700"
            >
              View on GitHub
            </a>
          </p>
        </div>
      </footer>
      </div>
    </ErrorBoundary>
  );
}

export default App;
