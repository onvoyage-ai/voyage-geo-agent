import type { TokenUsage } from '../types/result.js';

export interface ProviderResponse {
  text: string;
  model: string;
  provider: string;
  latencyMs: number;
  tokenUsage?: TokenUsage;
}

export interface ProviderHealthCheck {
  provider: string;
  healthy: boolean;
  latencyMs: number;
  model: string;
  error?: string;
}

export interface AIProvider {
  readonly name: string;
  readonly displayName: string;

  query(prompt: string): Promise<ProviderResponse>;
  healthCheck(): Promise<ProviderHealthCheck>;
  isConfigured(): boolean;
}
