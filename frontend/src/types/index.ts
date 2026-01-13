/**
 * TypeScript type definitions for HiveCouncil
 */

export interface Provider {
  name: string;
  current_model: string | null;
  default_model: string;
  available_models: string[];
  configured: boolean;
}

export interface ProvidersResponse {
  providers: Record<string, Provider>;
  configured_count: number;
}

export interface ModelConfig {
  provider: string;
  model: string;
}

export interface PersonalityArchetype {
  id: string;
  name: string;
  description: string;
  emoji: string;
}

export interface CouncilMember {
  id: string;
  provider: string;
  model: string;
  role: string;
  archetype: string;
  custom_personality?: string;
  is_chair: boolean;
}

export interface FileAttachment {
  filename: string;
  content_type: string;
  size: number;
  extracted_text?: string;
  base64_data?: string;
}

export interface SessionConfig {
  prompt: string;
  council_members: CouncilMember[];
  iterations: number;
  template: 'analytical' | 'creative' | 'technical' | 'balanced';
  preset: 'creative' | 'balanced' | 'precise';
  system_prompt?: string;
  autopilot: boolean;
  files?: FileAttachment[];

  // Legacy fields for backward compatibility
  chair?: string;
  selected_providers?: string[];
  model_configs?: ModelConfig[];
}

export interface SessionResponse {
  session_id: string;
  status: string;
  created_at: string;
}

export interface Response {
  id: string;
  created_at: string;
  session_id: string;
  provider: string;
  model: string;
  content: string;
  iteration: number;
  role: 'council' | 'chair';
  input_tokens: number;
  output_tokens: number;
  estimated_cost: number;
  response_time_ms: number;
  error?: string;
}

export interface Session {
  id: string;
  created_at: string;
  updated_at: string;
  prompt: string;
  current_prompt?: string;
  chair_provider: string;
  total_iterations: number;
  current_iteration: number;
  merge_template: string;
  preset: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed';
  autopilot: boolean;
  system_prompt?: string;
  user_guidance?: string;
}

export interface StreamEvent {
  type: 'session_created' | 'status' | 'initial_response' | 'merge' | 'feedback' | 'complete' | 'error';
  session_id?: number;
  message?: string;
  provider?: string;
  content?: string;
  iteration?: number;
  tokens?: {
    input: number;
    output: number;
  };
  cost?: number;
  done?: boolean;
  response_id?: number;
}

export interface CouncilResponse {
  id: number;
  provider: string;
  content: string;
  iteration: number;
  type: 'initial_response' | 'merge' | 'feedback';
  tokens: {
    input: number;
    output: number;
  };
  cost: number;
}

export interface SessionState {
  sessionId: number | null;
  status: 'idle' | 'running' | 'completed' | 'error';
  currentIteration: number;
  totalIterations: number;
  responses: CouncilResponse[];
  mergedResponses: CouncilResponse[];
  statusMessage: string;
  totalCost: number;
  totalTokens: {
    input: number;
    output: number;
  };
  error?: string;
}

export type Template = 'analytical' | 'creative' | 'technical' | 'balanced';
export type Preset = 'creative' | 'balanced' | 'precise';
