import type { Command } from 'commander';
import { loadConfig } from '../config/loader.js';
import { createRunContext } from '../core/context.js';
import type { BrandProfile } from '../types/brand.js';
import type { QuerySet } from '../types/query.js';
import { FileSystemStorage } from '../storage/filesystem.js';
import { ProviderRegistry } from '../providers/registry.js';
import { ExecutionStage } from '../stages/execution/stage.js';
import { setLogLevel } from '../utils/logger.js';
import { successMessage, errorMessage } from '../utils/progress.js';

export function registerExecuteCommand(program: Command): void {
  program
    .command('execute')
    .description('Execute queries against AI providers')
    .requiredOption('--run-id <id>', 'Run ID')
    .option('-p, --providers <list>', 'Comma-separated provider list')
    .option('-c, --config <path>', 'Config file path')
    .option('-o, --output <dir>', 'Output directory')
    .option('--log-level <level>', 'Log level', 'info')
    .action(async (opts) => {
      try {
        setLogLevel(opts.logLevel);

        const config = loadConfig({ configFile: opts.config });
        const storage = new FileSystemStorage(opts.output || config.outputDir);

        const brandProfile = await storage.loadJSON<BrandProfile>(opts.runId, 'brand-profile.json');
        const querySet = await storage.loadJSON<QuerySet>(opts.runId, 'queries.json');

        const registry = new ProviderRegistry();
        const enabledProviders = opts.providers
          ? opts.providers.split(',').map((p: string) => p.trim())
          : null;

        for (const [name, providerConfig] of Object.entries(config.providers)) {
          if (providerConfig.enabled && providerConfig.apiKey) {
            if (!enabledProviders || enabledProviders.includes(name)) {
              registry.register(name, providerConfig);
            }
          }
        }

        const ctx = {
          ...createRunContext(config),
          runId: opts.runId,
          brandProfile,
          querySet,
        };

        const stage = new ExecutionStage(registry, storage);
        const result = await stage.execute(ctx);

        successMessage(`Execution complete: ${result.executionRun?.completedQueries} queries`);
      } catch (err) {
        errorMessage(`Execution failed: ${err instanceof Error ? err.message : String(err)}`);
        process.exit(1);
      }
    });
}
