import type { RunContext } from '../core/context.js';

export interface PipelineStage {
  name: string;
  description: string;
  execute(ctx: RunContext): Promise<RunContext>;
}
