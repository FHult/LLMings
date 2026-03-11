/**
 * API client for LLMings backend
 */
import axios from 'axios';
import type {
  ProvidersResponse,
  SessionConfig,
  SessionResponse,
} from '@/types';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Provider API
 */
export const providersApi = {
  /**
   * Get all providers and their available models
   */
  getProviders: async (): Promise<ProvidersResponse> => {
    const response = await apiClient.get<ProvidersResponse>('/providers');
    return response.data;
  },

  /**
   * Get available models for a specific provider
   */
  getProviderModels: async (providerName: string) => {
    const response = await apiClient.get(`/providers/${providerName}/models`);
    return response.data;
  },
};

/**
 * Session API
 */
export const sessionApi = {
  /**
   * Create a new council session
   */
  createSession: async (config: SessionConfig): Promise<SessionResponse> => {
    const response = await apiClient.post<SessionResponse>('/session/create', config);
    return response.data;
  },

  /**
   * Get full session details
   */
  getSession: async (sessionId: string) => {
    const response = await apiClient.get(`/session/${sessionId}`);
    return response.data;
  },

  /**
   * Trigger next iteration
   */
  triggerIteration: async (
    sessionId: string,
    guidance?: string,
    excludedProviders?: string[]
  ) => {
    const response = await apiClient.post(`/session/${sessionId}/iterate`, {
      guidance,
      excluded_providers: excludedProviders,
    });
    return response.data;
  },

  /**
   * Pause iteration
   */
  pauseIteration: async (sessionId: string) => {
    const response = await apiClient.post(`/session/${sessionId}/pause`);
    return response.data;
  },

  /**
   * Resume iteration
   */
  resumeIteration: async (sessionId: string) => {
    const response = await apiClient.post(`/session/${sessionId}/resume`);
    return response.data;
  },

  /**
   * Export session to markdown
   */
  exportMarkdown: async (sessionId: string): Promise<string> => {
    const response = await apiClient.get(`/session/${sessionId}/export/markdown`);
    return response.data;
  },

  /**
   * Test backend connection
   */
  testConnection: async () => {
    const response = await apiClient.get('/sessions/test');
    return response.data;
  },
};

export default apiClient;
