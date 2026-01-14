/**
 * Zustand store for session management with SSE streaming
 * Includes localStorage persistence to prevent data loss on page refresh
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { SessionConfig, StreamEvent, CouncilResponse, SessionState as SessionStateType } from '@/types';
import { API_URLS } from '@/lib/config';

interface SessionStore extends SessionStateType {
  // Actions
  startSession: (config: SessionConfig) => Promise<void>;
  resumeSession: () => Promise<void>;
  pauseSession: () => void;
  clearSession: () => void;
  handleStreamEvent: (event: StreamEvent) => void;
  // Internal state (not persisted)
  _reader: ReadableStreamDefaultReader<Uint8Array> | null;
  _sessionConfig: SessionConfig | null;
  isPaused: boolean;
}

// Initial state for resetting
const initialState = {
  sessionId: null,
  status: 'idle' as const,
  currentIteration: 1,
  totalIterations: 1,
  responses: [] as CouncilResponse[],
  mergedResponses: [] as CouncilResponse[],
  statusMessage: '',
  totalCost: 0,
  totalTokens: { input: 0, output: 0 },
  error: undefined,
  _reader: null,
  _sessionConfig: null,
  isPaused: false,
};

export const useSessionStore = create<SessionStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      startSession: async (config: SessionConfig) => {
        // Reset state and store config for potential resume
        set({
          sessionId: null,
          status: 'running',
          currentIteration: 1,
          totalIterations: config.iterations,
          responses: [],
          mergedResponses: [],
          statusMessage: 'Initializing council session...',
          totalCost: 0,
          totalTokens: { input: 0, output: 0 },
          error: undefined,
          isPaused: false,
          _sessionConfig: config,
        });

        try {
          // Create SSE connection
          const response = await fetch(`${API_URLS.session}/create`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const reader = response.body?.getReader();
          const decoder = new TextDecoder();

          if (!reader) {
            throw new Error('No response body');
          }

          // Store reader for potential cancellation
          set({ _reader: reader });

          // Read the stream
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              break;
            }

            // Decode the chunk
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            // Process each line
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                try {
                  const event: StreamEvent = JSON.parse(data);
                  get().handleStreamEvent(event);
                } catch (e) {
                  console.error('Failed to parse SSE event:', e);
                }
              }
            }
          }
        } catch (error) {
          // Check if this was a manual pause
          if (error instanceof Error && error.name === 'AbortError') {
            // Don't change status if paused - keep the session data visible
            const currentState = get();
            if (!currentState.isPaused) {
              set({
                status: 'error',
                statusMessage: 'Session interrupted',
                _reader: null,
              });
            }
          } else {
            set({
              status: 'error',
              error: error instanceof Error ? error.message : 'Failed to create session',
              statusMessage: 'Session failed',
              _reader: null,
            });
          }
        }
      },

      pauseSession: () => {
        const { _reader, status } = get();

        if (status === 'running' && _reader) {
          _reader.cancel();
          set({
            isPaused: true,
            statusMessage: 'Session paused - you can resume to continue',
            _reader: null,
          });
        }
      },

      resumeSession: async () => {
        const state = get();

        if (!state.isPaused || !state._sessionConfig) {
          console.error('Cannot resume: session not paused or config missing');
          return;
        }

        // Resume with current state by creating a modified config
        const resumeConfig: SessionConfig & { resume_state?: unknown } = {
          ...state._sessionConfig,
          resume_state: {
            current_iteration: state.currentIteration,
            responses: state.responses,
            merged_responses: state.mergedResponses,
            total_cost: state.totalCost,
            total_tokens: state.totalTokens,
          }
        };

        set({
          status: 'running',
          isPaused: false,
          statusMessage: 'Resuming session...',
        });

        try {
          // Create SSE connection with resume data
          const response = await fetch(`${API_URLS.session}/resume`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(resumeConfig),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const reader = response.body?.getReader();
          const decoder = new TextDecoder();

          if (!reader) {
            throw new Error('No response body');
          }

          // Store reader for potential cancellation
          set({ _reader: reader });

          // Read the stream
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              break;
            }

            // Decode the chunk
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            // Process each line
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                try {
                  const event: StreamEvent = JSON.parse(data);
                  get().handleStreamEvent(event);
                } catch (e) {
                  console.error('Failed to parse SSE event:', e);
                }
              }
            }
          }
        } catch (error) {
          // Check if this was a manual pause
          if (error instanceof Error && error.name === 'AbortError') {
            // Don't change status if paused - keep the session data visible
            const currentState = get();
            if (!currentState.isPaused) {
              set({
                status: 'error',
                statusMessage: 'Session interrupted',
                _reader: null,
              });
            }
          } else {
            set({
              status: 'error',
              error: error instanceof Error ? error.message : 'Failed to resume session',
              statusMessage: 'Resume failed',
              _reader: null,
            });
          }
        }
      },

      handleStreamEvent: (event: StreamEvent) => {
        const state = get();

        switch (event.type) {
          case 'session_created':
            set({
              sessionId: event.session_id || null,
              statusMessage: 'Session created, starting council...',
            });
            break;

          case 'status':
            set({
              statusMessage: event.message || '',
            });
            break;

          case 'initial_response':
            if (event.done && event.provider && event.content) {
              const newResponse: CouncilResponse = {
                id: event.response_id || Date.now(),
                provider: event.provider,
                content: event.content,
                iteration: event.iteration || 1,
                type: 'initial_response',
                tokens: event.tokens || { input: 0, output: 0 },
                cost: event.cost || 0,
                member_id: event.member_id,
                member_role: event.member_role,
              };

              set({
                responses: [...state.responses, newResponse],
                totalCost: state.totalCost + (event.cost || 0),
                totalTokens: {
                  input: state.totalTokens.input + (event.tokens?.input || 0),
                  output: state.totalTokens.output + (event.tokens?.output || 0),
                },
                statusMessage: `Received response from ${event.member_role || event.provider}`,
              });
            }
            break;

          case 'merge':
            if (event.done && event.provider && event.content) {
              const mergedResponse: CouncilResponse = {
                id: event.response_id || Date.now(),
                provider: event.provider,
                content: event.content,
                iteration: event.iteration || 1,
                type: 'merge',
                tokens: event.tokens || { input: 0, output: 0 },
                cost: event.cost || 0,
                member_id: event.member_id,
                member_role: event.member_role,
              };

              set({
                mergedResponses: [...state.mergedResponses, mergedResponse],
                totalCost: state.totalCost + (event.cost || 0),
                totalTokens: {
                  input: state.totalTokens.input + (event.tokens?.input || 0),
                  output: state.totalTokens.output + (event.tokens?.output || 0),
                },
                statusMessage: `${event.member_role || 'Chair'} merged responses for iteration ${event.iteration}`,
                currentIteration: event.iteration || 1,
              });
            }
            break;

          case 'feedback':
            if (event.done && event.provider && event.content) {
              const feedbackResponse: CouncilResponse = {
                id: event.response_id || Date.now(),
                provider: event.provider,
                content: event.content,
                iteration: event.iteration || 1,
                type: 'feedback',
                tokens: event.tokens || { input: 0, output: 0 },
                cost: event.cost || 0,
                member_id: event.member_id,
                member_role: event.member_role,
              };

              // Update currentIteration if this feedback is for a new iteration
              const newIteration = event.iteration || 1;
              const shouldUpdateIteration = newIteration > state.currentIteration;

              set({
                responses: [...state.responses, feedbackResponse],
                totalCost: state.totalCost + (event.cost || 0),
                totalTokens: {
                  input: state.totalTokens.input + (event.tokens?.input || 0),
                  output: state.totalTokens.output + (event.tokens?.output || 0),
                },
                statusMessage: `Received feedback from ${event.member_role || event.provider} for iteration ${event.iteration}`,
                ...(shouldUpdateIteration && { currentIteration: newIteration }),
              });
            }
            break;

          case 'complete':
            set({
              status: 'completed',
              statusMessage: 'Council session completed!',
            });
            break;

          case 'error':
            set({
              status: 'error',
              error: event.message || 'Unknown error occurred',
              statusMessage: 'Session failed',
            });
            break;
        }
      },

      clearSession: () => {
        const { _reader } = get();

        // Cancel any active stream
        if (_reader) {
          _reader.cancel();
        }

        set(initialState);
      },
    }),
    {
      name: 'llmings-session',
      storage: createJSONStorage(() => localStorage),
      // Only persist the session data, not internal state like _reader
      partialize: (state) => ({
        sessionId: state.sessionId,
        status: state.status,
        currentIteration: state.currentIteration,
        totalIterations: state.totalIterations,
        responses: state.responses,
        mergedResponses: state.mergedResponses,
        statusMessage: state.statusMessage,
        totalCost: state.totalCost,
        totalTokens: state.totalTokens,
        error: state.error,
        isPaused: state.isPaused,
        _sessionConfig: state._sessionConfig,
      }),
      // When restoring from storage, if status was 'running', mark as paused
      onRehydrateStorage: () => (state) => {
        if (state && state.status === 'running') {
          // Session was interrupted (page refresh during running)
          state.status = 'idle';
          state.isPaused = true;
          state.statusMessage = 'Session was interrupted. You can start a new session.';
        }
      },
    }
  )
);
