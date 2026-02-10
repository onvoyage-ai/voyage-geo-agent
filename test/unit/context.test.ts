import { describe, it, expect } from 'vitest';
import { createRunContext, updateContext } from '../../src/core/context.js';
import { DEFAULT_CONFIG } from '../../src/config/defaults.js';

describe('RunContext', () => {
  it('should create context with unique run ID', () => {
    const ctx1 = createRunContext(DEFAULT_CONFIG);
    const ctx2 = createRunContext(DEFAULT_CONFIG);
    expect(ctx1.runId).toMatch(/^run-\d+-[a-f0-9]+$/);
    expect(ctx1.runId).not.toBe(ctx2.runId);
  });

  it('should set pending status initially', () => {
    const ctx = createRunContext(DEFAULT_CONFIG);
    expect(ctx.status).toBe('pending');
  });

  it('should have empty errors array', () => {
    const ctx = createRunContext(DEFAULT_CONFIG);
    expect(ctx.errors).toEqual([]);
  });

  it('should have ISO timestamp', () => {
    const ctx = createRunContext(DEFAULT_CONFIG);
    expect(() => new Date(ctx.startedAt)).not.toThrow();
  });

  it('should update context immutably', () => {
    const ctx = createRunContext(DEFAULT_CONFIG);
    const updated = updateContext(ctx, { status: 'running' });
    expect(updated.status).toBe('running');
    expect(ctx.status).toBe('pending'); // original unchanged
  });
});
