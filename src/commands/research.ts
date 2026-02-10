import type { Command } from 'commander';
import { loadConfig } from '../config/loader.js';
import { createRunContext } from '../core/context.js';
import { FileSystemStorage } from '../storage/filesystem.js';
import { ProviderRegistry } from '../providers/registry.js';
import { ResearchStage } from '../stages/research/stage.js';
import { setLogLevel } from '../utils/logger.js';
import { successMessage, errorMessage } from '../utils/progress.js';

export function registerResearchCommand(program: Command): void {
  program
    .command('research <brand>')
    .description('Run brand research stage only')
    .option('-w, --website <url>', 'Brand website URL')
    .option('-c, --config <path>', 'Config file path')
    .option('-o, --output <dir>', 'Output directory')
    .option('--log-level <level>', 'Log level', 'info')
    .action(async (brand, opts) => {
      try {
        setLogLevel(opts.logLevel);

        const config = loadConfig({
          configFile: opts.config,
          cliOverrides: {
            brand,
            website: opts.website,
            ...(opts.output ? { outputDir: opts.output } : {}),
          },
        });

        const storage = new FileSystemStorage(config.outputDir);
        const registry = new ProviderRegistry();

        for (const [name, providerConfig] of Object.entries(config.providers)) {
          if (providerConfig.enabled && providerConfig.apiKey) {
            registry.register(name, providerConfig);
          }
        }

        const ctx = createRunContext(config);
        await storage.createRunDir(ctx.runId);

        const stage = new ResearchStage(registry, storage);
        const result = await stage.execute(ctx);

        successMessage(`Research complete! Run ID: ${ctx.runId}`);
        if (result.brandProfile) {
          successMessage(`Industry: ${result.brandProfile.industry}`);
          successMessage(`Competitors: ${result.brandProfile.competitors.join(', ')}`);
        }
      } catch (err) {
        errorMessage(`Research failed: ${err instanceof Error ? err.message : String(err)}`);
        process.exit(1);
      }
    });
}
