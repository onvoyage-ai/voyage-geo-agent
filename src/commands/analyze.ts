import type { Command } from 'commander';
import { loadConfig } from '../config/loader.js';
import { createRunContext } from '../core/context.js';
import type { BrandProfile } from '../types/brand.js';
import type { QueryResult } from '../types/result.js';
import { FileSystemStorage } from '../storage/filesystem.js';
import { AnalysisStage } from '../stages/analysis/stage.js';
import { setLogLevel } from '../utils/logger.js';
import { successMessage, errorMessage } from '../utils/progress.js';

export function registerAnalyzeCommand(program: Command): void {
  program
    .command('analyze')
    .description('Analyze execution results')
    .requiredOption('--run-id <id>', 'Run ID')
    .option('-c, --config <path>', 'Config file path')
    .option('-o, --output <dir>', 'Output directory')
    .option('--log-level <level>', 'Log level', 'info')
    .action(async (opts) => {
      try {
        setLogLevel(opts.logLevel);

        const config = loadConfig({ configFile: opts.config });
        const storage = new FileSystemStorage(opts.output || config.outputDir);

        const brandProfile = await storage.loadJSON<BrandProfile>(opts.runId, 'brand-profile.json');
        const results = await storage.loadJSON<QueryResult[]>(opts.runId, 'results/results.json');

        const ctx = {
          ...createRunContext(config),
          runId: opts.runId,
          brandProfile,
          executionRun: {
            runId: opts.runId,
            brand: brandProfile.name,
            providers: [...new Set(results.map((r) => r.provider))],
            totalQueries: results.length,
            completedQueries: results.filter((r) => !r.error).length,
            failedQueries: results.filter((r) => r.error).length,
            results,
            startedAt: new Date().toISOString(),
            status: 'completed' as const,
          },
        };

        const stage = new AnalysisStage(storage);
        const result = await stage.execute(ctx);

        successMessage(`Analysis complete: ${result.analysisResult?.summary.headline}`);
      } catch (err) {
        errorMessage(`Analysis failed: ${err instanceof Error ? err.message : String(err)}`);
        process.exit(1);
      }
    });
}
