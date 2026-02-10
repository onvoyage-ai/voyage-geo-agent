import { EventEmitter } from 'node:events';
import type { RunContext } from './context.js';
import type { PipelineStage } from '../stages/types.js';
import { GeoPipelineError } from './errors.js';
import { createLogger } from '../utils/logger.js';

export interface PipelineEvents {
  'stage:start': (stage: string) => void;
  'stage:complete': (stage: string, ctx: RunContext) => void;
  'stage:error': (stage: string, error: Error) => void;
  'pipeline:start': (ctx: RunContext) => void;
  'pipeline:complete': (ctx: RunContext) => void;
  'pipeline:error': (error: Error) => void;
}

export class Pipeline extends EventEmitter {
  private stages: PipelineStage[] = [];
  private logger = createLogger('pipeline');

  addStage(stage: PipelineStage): this {
    this.stages.push(stage);
    return this;
  }

  getStages(): PipelineStage[] {
    return [...this.stages];
  }

  async run(ctx: RunContext): Promise<RunContext> {
    this.emit('pipeline:start', ctx);
    this.logger.info({ runId: ctx.runId }, 'Pipeline started');

    let currentCtx: RunContext = { ...ctx, status: 'running' };

    for (const stage of this.stages) {
      try {
        this.emit('stage:start', stage.name);
        this.logger.info({ stage: stage.name }, `Stage started: ${stage.name}`);

        currentCtx = { ...currentCtx, currentStage: stage.name };
        currentCtx = await stage.execute(currentCtx);

        this.emit('stage:complete', stage.name, currentCtx);
        this.logger.info({ stage: stage.name }, `Stage completed: ${stage.name}`);
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        const pipelineError = new GeoPipelineError(
          `Stage "${stage.name}" failed: ${error.message}`,
          stage.name,
        );

        currentCtx.errors.push({
          stage: stage.name,
          error: error.message,
          timestamp: new Date().toISOString(),
        });

        this.emit('stage:error', stage.name, pipelineError);
        this.logger.error({ stage: stage.name, error: error.message }, `Stage failed: ${stage.name}`);

        currentCtx = { ...currentCtx, status: 'failed' };
        this.emit('pipeline:error', pipelineError);
        throw pipelineError;
      }
    }

    currentCtx = {
      ...currentCtx,
      status: 'completed',
      completedAt: new Date().toISOString(),
      currentStage: undefined,
    };

    this.emit('pipeline:complete', currentCtx);
    this.logger.info({ runId: currentCtx.runId }, 'Pipeline completed');

    return currentCtx;
  }
}
