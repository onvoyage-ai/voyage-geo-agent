import type { PipelineStage } from '../types.js';
import type { RunContext } from '../../core/context.js';
import type { ExecutionRun } from '../../types/result.js';
import type { ProviderRegistry } from '../../providers/registry.js';
import type { FileSystemStorage } from '../../storage/filesystem.js';
import { QueryRunner, type ExecutionTask } from './runner.js';
import { ResultStore } from '../../storage/result-store.js';
import { createLogger } from '../../utils/logger.js';
import { stageHeader, createSpinner } from '../../utils/progress.js';

const logger = createLogger('execution');

export class ExecutionStage implements PipelineStage {
  name = 'execution';
  description = 'Run queries against AI providers';

  constructor(
    private providerRegistry: ProviderRegistry,
    private storage: FileSystemStorage,
  ) {}

  async execute(ctx: RunContext): Promise<RunContext> {
    stageHeader(this.name, this.description);

    if (!ctx.querySet) {
      throw new Error('Query set is required for execution stage');
    }

    const providers = this.providerRegistry.getEnabled();
    if (providers.length === 0) {
      throw new Error('No providers configured. Set API keys in .env');
    }

    const queries = ctx.querySet.queries;
    const iterations = ctx.config.execution.iterations;
    const totalTasks = queries.length * providers.length * iterations;

    const spinner = createSpinner(`Executing ${totalTasks} queries across ${providers.length} providers...`);
    spinner.start();

    const runner = new QueryRunner(ctx.config.execution);

    // Set up rate limits
    for (const [name, config] of Object.entries(ctx.config.providers)) {
      if (config.rateLimit) {
        runner.setRateLimit(name, config.rateLimit.requestsPerMinute);
      }
    }

    // Build task list
    const tasks: ExecutionTask[] = [];
    for (let iter = 0; iter < iterations; iter++) {
      for (const query of queries) {
        for (const provider of providers) {
          tasks.push({ query, provider, iteration: iter + 1 });
        }
      }
    }

    const resultStore = new ResultStore(this.storage, ctx.runId);
    let completed = 0;

    const results = await runner.runAll(tasks, (result) => {
      completed++;
      const pct = Math.round((completed / totalTasks) * 100);
      spinner.text = `Progress: ${completed}/${totalTasks} (${pct}%) — ${result.provider}`;
    });

    await resultStore.appendBatch(results);
    await resultStore.exportCSV();

    const failed = results.filter((r) => r.error).length;
    spinner.succeed(`Executed ${results.length} queries (${failed} failed)`);

    const executionRun: ExecutionRun = {
      runId: ctx.runId,
      brand: ctx.config.brand || '',
      providers: providers.map((p) => p.name),
      totalQueries: totalTasks,
      completedQueries: results.length - failed,
      failedQueries: failed,
      results,
      startedAt: ctx.startedAt,
      completedAt: new Date().toISOString(),
      status: failed === totalTasks ? 'failed' : failed > 0 ? 'partial' : 'completed',
    };

    logger.info(
      { total: totalTasks, completed: results.length, failed },
      'Execution complete',
    );

    return { ...ctx, executionRun };
  }
}
