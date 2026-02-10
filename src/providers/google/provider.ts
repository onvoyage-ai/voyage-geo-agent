import { GoogleGenAI } from '@google/genai';
import type { ProviderConfig } from '../../config/schema.js';
import { BaseProvider } from '../base.js';
import type { ProviderResponse } from '../types.js';
import { GeoProviderError, GeoRateLimitError } from '../../core/errors.js';

export class GoogleProvider extends BaseProvider {
  readonly name = 'google';
  readonly displayName = 'Google (Gemini)';
  private client: GoogleGenAI;

  constructor(config: ProviderConfig) {
    super(config);
    this.client = new GoogleGenAI({ apiKey: config.apiKey || '' });
  }

  async query(prompt: string): Promise<ProviderResponse> {
    const start = Date.now();
    const model = this.config.model || 'gemini-2.0-flash';

    try {
      const response = await this.withTimeout(
        this.client.models.generateContent({
          model,
          contents: prompt,
          config: {
            maxOutputTokens: this.config.maxTokens,
            temperature: this.config.temperature,
          },
        }),
      );

      const text = response.text ?? '';
      const latencyMs = Date.now() - start;

      return {
        text,
        model,
        provider: this.name,
        latencyMs,
        tokenUsage: response.usageMetadata
          ? {
              promptTokens: response.usageMetadata.promptTokenCount ?? 0,
              completionTokens: response.usageMetadata.candidatesTokenCount ?? 0,
              totalTokens: response.usageMetadata.totalTokenCount ?? 0,
            }
          : undefined,
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      if (message.includes('429') || message.toLowerCase().includes('rate limit')) {
        throw new GeoRateLimitError(message, this.name);
      }
      if (err instanceof GeoProviderError) throw err;
      throw this.wrapError(err);
    }
  }
}
