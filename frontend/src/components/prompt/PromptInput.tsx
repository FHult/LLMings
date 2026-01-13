import { useState } from 'react';
import { useSessionStore } from '@/store/sessionStore';
import { useProvidersStore } from '@/store/providersStore';
import { useUIStore } from '@/store/uiStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ModelSelector } from './ModelSelector';
import { FileUpload } from './FileUpload';
import ProviderSelector from '@/components/ProviderSelector';
import type { SessionConfig, Template, Preset, FileAttachment } from '@/types';

export function PromptInput() {
  const [prompt, setPrompt] = useState('');
  const [chair, setChair] = useState('anthropic');
  const [selectedProviders, setSelectedProviders] = useState<string[]>([]);
  const [iterations, setIterations] = useState(3);
  const [template, setTemplate] = useState<Template>('balanced');
  const [preset, setPreset] = useState<Preset>('balanced');
  const [autopilot, setAutopilot] = useState(false);
  const [files, setFiles] = useState<FileAttachment[]>([]);

  const { startSession, status, error } = useSessionStore();
  const isStreaming = status === 'running';
  const { providers, getModelConfigs } = useProvidersStore();
  const { showModelSelector, toggleModelSelector, showAdvancedOptions, toggleAdvancedOptions } = useUIStore();

  const configuredProviders = Object.keys(providers).filter(
    (name) => providers[name]?.configured
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!prompt.trim()) {
      return;
    }

    if (selectedProviders.length === 0) {
      alert('Please select at least one provider');
      return;
    }

    const config: SessionConfig = {
      prompt: prompt.trim(),
      chair,
      selected_providers: selectedProviders,
      iterations,
      template,
      preset,
      autopilot,
      model_configs: getModelConfigs(),
      files: files.length > 0 ? files : undefined,
    };

    await startSession(config);

    // Clear files after submission
    if (files.length > 0) {
      setFiles([]);
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Create Council Session</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Prompt Input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Prompt
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask your question or describe what you'd like the AI council to discuss..."
                rows={4}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                disabled={isStreaming}
              />
            </div>

            {/* File Upload */}
            <FileUpload files={files} onFilesChange={setFiles} disabled={isStreaming} />

            {/* Provider Selection */}
            <ProviderSelector
              selectedProviders={selectedProviders}
              onSelectionChange={setSelectedProviders}
              chair={chair}
              onChairChange={setChair}
            />

            {/* Main Controls */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Iterations */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Iterations
                </label>
                <select
                  value={iterations}
                  onChange={(e) => setIterations(Number(e.target.value))}
                  className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  disabled={isStreaming}
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                    <option key={n} value={n}>
                      {n} {n === 1 ? 'iteration' : 'iterations'}
                    </option>
                  ))}
                </select>
              </div>

              {/* Preset */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Preset
                </label>
                <select
                  value={preset}
                  onChange={(e) => setPreset(e.target.value as Preset)}
                  className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  disabled={isStreaming}
                >
                  <option value="creative">Creative (0.9 temp)</option>
                  <option value="balanced">Balanced (0.7 temp)</option>
                  <option value="precise">Precise (0.3 temp)</option>
                </select>
              </div>
            </div>

            {/* Advanced Options Toggle */}
            <div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={toggleAdvancedOptions}
                className="text-indigo-600"
              >
                {showAdvancedOptions ? '▼' : '▶'} Advanced Options
              </Button>
            </div>

            {/* Advanced Options */}
            {showAdvancedOptions && (
              <div className="space-y-4 border-t pt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Merge Template
                  </label>
                  <select
                    value={template}
                    onChange={(e) => setTemplate(e.target.value as Template)}
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    disabled={isStreaming}
                  >
                    <option value="analytical">Analytical</option>
                    <option value="creative">Creative</option>
                    <option value="technical">Technical</option>
                    <option value="balanced">Balanced</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="autopilot"
                    checked={autopilot}
                    onChange={(e) => setAutopilot(e.target.checked)}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    disabled={isStreaming}
                  />
                  <label htmlFor="autopilot" className="text-sm text-gray-700">
                    Autopilot mode (run all iterations automatically)
                  </label>
                </div>
              </div>
            )}

            {/* Model Selection Toggle */}
            <div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={toggleModelSelector}
                className="text-indigo-600"
              >
                {showModelSelector ? '▼' : '▶'} Model Selection
              </Button>
            </div>

            {/* Error Display */}
            {error && (
              <div className="rounded-md bg-red-50 border border-red-200 p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Submit Button */}
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-500">
                {configuredProviders.length} provider{configuredProviders.length !== 1 ? 's' : ''} configured
              </p>
              <Button type="submit" disabled={isStreaming || !prompt.trim()}>
                {isStreaming ? (
                  <>
                    <span className="animate-spin mr-2">⚙️</span>
                    Creating Session...
                  </>
                ) : (
                  'Start Council Session'
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Model Selector */}
      {showModelSelector && <ModelSelector />}
    </div>
  );
}
