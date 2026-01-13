import React, { useState, useEffect } from 'react';
import APIKeyModal from './APIKeyModal';

interface Provider {
  name: string;
  configured: boolean;
  displayName: string;
  default_model: string;
  available_models: string[];
}

const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google Gemini',
  grok: 'Grok',
  ollama: 'Ollama (Local)',
};

const PROVIDER_DESCRIPTIONS: Record<string, string> = {
  openai: 'GPT-4, GPT-4o - Industry leading models with strong reasoning',
  anthropic: 'Claude - Long context window, excellent for complex analysis',
  google: 'Gemini - Free tier available, multimodal capabilities',
  grok: 'Grok - X.AI models with real-time information',
  ollama: 'Local LLMs - No cost, complete privacy, runs on your machine',
};

const PROVIDER_DOCS: Record<string, string> = {
  openai: 'https://platform.openai.com/docs',
  anthropic: 'https://docs.anthropic.com/',
  google: 'https://ai.google.dev/docs',
  grok: 'https://docs.x.ai/',
  ollama: 'https://ollama.ai/',
};

export default function ProviderSettings() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [configureProvider, setConfigureProvider] = useState<string | null>(null);

  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/providers');
      const data = await response.json();
      const providersData = data.providers || data;

      const providerList: Provider[] = Object.keys(providersData).map((name) => ({
        name,
        configured: providersData[name].configured,
        displayName: PROVIDER_DISPLAY_NAMES[name] || name,
        default_model: providersData[name].default_model,
        available_models: providersData[name].available_models || [],
      }));

      setProviders(providerList);
    } catch (error) {
      console.error('Failed to fetch providers:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="provider-settings">
        <div className="loading">Loading provider settings...</div>
      </div>
    );
  }

  return (
    <div className="provider-settings">
      <div className="settings-header">
        <h2>Provider Settings</h2>
        <p className="subtitle">Manage API keys and provider configurations</p>
      </div>

      <div className="providers-grid">
        {providers.map((provider) => (
          <div
            key={provider.name}
            className={`provider-settings-card ${provider.configured ? 'configured' : 'unconfigured'}`}
          >
            <div className="provider-header">
              <div className="provider-title">
                <h3>{provider.displayName}</h3>
                {provider.configured ? (
                  <span className="status-badge configured">✓ Configured</span>
                ) : (
                  <span className="status-badge unconfigured">⚠ Not Configured</span>
                )}
              </div>
              <div className="provider-description">
                {PROVIDER_DESCRIPTIONS[provider.name] || 'AI Provider'}
              </div>
            </div>

            <div className="provider-details">
              <div className="detail-row">
                <span className="detail-label">Default Model:</span>
                <span className="detail-value">{provider.default_model}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Available Models:</span>
                <span className="detail-value">{provider.available_models.length} models</span>
              </div>
            </div>

            <div className="provider-actions">
              {provider.name !== 'ollama' && (
                <button
                  type="button"
                  onClick={() => setConfigureProvider(provider.name)}
                  className={`btn-action ${provider.configured ? 'btn-secondary' : 'btn-primary'}`}
                >
                  {provider.configured ? '🔑 Update API Key' : '🔑 Add API Key'}
                </button>
              )}
              {PROVIDER_DOCS[provider.name] && (
                <a
                  href={PROVIDER_DOCS[provider.name]}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-action btn-link"
                >
                  📚 Documentation
                </a>
              )}
            </div>

            {!provider.configured && provider.name !== 'ollama' && (
              <div className="warning-box">
                <span className="warning-icon">ℹ️</span>
                <span>This provider requires an API key to be used in council sessions.</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="info-section">
        <h3>About Providers</h3>
        <div className="info-grid">
          <div className="info-card">
            <h4>🔐 API Key Security</h4>
            <p>
              API keys are stored securely in your local .env file and never sent to external
              servers except when making requests to the respective AI providers.
            </p>
          </div>
          <div className="info-card">
            <h4>💰 Pricing</h4>
            <p>
              Each provider has different pricing models. Check their documentation for current
              rates. Ollama is completely free as it runs locally on your machine.
            </p>
          </div>
          <div className="info-card">
            <h4>🔄 Backend Restart Required</h4>
            <p>
              After adding or updating an API key, you must restart the backend server for the
              changes to take effect.
            </p>
          </div>
        </div>
      </div>

      {/* API Key Configuration Modal */}
      {configureProvider && (
        <APIKeyModal
          provider={configureProvider}
          displayName={PROVIDER_DISPLAY_NAMES[configureProvider] || configureProvider}
          isOpen={true}
          onClose={() => setConfigureProvider(null)}
          onSuccess={() => {
            alert(
              'API key saved successfully! Please restart the backend server for changes to take effect.\n\n' +
              'From the backend directory, run:\n' +
              'source venv/bin/activate && uvicorn app.main:app --reload'
            );
            fetchProviders();
            setConfigureProvider(null);
          }}
        />
      )}

      <style>{`
        .provider-settings {
          padding: 2rem;
          max-width: 1200px;
          margin: 0 auto;
        }

        .settings-header {
          margin-bottom: 2rem;
        }

        .settings-header h2 {
          margin: 0 0 0.5rem 0;
          font-size: 2rem;
          color: #e0e0e0;
        }

        .subtitle {
          margin: 0;
          color: #999;
          font-size: 1rem;
        }

        .providers-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
          gap: 1.5rem;
          margin-bottom: 3rem;
        }

        .provider-settings-card {
          background: #1e1e1e;
          border: 2px solid #333;
          border-radius: 12px;
          padding: 1.5rem;
          transition: all 0.2s;
        }

        .provider-settings-card.configured {
          border-color: #4a9eff;
        }

        .provider-settings-card.unconfigured {
          border-color: #ef4444;
          opacity: 0.8;
        }

        .provider-settings-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .provider-header {
          margin-bottom: 1.5rem;
        }

        .provider-title {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 0.75rem;
        }

        .provider-title h3 {
          margin: 0;
          font-size: 1.25rem;
          color: #e0e0e0;
        }

        .status-badge {
          padding: 0.25rem 0.75rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 600;
        }

        .status-badge.configured {
          background: rgba(34, 197, 94, 0.2);
          color: #22c55e;
        }

        .status-badge.unconfigured {
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
        }

        .provider-description {
          color: #999;
          font-size: 0.875rem;
          line-height: 1.5;
        }

        .provider-details {
          background: rgba(74, 158, 255, 0.05);
          border-radius: 6px;
          padding: 1rem;
          margin-bottom: 1rem;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          padding: 0.25rem 0;
        }

        .detail-row:not(:last-child) {
          margin-bottom: 0.5rem;
        }

        .detail-label {
          color: #999;
          font-size: 0.875rem;
        }

        .detail-value {
          color: #e0e0e0;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .provider-actions {
          display: flex;
          gap: 0.75rem;
          margin-bottom: 1rem;
        }

        .btn-action {
          flex: 1;
          padding: 0.625rem 1rem;
          border-radius: 6px;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          text-decoration: none;
          text-align: center;
          display: inline-block;
        }

        .btn-primary {
          background: #4a9eff;
          border: 1px solid #4a9eff;
          color: #000;
        }

        .btn-primary:hover {
          background: #6bb0ff;
          border-color: #6bb0ff;
          transform: translateY(-1px);
        }

        .btn-secondary {
          background: #333;
          border: 1px solid #4a9eff;
          color: #4a9eff;
        }

        .btn-secondary:hover {
          background: rgba(74, 158, 255, 0.1);
          border-color: #6bb0ff;
        }

        .btn-link {
          background: transparent;
          border: 1px solid #666;
          color: #999;
        }

        .btn-link:hover {
          border-color: #4a9eff;
          color: #4a9eff;
        }

        .warning-box {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 6px;
          color: #ef4444;
          font-size: 0.8125rem;
        }

        .warning-icon {
          font-size: 1rem;
          flex-shrink: 0;
        }

        .info-section {
          margin-top: 3rem;
          padding-top: 2rem;
          border-top: 2px solid #333;
        }

        .info-section h3 {
          margin: 0 0 1.5rem 0;
          font-size: 1.5rem;
          color: #e0e0e0;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 1.5rem;
        }

        .info-card {
          background: rgba(74, 158, 255, 0.05);
          border: 1px solid rgba(74, 158, 255, 0.2);
          border-radius: 8px;
          padding: 1.5rem;
        }

        .info-card h4 {
          margin: 0 0 0.75rem 0;
          font-size: 1rem;
          color: #4a9eff;
        }

        .info-card p {
          margin: 0;
          color: #b3d4ff;
          font-size: 0.875rem;
          line-height: 1.6;
        }

        .loading {
          text-align: center;
          padding: 3rem;
          color: #999;
          font-size: 1.125rem;
        }
      `}</style>
    </div>
  );
}
