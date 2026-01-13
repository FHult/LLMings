/**
 * Ollama model management component
 */
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const API_BASE_URL = 'http://localhost:8000/api';

interface OllamaStatus {
  running: boolean;
  version?: string;
  error?: string;
  system_ram?: {
    total_gb: number;
    available_gb: number;
  };
}

interface ModelInfo {
  name: string;
  base_model?: string;
  ram_required?: number;
  can_run?: boolean;
  message?: string;
  suitability?: {
    general: number;
    coding: number;
    reasoning: number;
    creative: number;
  };
  supports_vision?: boolean;
  installed?: boolean;
}

export const OllamaManager: React.FC = () => {
  const [status, setStatus] = useState<OllamaStatus | null>(null);
  const [installedModels, setInstalledModels] = useState<ModelInfo[]>([]);
  const [recommendedModels, setRecommendedModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [pullStatus, setPullStatus] = useState<Record<string, string>>({});

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/ollama/status`);
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch Ollama status:', error);
      setStatus({ running: false, error: 'Failed to connect to backend' });
    }
  };

  const fetchInstalledModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/ollama/models`);
      const data = await response.json();
      setInstalledModels(data.models || []);
    } catch (error) {
      console.error('Failed to fetch installed models:', error);
    }
  };

  const fetchRecommendedModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/ollama/recommended`);
      const data = await response.json();
      setRecommendedModels(data.recommended || []);
    } catch (error) {
      console.error('Failed to fetch recommended models:', error);
    }
  };


  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchStatus(),
        fetchInstalledModels(),
        fetchRecommendedModels(),
      ]);
      setLoading(false);
    };

    loadData();
  }, []);

  const handlePullModel = async (modelName: string) => {
    setPullStatus((prev) => ({ ...prev, [modelName]: 'Pulling...' }));

    try {
      const response = await fetch(`${API_BASE_URL}/ollama/models/pull`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_name: modelName }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));

            if (data.error) {
              setPullStatus((prev) => ({ ...prev, [modelName]: `Error: ${data.error}` }));
              return;
            }

            if (data.status) {
              setPullStatus((prev) => ({ ...prev, [modelName]: data.status }));
            }
          }
        }
      }

      setPullStatus((prev) => ({ ...prev, [modelName]: 'Complete' }));
      await fetchInstalledModels();
    } catch (error) {
      setPullStatus((prev) => ({
        ...prev,
        [modelName]: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      }));
    }
  };


  const handleDeleteModel = async (modelName: string) => {
    try {
      await fetch(`${API_BASE_URL}/ollama/models/${encodeURIComponent(modelName)}`, {
        method: 'DELETE',
      });
      await fetchInstalledModels();
    } catch (error) {
      console.error('Failed to delete model:', error);
    }
  };

  const renderSuitability = (suitability?: Record<string, number>) => {
    if (!suitability) return null;

    const categories = [
      { key: 'general', label: 'General', emoji: '💬' },
      { key: 'coding', label: 'Coding', emoji: '💻' },
      { key: 'reasoning', label: 'Reasoning', emoji: '🧠' },
      { key: 'creative', label: 'Creative', emoji: '🎨' },
    ];

    return (
      <div className="grid grid-cols-2 gap-2 mt-2">
        {categories.map(({ key, label, emoji }) => (
          <div key={key} className="flex items-center gap-1 text-xs">
            <span>{emoji}</span>
            <span className="text-muted-foreground">{label}:</span>
            <span className="font-medium">{suitability[key]}/10</span>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="p-6 text-center text-muted-foreground">Loading Ollama status...</div>
    );
  }

  if (!status?.running) {
    return (
      <Card className="p-6">
        <div className="text-center space-y-4">
          <h3 className="text-lg font-semibold text-destructive">Ollama Not Running</h3>
          <p className="text-muted-foreground">{status?.error || 'Ollama service is not running'}</p>
          <div className="bg-muted p-4 rounded-md text-left">
            <p className="font-medium mb-2">To start Ollama:</p>
            <code className="block bg-background p-2 rounded">ollama serve</code>
            <p className="text-sm text-muted-foreground mt-2">
              Install Ollama from:{' '}
              <a href="https://ollama.ai" target="_blank" rel="noopener noreferrer" className="text-primary underline">
                https://ollama.ai
              </a>
            </p>
          </div>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">Ollama Status</h3>
            <p className="text-sm text-muted-foreground">Version: {status.version}</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium">Running</span>
            </div>
            {status.system_ram && (
              <p className="text-xs text-muted-foreground mt-1">
                RAM: {status.system_ram.available_gb.toFixed(1)} GB / {status.system_ram.total_gb.toFixed(1)} GB
                available
              </p>
            )}
          </div>
        </div>
      </Card>

      {/* Installed Models */}
      {installedModels.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3">Installed Models ({installedModels.length})</h3>
          <div className="space-y-2">
            {installedModels.map((model) => (
              <Card key={model.name} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{model.name}</span>
                      {model.supports_vision && (
                        <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-800 rounded">Vision</span>
                      )}
                      {model.can_run !== undefined && (
                        <span
                          className={`px-2 py-0.5 text-xs rounded ${
                            model.can_run ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {model.can_run ? 'Compatible' : 'Insufficient RAM'}
                        </span>
                      )}
                    </div>
                    {model.ram_required && (
                      <p className="text-sm text-muted-foreground mt-1">
                        Requires {model.ram_required} GB RAM {model.message && `• ${model.message}`}
                      </p>
                    )}
                    {renderSuitability(model.suitability)}
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteModel(model.name)}
                  >
                    Delete
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Models */}
      {recommendedModels.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3">Recommended Models for Your System</h3>
          <div className="space-y-2">
            {recommendedModels.map((model) => (
              <Card key={model.name} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{model.name}</span>
                      <span className="px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded">
                        {model.ram_required} GB RAM
                      </span>
                    </div>
                    {renderSuitability(model.suitability)}
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handlePullModel(model.name)}
                    disabled={!!pullStatus[model.name]}
                  >
                    {pullStatus[model.name] || 'Install'}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
