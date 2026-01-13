import React, { useState, useEffect } from 'react';
import APIKeyModal from './APIKeyModal';

interface Provider {
  name: string;
  configured: boolean;
  displayName: string;
  status?: 'available' | 'quota_exceeded' | 'offline' | 'unknown';
  statusMessage?: string;
}

interface ProviderSelectorProps {
  selectedProviders: string[];
  onSelectionChange: (providers: string[]) => void;
  chair: string;
  onChairChange: (chair: string) => void;
}

const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google Gemini',
  grok: 'Grok',
  ollama: 'Ollama (Local)',
};

const PROVIDER_DESCRIPTIONS: Record<string, string> = {
  openai: 'GPT-4, GPT-4o - Industry leading models',
  anthropic: 'Claude - Long context, strong reasoning',
  google: 'Gemini - Free tier available',
  grok: 'Grok - X.AI models',
  ollama: 'Local LLMs - No cost, private',
};

export default function ProviderSelector({
  selectedProviders,
  onSelectionChange,
  chair,
  onChairChange,
}: ProviderSelectorProps) {
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

      // Extract providers object from API response
      const providersData = data.providers || data;

      const providerList: Provider[] = Object.keys(providersData).map((name) => ({
        name,
        configured: providersData[name].configured,
        displayName: PROVIDER_DISPLAY_NAMES[name] || name,
        status: 'unknown',
      }));

      setProviders(providerList);

      // If no providers selected yet, select all configured ones by default
      if (selectedProviders.length === 0) {
        const configuredProviders = providerList
          .filter((p) => p.configured)
          .map((p) => p.name);
        onSelectionChange(configuredProviders);

        // Set first configured provider as chair if not set or if current chair is not configured
        if (configuredProviders.length > 0) {
          const isChairConfigured = configuredProviders.includes(chair);
          if (!chair || !isChairConfigured) {
            // Prefer ollama as default chair if available, otherwise use first configured
            const defaultChair = configuredProviders.includes('ollama')
              ? 'ollama'
              : configuredProviders[0];
            onChairChange(defaultChair);
          }
        }
      } else {
        // Check if current chair is still configured, if not switch to a configured one
        const configuredProviders = providerList
          .filter((p) => p.configured)
          .map((p) => p.name);

        const isChairConfigured = configuredProviders.includes(chair);
        if (!isChairConfigured && configuredProviders.length > 0) {
          // Switch to a configured provider
          const defaultChair = configuredProviders.includes('ollama')
            ? 'ollama'
            : configuredProviders[0];
          onChairChange(defaultChair);
        }
      }
    } catch (error) {
      console.error('Failed to fetch providers:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleProvider = (providerName: string) => {
    const isSelected = selectedProviders.includes(providerName);
    let newSelection: string[];

    if (isSelected) {
      // Deselect
      newSelection = selectedProviders.filter((p) => p !== providerName);

      // If deselecting the chair, change chair to first remaining provider
      if (chair === providerName && newSelection.length > 0) {
        onChairChange(newSelection[0]);
      }
    } else {
      // Select
      newSelection = [...selectedProviders, providerName];
    }

    onSelectionChange(newSelection);
  };

  const selectAll = () => {
    const configuredProviders = providers
      .filter((p) => p.configured)
      .map((p) => p.name);
    onSelectionChange(configuredProviders);
  };

  const deselectAll = () => {
    onSelectionChange([]);
  };

  const handleChairChange = (providerName: string) => {
    // Ensure the chair is also selected as a provider
    if (!selectedProviders.includes(providerName)) {
      onSelectionChange([...selectedProviders, providerName]);
    }
    onChairChange(providerName);
  };

  if (loading) {
    return (
      <div className="provider-selector">
        <div className="loading">Loading providers...</div>
      </div>
    );
  }

  return (
    <div className="provider-selector">
      <div className="provider-selector-header">
        <h3>Select Council Members</h3>
        <div className="selection-actions">
          <button
            type="button"
            onClick={selectAll}
            className="btn-text"
            disabled={selectedProviders.length === providers.filter(p => p.configured).length}
          >
            Select All
          </button>
          <button
            type="button"
            onClick={deselectAll}
            className="btn-text"
            disabled={selectedProviders.length === 0}
          >
            Deselect All
          </button>
        </div>
      </div>

      <div className="provider-grid">
        {providers.map((provider) => {
          const isSelected = selectedProviders.includes(provider.name);
          const isChair = chair === provider.name;
          const isDisabled = !provider.configured;

          return (
            <div
              key={provider.name}
              className={`provider-card ${isSelected ? 'selected' : ''} ${
                isDisabled ? 'disabled' : ''
              } ${isChair ? 'chair' : ''}`}
            >
              <div className="provider-card-header">
                <label className="provider-checkbox">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleProvider(provider.name)}
                    disabled={isDisabled}
                  />
                  <span className="provider-name">{provider.displayName}</span>
                  {isChair && <span className="chair-badge">Chair</span>}
                </label>
              </div>

              <div className="provider-description">
                {PROVIDER_DESCRIPTIONS[provider.name] || 'AI Provider'}
              </div>

              {!provider.configured && provider.name !== 'ollama' && (
                <>
                  <div className="provider-status error">
                    <span className="status-icon">⚠️</span>
                    Not configured (API key missing)
                  </div>
                  <button
                    type="button"
                    onClick={() => setConfigureProvider(provider.name)}
                    className="btn-configure"
                  >
                    🔑 Add API Key
                  </button>
                </>
              )}

              {provider.configured && isSelected && (
                <button
                  type="button"
                  onClick={() => handleChairChange(provider.name)}
                  className={`btn-chair ${isChair ? 'active' : ''}`}
                  disabled={isChair}
                >
                  {isChair ? '★ Chair' : 'Make Chair'}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {selectedProviders.length === 0 && (
        <div className="provider-warning">
          <span className="warning-icon">⚠️</span>
          Please select at least one provider to participate in the council.
        </div>
      )}

      {selectedProviders.length > 0 && (
        <div className="provider-summary">
          <strong>{selectedProviders.length}</strong> provider
          {selectedProviders.length !== 1 ? 's' : ''} selected
          {chair && (
            <>
              {' • '}
              <strong>{PROVIDER_DISPLAY_NAMES[chair]}</strong> as chair
            </>
          )}
        </div>
      )}

      {/* API Key Configuration Modal */}
      {configureProvider && (
        <APIKeyModal
          provider={configureProvider}
          displayName={PROVIDER_DISPLAY_NAMES[configureProvider] || configureProvider}
          isOpen={true}
          onClose={() => setConfigureProvider(null)}
          onSuccess={() => {
            // Show success message and prompt to restart
            alert(
              'API key saved successfully! Please restart the backend server for changes to take effect.\n\n' +
              'From the backend directory, run:\n' +
              'source venv/bin/activate && uvicorn app.main:app --reload'
            );
            // Refetch providers to update UI
            fetchProviders();
          }}
        />
      )}

      <style>{`
        .provider-selector {
          margin: 1.5rem 0;
        }

        .provider-selector-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .provider-selector-header h3 {
          margin: 0;
          font-size: 1.1rem;
          color: #e0e0e0;
        }

        .selection-actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn-text {
          background: none;
          border: none;
          color: #4a9eff;
          cursor: pointer;
          font-size: 0.875rem;
          padding: 0.25rem 0.5rem;
        }

        .btn-text:hover:not(:disabled) {
          color: #6bb0ff;
          text-decoration: underline;
        }

        .btn-text:disabled {
          color: #666;
          cursor: not-allowed;
        }

        .provider-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .provider-card {
          background: #1e1e1e;
          border: 2px solid #333;
          border-radius: 8px;
          padding: 1rem;
          transition: all 0.2s ease;
        }

        .provider-card.selected {
          border-color: #4a9eff;
          background: #1a2838;
        }

        .provider-card.chair {
          border-color: #f59e0b;
          background: #2d2416;
        }

        .provider-card.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .provider-card:not(.disabled):hover {
          border-color: #4a9eff;
          transform: translateY(-2px);
        }

        .provider-card-header {
          margin-bottom: 0.5rem;
        }

        .provider-checkbox {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
          user-select: none;
        }

        .provider-checkbox input[type="checkbox"] {
          width: 18px;
          height: 18px;
          cursor: pointer;
        }

        .provider-checkbox input[type="checkbox"]:disabled {
          cursor: not-allowed;
        }

        .provider-name {
          font-weight: 600;
          color: #e0e0e0;
          font-size: 1rem;
        }

        .chair-badge {
          background: #f59e0b;
          color: #000;
          padding: 0.125rem 0.5rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 600;
          margin-left: auto;
        }

        .provider-description {
          color: #999;
          font-size: 0.875rem;
          margin-bottom: 0.75rem;
        }

        .provider-status {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem;
          border-radius: 4px;
          font-size: 0.875rem;
          margin-top: 0.5rem;
        }

        .provider-status.error {
          background: rgba(239, 68, 68, 0.1);
          color: #ef4444;
        }

        .status-icon {
          font-size: 1rem;
        }

        .btn-configure {
          width: 100%;
          margin-top: 0.75rem;
          padding: 0.5rem;
          background: #2a2a2a;
          border: 1px solid #4a9eff;
          color: #4a9eff;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.875rem;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .btn-configure:hover {
          background: #4a9eff;
          color: #000;
        }

        .btn-chair {
          width: 100%;
          margin-top: 0.75rem;
          padding: 0.5rem;
          background: #333;
          border: 1px solid #4a9eff;
          color: #4a9eff;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.875rem;
          font-weight: 500;
          transition: all 0.2s ease;
        }

        .btn-chair:hover:not(:disabled) {
          background: #4a9eff;
          color: #000;
        }

        .btn-chair.active {
          background: #f59e0b;
          border-color: #f59e0b;
          color: #000;
          cursor: default;
        }

        .btn-chair:disabled {
          cursor: not-allowed;
        }

        .provider-warning {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 1rem;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid #ef4444;
          border-radius: 6px;
          color: #ef4444;
          font-size: 0.875rem;
        }

        .warning-icon {
          font-size: 1.25rem;
        }

        .provider-summary {
          padding: 0.75rem 1rem;
          background: #1a2838;
          border: 1px solid #4a9eff;
          border-radius: 6px;
          color: #e0e0e0;
          font-size: 0.875rem;
        }

        .loading {
          text-align: center;
          padding: 2rem;
          color: #999;
        }
      `}</style>
    </div>
  );
}
