import OpenAI from 'openai';
import type { ProviderConfig } from '../../config/schema.js';
import { BaseProvider } from '../base.js';
import type { ProviderResponse } from '../types.js';
import { GeoProviderError, GeoRateLimitError } from '../../core/errors.js';

export class OpenAIProvider extends BaseProvider {
  readonly name = 'openai';
  readonly displayName = 'OpenAI (ChatGPT)';
  private client: OpenAI;

  constructor(config: ProviderConfig) {
    super(config);
    this.client = new OpenAI({
      apiKey: config.apiKey,
      ...(config.baseURL ? { baseURL: config.baseURL } : {}),
    });
  }

  async query(prompt: string): Promise<ProviderResponse> {
    const start = Date.now();
    const model = this.config.model || 'gpt-4o-mini';

    try {
      const response = await this.withTimeout(
        this.client.chat.completions.create({
          model,
          messages: [{ role: 'user', content: prompt }],
          max_tokens: this.config.maxTokens,
          temperature: this.config.temperature,
        }),
      );

      const text = response.choices[0]?.message?.content || '';
      const latencyMs = Date.now() - start;

      return {
        text,
        model: response.model,
        provider: this.name,
        latencyMs,
        tokenUsage: response.usage
          ? {
              promptTokens: response.usage.prompt_tokens,
              completionTokens: response.usage.completion_tokens,
              totalTokens: response.usage.total_tokens,
            }
          : undefined,
      };
    } catch (err) {
      if (err instanceof OpenAI.RateLimitError) {
        throw new GeoRateLimitError(err.message, this.name);
      }
      if (err instanceof GeoProviderError) throw err;
      throw this.wrapError(err);
    }
  }
}
