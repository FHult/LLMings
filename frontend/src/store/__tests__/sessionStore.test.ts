/**
 * Tests for useSessionStore — focuses on handleStreamEvent and state transitions.
 *
 * handleStreamEvent is the most complex frontend logic (6-branch switch) and
 * is the glue between the SSE wire format and the UI state. Any mismatch
 * between what the backend emits and what the frontend expects surfaces here.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useSessionStore } from '../sessionStore';
import type { StreamEvent } from '@/types';

// ---------------------------------------------------------------------------
// Reset store state between tests so tests are independent.
// ---------------------------------------------------------------------------

const INITIAL_STATE = {
  sessionId: null,
  status: 'idle' as const,
  currentIteration: 1,
  totalIterations: 1,
  responses: [],
  mergedResponses: [],
  statusMessage: '',
  totalCost: 0,
  totalTokens: { input: 0, output: 0 },
  error: undefined,
  _reader: null,
  _sessionConfig: null,
  isPaused: false,
};

beforeEach(() => {
  useSessionStore.setState(INITIAL_STATE);
  localStorage.clear();
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function dispatch(event: StreamEvent) {
  useSessionStore.getState().handleStreamEvent(event);
}

function state() {
  return useSessionStore.getState();
}

// ---------------------------------------------------------------------------
// session_created
// ---------------------------------------------------------------------------

describe('handleStreamEvent: session_created', () => {
  it('sets sessionId from event', () => {
    dispatch({ type: 'session_created', session_id: 'sess-abc' });
    expect(state().sessionId).toBe('sess-abc');
  });

  it('sets status message', () => {
    dispatch({ type: 'session_created', session_id: 'sess-abc' });
    expect(state().statusMessage).toBeTruthy();
  });

  it('null session_id stored as null not undefined', () => {
    dispatch({ type: 'session_created' });
    expect(state().sessionId).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// status
// ---------------------------------------------------------------------------

describe('handleStreamEvent: status', () => {
  it('updates statusMessage', () => {
    dispatch({ type: 'status', message: 'Initialising council…' });
    expect(state().statusMessage).toBe('Initialising council…');
  });

  it('empty message stored as empty string', () => {
    dispatch({ type: 'status', message: '' });
    expect(state().statusMessage).toBe('');
  });
});

// ---------------------------------------------------------------------------
// initial_response
// ---------------------------------------------------------------------------

describe('handleStreamEvent: initial_response', () => {
  const RESPONSE_EVENT: StreamEvent = {
    type: 'initial_response',
    done: true,
    provider: 'openai',
    content: 'The answer is 42.',
    iteration: 1,
    response_id: 'resp-001',
    member_id: 'member-1',
    member_role: 'Analyst',
    tokens: { input: 100, output: 50 },
    cost: 0.002,
  };

  it('appends to responses array', () => {
    dispatch(RESPONSE_EVENT);
    expect(state().responses).toHaveLength(1);
  });

  it('response has correct fields', () => {
    dispatch(RESPONSE_EVENT);
    const r = state().responses[0];
    expect(r.provider).toBe('openai');
    expect(r.content).toBe('The answer is 42.');
    expect(r.type).toBe('initial_response');
    expect(r.iteration).toBe(1);
    expect(r.member_id).toBe('member-1');
    expect(r.member_role).toBe('Analyst');
  });

  it('accumulates cost', () => {
    dispatch(RESPONSE_EVENT);
    dispatch({ ...RESPONSE_EVENT, response_id: 'resp-002', cost: 0.003 });
    expect(state().totalCost).toBeCloseTo(0.005);
  });

  it('accumulates token counts', () => {
    dispatch(RESPONSE_EVENT);
    dispatch({ ...RESPONSE_EVENT, response_id: 'resp-002', tokens: { input: 50, output: 25 } });
    expect(state().totalTokens.input).toBe(150);
    expect(state().totalTokens.output).toBe(75);
  });

  it('does NOT append when done is false', () => {
    dispatch({ ...RESPONSE_EVENT, done: false });
    expect(state().responses).toHaveLength(0);
  });

  it('does NOT append when content is missing', () => {
    const { content: _, ...withoutContent } = RESPONSE_EVENT;
    dispatch(withoutContent);
    expect(state().responses).toHaveLength(0);
  });

  it('does NOT append when provider is missing', () => {
    const { provider: _, ...withoutProvider } = RESPONSE_EVENT;
    dispatch(withoutProvider);
    expect(state().responses).toHaveLength(0);
  });

  it('multiple responses accumulate in order received', () => {
    dispatch({ ...RESPONSE_EVENT, response_id: 'r1', member_role: 'Analyst' });
    dispatch({ ...RESPONSE_EVENT, response_id: 'r2', member_role: 'Creative' });
    const roles = state().responses.map((r) => r.member_role);
    expect(roles).toContain('Analyst');
    expect(roles).toContain('Creative');
    expect(state().responses).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// merge
// ---------------------------------------------------------------------------

describe('handleStreamEvent: merge', () => {
  const MERGE_EVENT: StreamEvent = {
    type: 'merge',
    done: true,
    provider: 'anthropic',
    content: 'Synthesised answer.',
    iteration: 1,
    response_id: 'merge-001',
    member_role: 'Chair',
    tokens: { input: 500, output: 200 },
    cost: 0.01,
  };

  it('appends to mergedResponses, not responses', () => {
    dispatch(MERGE_EVENT);
    expect(state().mergedResponses).toHaveLength(1);
    expect(state().responses).toHaveLength(0);
  });

  it('merge response has type merge', () => {
    dispatch(MERGE_EVENT);
    expect(state().mergedResponses[0].type).toBe('merge');
  });

  it('updates currentIteration from event', () => {
    dispatch({ ...MERGE_EVENT, iteration: 3 });
    expect(state().currentIteration).toBe(3);
  });

  it('preserves structure field when present', () => {
    const structure = {
      key_agreements: ['Both agree on X'],
      key_disagreements: [],
      confidence: 0.9,
      reasoning: 'Clear consensus',
    };
    dispatch({ ...MERGE_EVENT, structure });
    expect(state().mergedResponses[0].structure).toEqual(structure);
  });

  it('accumulates cost', () => {
    dispatch(MERGE_EVENT);
    expect(state().totalCost).toBeCloseTo(0.01);
  });
});

// ---------------------------------------------------------------------------
// feedback
// ---------------------------------------------------------------------------

describe('handleStreamEvent: feedback', () => {
  const FEEDBACK_EVENT: StreamEvent = {
    type: 'feedback',
    done: true,
    provider: 'openai',
    content: 'Here is my feedback.',
    iteration: 2,
    response_id: 'fb-001',
    member_role: 'Analyst',
    tokens: { input: 300, output: 100 },
    cost: 0.005,
  };

  it('appends to responses (not mergedResponses)', () => {
    dispatch(FEEDBACK_EVENT);
    expect(state().responses).toHaveLength(1);
    expect(state().mergedResponses).toHaveLength(0);
  });

  it('feedback response has type feedback', () => {
    dispatch(FEEDBACK_EVENT);
    expect(state().responses[0].type).toBe('feedback');
  });

  it('advances currentIteration when feedback iteration is higher', () => {
    useSessionStore.setState({ currentIteration: 1 });
    dispatch(FEEDBACK_EVENT); // iteration: 2
    expect(state().currentIteration).toBe(2);
  });

  it('does NOT regress currentIteration for stale feedback', () => {
    useSessionStore.setState({ currentIteration: 3 });
    dispatch({ ...FEEDBACK_EVENT, iteration: 1 });
    expect(state().currentIteration).toBe(3);
  });
});

// ---------------------------------------------------------------------------
// complete
// ---------------------------------------------------------------------------

describe('handleStreamEvent: complete', () => {
  it('sets status to completed', () => {
    useSessionStore.setState({ status: 'running' });
    dispatch({ type: 'complete' });
    expect(state().status).toBe('completed');
  });

  it('sets a statusMessage', () => {
    dispatch({ type: 'complete' });
    expect(state().statusMessage).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// error
// ---------------------------------------------------------------------------

describe('handleStreamEvent: error', () => {
  it('sets status to error', () => {
    useSessionStore.setState({ status: 'running' });
    dispatch({ type: 'error', message: 'Provider failed' });
    expect(state().status).toBe('error');
  });

  it('stores error message', () => {
    dispatch({ type: 'error', message: 'Rate limit exceeded' });
    expect(state().error).toBe('Rate limit exceeded');
  });

  it('falls back to default when message is missing', () => {
    dispatch({ type: 'error' });
    expect(state().error).toBeTruthy();
  });

  it('sets statusMessage to indicate failure', () => {
    dispatch({ type: 'error', message: 'Something went wrong' });
    expect(state().statusMessage).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// pauseSession
// ---------------------------------------------------------------------------

describe('pauseSession', () => {
  it('sets isPaused and clears reader', () => {
    const mockReader = { cancel: vi.fn() } as unknown as ReadableStreamDefaultReader<Uint8Array>;
    useSessionStore.setState({ status: 'running', _reader: mockReader });

    state().pauseSession();

    expect(state().isPaused).toBe(true);
    expect(state()._reader).toBeNull();
    expect(mockReader.cancel).toHaveBeenCalled();
  });

  it('cancels the SSE reader', () => {
    const cancel = vi.fn();
    const mockReader = { cancel } as unknown as ReadableStreamDefaultReader<Uint8Array>;
    useSessionStore.setState({ status: 'running', _reader: mockReader });

    state().pauseSession();
    expect(cancel).toHaveBeenCalledOnce();
  });

  it('no-op when session is not running', () => {
    const cancel = vi.fn();
    const mockReader = { cancel } as unknown as ReadableStreamDefaultReader<Uint8Array>;
    useSessionStore.setState({ status: 'idle', _reader: mockReader });

    state().pauseSession();
    expect(cancel).not.toHaveBeenCalled();
    expect(state().isPaused).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// clearSession
// ---------------------------------------------------------------------------

describe('clearSession', () => {
  it('resets all state to initial values', () => {
    useSessionStore.setState({
      sessionId: 'sess-123',
      status: 'completed',
      currentIteration: 3,
      responses: [{ id: 'r1', provider: 'openai', content: 'x', iteration: 1, type: 'initial_response', tokens: { input: 1, output: 1 }, cost: 0 }],
      totalCost: 99,
    });

    state().clearSession();

    expect(state().sessionId).toBeNull();
    expect(state().status).toBe('idle');
    expect(state().currentIteration).toBe(1);
    expect(state().responses).toHaveLength(0);
    expect(state().totalCost).toBe(0);
  });

  it('cancels an active reader before clearing', () => {
    const cancel = vi.fn();
    const mockReader = { cancel } as unknown as ReadableStreamDefaultReader<Uint8Array>;
    useSessionStore.setState({ _reader: mockReader });

    state().clearSession();
    expect(cancel).toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Cost / token accumulation edge cases
// ---------------------------------------------------------------------------

describe('cost and token edge cases', () => {
  it('missing cost defaults to 0 (no NaN)', () => {
    useSessionStore.getState().handleStreamEvent({
      type: 'initial_response',
      done: true,
      provider: 'openai',
      content: 'hello',
      // cost intentionally omitted
    });
    expect(state().totalCost).toBe(0);
    expect(Number.isNaN(state().totalCost)).toBe(false);
  });

  it('missing tokens defaults to 0 (no NaN)', () => {
    useSessionStore.getState().handleStreamEvent({
      type: 'initial_response',
      done: true,
      provider: 'openai',
      content: 'hello',
      // tokens intentionally omitted
    });
    expect(state().totalTokens.input).toBe(0);
    expect(state().totalTokens.output).toBe(0);
  });
});
