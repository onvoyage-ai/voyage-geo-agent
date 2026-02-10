import Anthropic from '@anthropic-ai/sdk';
import type { ProviderConfig } from '../../config/schema.js';
import { BaseProvider } from '../base.js';
import type { ProviderResponse } from '../types.js';
import { GeoProviderError, GeoRateLimitError } from '../../core/errors.js';

export class AnthropicProvider extends BaseProvider {
  readonly name = 'anthropic';
  readonly displayName = 'Anthropic (Claude)';
  private client: Anthropic;

  constructor(config: ProviderConfig) {
    super(config);
    this.client = new Anthropic({
      apiKey: config.apiKey,
    });
  }

  async query(prompt: string): Promise<ProviderResponse> {
    const start = Date.now();
    const model = this.config.model || 'claude-haiku-4-5-20251001';

    try {
      const response = await this.withTimeout(
        this.client.messages.create({
          model,
          max_tokens: this.config.maxTokens,
          messages: [{ role: 'user', content: prompt }],
        }),
      );

      const text = response.content
        .filter((block): block is Anthropic.TextBlock => block.type === 'text')
        .map((block) => block.text)
        .join('\n');

      const latencyMs = Date.now() - start;

      return {
        text,
        model: response.model,
        provider: this.name,
        latencyMs,
        tokenUsage: {
          promptTokens: response.usage.input_tokens,
          completionTokens: response.usage.output_tokens,
          totalTokens: response.usage.input_tokens + response.usage.output_tokens,
        },
      };
    } catch (err) {
      if (err instanceof Anthropic.RateLimitError) {
        throw new GeoRateLimitError(err.message, this.name);
      }
      if (err instanceof GeoProviderError) throw err;
      throw this.wrapError(err);
    }
  }
}
