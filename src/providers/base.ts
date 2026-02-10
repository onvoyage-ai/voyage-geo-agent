import type { ProviderConfig } from '../config/schema.js';
import type { AIProvider, ProviderResponse, ProviderHealthCheck } from './types.js';
import { GeoProviderError, GeoTimeoutError } from '../core/errors.js';
import { createLogger } from '../utils/logger.js';

export abstract class BaseProvider implements AIProvider {
  abstract readonly name: string;
  abstract readonly displayName: string;

  protected config: ProviderConfig;
  protected logger;

  constructor(config: ProviderConfig) {
    this.config = config;
    this.logger = createLogger(`provider:${config.name}`);
  }

  abstract query(prompt: string): Promise<ProviderResponse>;

  isConfigured(): boolean {
    return !!this.config.apiKey;
  }

  async healthCheck(): Promise<ProviderHealthCheck> {
    const start = Date.now();
    try {
      const response = await this.query('Say "ok" and nothing else.');
      return {
        provider: this.name,
        healthy: true,
        latencyMs: response.latencyMs,
        model: response.model,
      };
    } catch (err) {
      return {
        provider: this.name,
        healthy: false,
        latencyMs: Date.now() - start,
        model: this.config.model || 'unknown',
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }

  protected withTimeout<T>(promise: Promise<T>, timeoutMs?: number): Promise<T> {
    const timeout = timeoutMs ?? 15000;

    return new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new GeoTimeoutError(
          `Provider ${this.name} timed out after ${timeout}ms`,
          this.name,
          timeout,
        ));
      }, timeout);

      promise
        .then((result) => {
          clearTimeout(timer);
          resolve(result);
        })
        .catch((err) => {
          clearTimeout(timer);
          reject(err);
        });
    });
  }

  protected wrapError(err: unknown): GeoProviderError {
    if (err instanceof GeoProviderError) return err;
    const message = err instanceof Error ? err.message : String(err);
    return new GeoProviderError(message, this.name);
  }
}
