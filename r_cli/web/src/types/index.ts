// API Types for R CLI Dashboard

export interface LLMStatus {
  connected: boolean;
  backend: string | null;
  model: string | null;
  base_url: string | null;
}

export interface StatusResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  uptime_seconds: number;
  llm: LLMStatus;
  skills_loaded: number;
  timestamp: string;
}

export interface SkillTool {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
}

export interface SkillInfo {
  name: string;
  description: string;
  category: string;
  tools: SkillTool[];
}

export interface SkillsResponse {
  skills: SkillInfo[];
  total: number;
}

export interface ChatRequest {
  message: string;
  skill?: string;
  stream?: boolean;
}

export interface ChatResponse {
  response: string;
  skill_used: string | null;
  tools_called: string[];
  tokens_used: number;
}

export interface AuditEvent {
  timestamp: string;
  action: string;
  severity: string;
  user_id: string | null;
  username: string | null;
  auth_type: string | null;
  client_ip: string | null;
  resource: string | null;
  success: boolean;
  error_message: string | null;
  duration_ms: number | null;
}

export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthUser {
  user_id: string;
  username: string;
  scopes: string[];
  auth_type: string;
}

export interface APIKeyInfo {
  key_id: string;
  name: string;
  scopes: string[];
  created_at: string;
  last_used: string | null;
  expires_at: string | null;
  is_active: boolean;
}

export interface APIKeyCreateResponse {
  key: string;
  key_id: string;
  name: string;
  scopes: string[];
  message: string;
}
