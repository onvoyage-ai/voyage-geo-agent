import type { Command } from 'commander';
import { loadConfig } from '../config/loader.js';
import { createRunContext } from '../core/context.js';
import type { BrandProfile } from '../types/brand.js';
import { FileSystemStorage } from '../storage/filesystem.js';
import { ProviderRegistry } from '../providers/registry.js';
import { QueryGenerationStage } from '../stages/query-generation/stage.js';
import { setLogLevel } from '../utils/logger.js';
import { successMessage, errorMessage } from '../utils/progress.js';

export function registerQueryCommand(program: Command): void {
  program
    .command('query')
    .description('Generate queries for an existing run')
    .requiredOption('--run-id <id>', 'Run ID to generate queries for')
    .option('-c, --config <path>', 'Config file path')
    .option('-o, --output <dir>', 'Output directory')
    .option('--log-level <level>', 'Log level', 'info')
    .action(async (opts) => {
      try {
        setLogLevel(opts.logLevel);

        const config = loadConfig({ configFile: opts.config });
        const storage = new FileSystemStorage(opts.output || config.outputDir);

        const brandProfile = await storage.loadJSON<BrandProfile>(opts.runId, 'brand-profile.json');
        const registry = new ProviderRegistry();

        const ctx = {
          ...createRunContext(config),
          runId: opts.runId,
          brandProfile,
        };

        const stage = new QueryGenerationStage(registry, storage);
        const result = await stage.execute(ctx);

        successMessage(`Queries generated: ${result.querySet?.totalCount}`);
      } catch (err) {
        errorMessage(`Query generation failed: ${err instanceof Error ? err.message : String(err)}`);
        process.exit(1);
      }
    });
}
