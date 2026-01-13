import React, { useState } from 'react';

interface APIKeyModalProps {
  provider: string;
  displayName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const API_KEY_DOCS: Record<string, { url: string; description: string }> = {
  openai: {
    url: 'https://platform.openai.com/api-keys',
    description: 'Create an API key from your OpenAI dashboard',
  },
  anthropic: {
    url: 'https://console.anthropic.com/settings/keys',
    description: 'Get your API key from Anthropic Console',
  },
  google: {
    url: 'https://ai.google.dev/gemini-api/docs/api-key',
    description: 'Get a free Gemini API key from Google AI Studio',
  },
  grok: {
    url: 'https://x.ai/',
    description: 'Get API access from X.AI',
  },
};

export default function APIKeyModal({
  provider,
  displayName,
  isOpen,
  onClose,
  onSuccess,
}: APIKeyModalProps) {
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);

  const docs = API_KEY_DOCS[provider];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!apiKey.trim()) {
      setError('Please enter an API key');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/config/api-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider,
          api_key: apiKey.trim(),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to save API key');
      }

      // Success!
      onSuccess();
      onClose();
      setApiKey('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save API key');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Configure {displayName}</h2>
          <button className="close-button" onClick={onClose} disabled={loading}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {docs && (
              <div className="info-box">
                <p className="info-text">
                  {docs.description}
                </p>
                <a
                  href={docs.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="docs-link"
                >
                  Get API Key →
                </a>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="api-key">API Key</label>
              <div className="input-with-toggle">
                <input
                  id="api-key"
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={`Enter your ${displayName} API key`}
                  disabled={loading}
                  autoComplete="off"
                  className="api-key-input"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="toggle-visibility"
                  tabIndex={-1}
                >
                  {showKey ? '🙈' : '👁️'}
                </button>
              </div>
            </div>

            {error && (
              <div className="error-message">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}

            <div className="warning-box">
              <span className="warning-icon">ℹ️</span>
              <div>
                <strong>Note:</strong> The API key will be saved to your{' '}
                <code>.env</code> file. You'll need to restart the backend server
                for the changes to take effect.
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button type="submit" disabled={loading || !apiKey.trim()} className="btn-primary">
              {loading ? 'Saving...' : 'Save API Key'}
            </button>
          </div>
        </form>
      </div>

      <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.75);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          padding: 1rem;
        }

        .modal-content {
          background: #1e1e1e;
          border-radius: 12px;
          max-width: 500px;
          width: 100%;
          max-height: 90vh;
          overflow-y: auto;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem;
          border-bottom: 1px solid #333;
        }

        .modal-header h2 {
          margin: 0;
          font-size: 1.5rem;
          color: #e0e0e0;
        }

        .close-button {
          background: none;
          border: none;
          color: #999;
          font-size: 2rem;
          cursor: pointer;
          padding: 0;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
          transition: all 0.2s;
        }

        .close-button:hover:not(:disabled) {
          background: #333;
          color: #fff;
        }

        .close-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .modal-body {
          padding: 1.5rem;
        }

        .info-box {
          background: rgba(74, 158, 255, 0.1);
          border: 1px solid rgba(74, 158, 255, 0.3);
          border-radius: 6px;
          padding: 1rem;
          margin-bottom: 1.5rem;
        }

        .info-text {
          margin: 0 0 0.75rem 0;
          color: #b3d4ff;
          font-size: 0.875rem;
        }

        .docs-link {
          display: inline-flex;
          align-items: center;
          color: #4a9eff;
          text-decoration: none;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .docs-link:hover {
          color: #6bb0ff;
          text-decoration: underline;
        }

        .form-group {
          margin-bottom: 1rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          color: #e0e0e0;
          font-weight: 500;
          font-size: 0.875rem;
        }

        .input-with-toggle {
          position: relative;
          display: flex;
          align-items: center;
        }

        .api-key-input {
          flex: 1;
          background: #2a2a2a;
          border: 1px solid #444;
          color: #e0e0e0;
          padding: 0.75rem;
          padding-right: 3rem;
          border-radius: 6px;
          font-size: 0.875rem;
          font-family: 'Monaco', 'Courier New', monospace;
          transition: border-color 0.2s;
        }

        .api-key-input:focus {
          outline: none;
          border-color: #4a9eff;
        }

        .api-key-input:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .toggle-visibility {
          position: absolute;
          right: 0.5rem;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 1.25rem;
          padding: 0.25rem;
          opacity: 0.7;
          transition: opacity 0.2s;
        }

        .toggle-visibility:hover {
          opacity: 1;
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 6px;
          color: #ef4444;
          font-size: 0.875rem;
          margin-bottom: 1rem;
        }

        .error-icon {
          font-size: 1.125rem;
        }

        .warning-box {
          display: flex;
          gap: 0.75rem;
          padding: 1rem;
          background: rgba(245, 158, 11, 0.1);
          border: 1px solid rgba(245, 158, 11, 0.3);
          border-radius: 6px;
          color: #fbbf24;
          font-size: 0.875rem;
          line-height: 1.5;
        }

        .warning-icon {
          font-size: 1.125rem;
          flex-shrink: 0;
        }

        .warning-box code {
          background: rgba(0, 0, 0, 0.3);
          padding: 0.125rem 0.375rem;
          border-radius: 3px;
          font-family: 'Monaco', 'Courier New', monospace;
          font-size: 0.8125rem;
        }

        .modal-footer {
          display: flex;
          justify-content: flex-end;
          gap: 0.75rem;
          padding: 1.5rem;
          border-top: 1px solid #333;
        }

        .btn-secondary,
        .btn-primary {
          padding: 0.625rem 1.25rem;
          border-radius: 6px;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          border: none;
        }

        .btn-secondary {
          background: #333;
          color: #e0e0e0;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #444;
        }

        .btn-primary {
          background: #4a9eff;
          color: #000;
        }

        .btn-primary:hover:not(:disabled) {
          background: #6bb0ff;
        }

        .btn-secondary:disabled,
        .btn-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}
