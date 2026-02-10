import pLimit from 'p-limit';
import type { AIProvider } from '../../providers/types.js';
import type { GeneratedQuery } from '../../types/query.js';
import type { QueryResult } from '../../types/result.js';
import type { ExecutionConfig } from '../../config/schema.js';
import { RateLimiter } from './rate-limiter.js';
import { withRetry } from './retry.js';
import { createLogger } from '../../utils/logger.js';

const logger = createLogger('runner');

export interface ExecutionTask {
  query: GeneratedQuery;
  provider: AIProvider;
  iteration: number;
}

export class QueryRunner {
  private config: ExecutionConfig;
  private rateLimiters = new Map<string, RateLimiter>();

  constructor(config: ExecutionConfig) {
    this.config = config;
  }

  setRateLimit(providerName: string, requestsPerMinute: number): void {
    this.rateLimiters.set(providerName, new RateLimiter(requestsPerMinute));
  }

  async runAll(
    tasks: ExecutionTask[],
    onResult?: (result: QueryResult) => void,
  ): Promise<QueryResult[]> {
    const limit = pLimit(this.config.concurrency);
    const results: QueryResult[] = [];

    const promises = tasks.map((task) =>
      limit(async () => {
        const result = await this.executeTask(task);
        results.push(result);
        onResult?.(result);
        return result;
      }),
    );

    await Promise.all(promises);
    return results;
  }

  private async executeTask(task: ExecutionTask): Promise<QueryResult> {
    const { query, provider, iteration } = task;
    const rateLimiter = this.rateLimiters.get(provider.name);

    try {
      const result = await withRetry(
        async () => {
          if (rateLimiter) {
            await rateLimiter.acquire();
          }

          const response = await provider.query(query.text);

          return {
            queryId: query.id,
            queryText: query.text,
            provider: provider.name,
            model: response.model,
            response: response.text,
            latencyMs: response.latencyMs,
            tokenUsage: response.tokenUsage,
            iteration,
            timestamp: new Date().toISOString(),
          } satisfies QueryResult;
        },
        {
          retries: this.config.retries,
          minTimeout: this.config.retryDelayMs,
        },
        `${provider.name}:${query.id}`,
      );

      return result;
    } catch (err) {
      logger.error(
        { provider: provider.name, queryId: query.id, error: err instanceof Error ? err.message : String(err) },
        'Query execution failed after retries',
      );

      return {
        queryId: query.id,
        queryText: query.text,
        provider: provider.name,
        model: 'unknown',
        response: '',
        latencyMs: 0,
        iteration,
        timestamp: new Date().toISOString(),
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }
}
