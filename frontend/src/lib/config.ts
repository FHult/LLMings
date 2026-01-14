/**
 * Application configuration
 * Centralized configuration for API URLs and other settings
 */

export const config = {
  // API Base URL - defaults to localhost:8000 if not set
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',

  // API endpoint paths
  api: {
    providers: '/api/providers',
    session: '/api/session',
    archetypes: '/api/archetypes',
    templates: '/api/templates',
    system: '/api/system',
    ollama: '/api/ollama',
    files: '/api/files',
  },
} as const;

// Helper function to build full API URLs
export const getApiUrl = (path: string): string => {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${config.apiBaseUrl}${cleanPath}`;
};

// Export commonly used full URLs
export const API_URLS = {
  providers: getApiUrl(config.api.providers),
  session: getApiUrl(config.api.session),
  archetypes: getApiUrl(config.api.archetypes),
  templates: getApiUrl(config.api.templates),
  systemRamStatus: getApiUrl(`${config.api.system}/ram-status`),
  ollamaStatus: getApiUrl(`${config.api.ollama}/status`),
  ollamaModels: getApiUrl(`${config.api.ollama}/models`),
  ollamaRecommended: getApiUrl(`${config.api.ollama}/recommended`),
  uploadFile: getApiUrl(`${config.api.files}/upload`),
} as const;

// Validation limits (should match backend)
export const VALIDATION = {
  // File upload limits
  maxFileSize: 10 * 1024 * 1024, // 10MB
  maxFileSizeMB: 10,

  // Prompt limits
  maxPromptLength: 50000, // 50k characters
  minPromptLength: 1,

  // Session limits
  maxIterations: 10,
  minIterations: 1,
  maxCouncilMembers: 10,
  minCouncilMembers: 1,
} as const;
