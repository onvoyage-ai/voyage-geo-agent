import { describe, it, expect } from 'vitest';
import {
  GeoError,
  GeoProviderError,
  GeoPipelineError,
  GeoRateLimitError,
  GeoTimeoutError,
  GeoConfigError,
  GeoStorageError,
} from '../../src/core/errors.js';

describe('Error Hierarchy', () => {
  it('GeoError should have code', () => {
    const err = new GeoError('test', 'TEST_CODE');
    expect(err.message).toBe('test');
    expect(err.code).toBe('TEST_CODE');
    expect(err.name).toBe('GeoError');
    expect(err).toBeInstanceOf(Error);
  });

  it('GeoProviderError should include provider name', () => {
    const err = new GeoProviderError('failed', 'openai', 500);
    expect(err.provider).toBe('openai');
    expect(err.statusCode).toBe(500);
    expect(err).toBeInstanceOf(GeoError);
  });

  it('GeoPipelineError should include stage name', () => {
    const err = new GeoPipelineError('stage failed', 'research');
    expect(err.stage).toBe('research');
    expect(err).toBeInstanceOf(GeoError);
  });

  it('GeoRateLimitError should extend provider error', () => {
    const err = new GeoRateLimitError('rate limited', 'openai', 5000);
    expect(err.retryAfterMs).toBe(5000);
    expect(err.code).toBe('RATE_LIMIT_ERROR');
    expect(err).toBeInstanceOf(GeoProviderError);
  });

  it('GeoTimeoutError should include timeout', () => {
    const err = new GeoTimeoutError('timed out', 'anthropic', 30000);
    expect(err.timeoutMs).toBe(30000);
    expect(err.code).toBe('TIMEOUT_ERROR');
    expect(err).toBeInstanceOf(GeoProviderError);
  });

  it('GeoConfigError should have CONFIG_ERROR code', () => {
    const err = new GeoConfigError('bad config');
    expect(err.code).toBe('CONFIG_ERROR');
  });

  it('GeoStorageError should have STORAGE_ERROR code', () => {
    const err = new GeoStorageError('disk full');
    expect(err.code).toBe('STORAGE_ERROR');
  });
});
