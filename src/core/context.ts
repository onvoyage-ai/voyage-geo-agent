import { randomBytes } from 'node:crypto';
import type { VoyageGeoConfig } from '../config/schema.js';
import type { BrandProfile } from '../types/brand.js';
import type { QuerySet } from '../types/query.js';
import type { ExecutionRun } from '../types/result.js';
import type { AnalysisResult } from '../types/analysis.js';

export interface RunContext {
  runId: string;
  config: VoyageGeoConfig;
  startedAt: string;
  completedAt?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  currentStage?: string;
  brandProfile?: BrandProfile;
  querySet?: QuerySet;
  executionRun?: ExecutionRun;
  analysisResult?: AnalysisResult;
  errors: Array<{ stage: string; error: string; timestamp: string }>;
}

export function createRunContext(config: VoyageGeoConfig): RunContext {
  const now = new Date();
  const dateStr = now.toISOString().replace(/[-:T]/g, '').slice(0, 14);
  const suffix = randomBytes(3).toString('hex');
  const runId = `run-${dateStr}-${suffix}`;

  return {
    runId,
    config,
    startedAt: now.toISOString(),
    status: 'pending',
    errors: [],
  };
}

export function updateContext(ctx: RunContext, updates: Partial<RunContext>): RunContext {
  return { ...ctx, ...updates };
}
