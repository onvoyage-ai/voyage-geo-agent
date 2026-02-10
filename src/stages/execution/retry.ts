import pRetry from 'p-retry';
import { GeoRateLimitError } from '../../core/errors.js';
import { createLogger } from '../../utils/logger.js';

const logger = createLogger('retry');

export interface RetryOptions {
  retries: number;
  minTimeout: number;
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  options: RetryOptions,
  label: string,
): Promise<T> {
  return pRetry(fn, {
    retries: options.retries,
    minTimeout: options.minTimeout,
    factor: 2,
    onFailedAttempt: (error) => {
      const attempt = error.attemptNumber;
      const remaining = error.retriesLeft;

      if (error instanceof GeoRateLimitError && error.retryAfterMs) {
        logger.warn(
          { label, attempt, remaining, retryAfterMs: error.retryAfterMs },
          `Rate limited, waiting ${error.retryAfterMs}ms`,
        );
      } else {
        logger.warn(
          { label, attempt, remaining, error: error.message },
          `Attempt ${attempt} failed, ${remaining} retries left`,
        );
      }
    },
  });
}
