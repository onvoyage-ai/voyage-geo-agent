import type { Command } from 'commander';
import { loadConfig } from '../config/loader.js';
import { VoyageGeoEngine } from '../core/engine.js';
import { setLogLevel } from '../utils/logger.js';
import { successMessage, errorMessage } from '../utils/progress.js';

export function registerRunCommand(program: Command): void {
  program
    .command('run')
    .description('Run the full GEO analysis pipeline')
    .requiredOption('-b, --brand <name>', 'Brand name to analyze')
    .option('-w, --website <url>', 'Brand website URL')
    .option('-p, --providers <list>', 'Comma-separated provider list', 'openai,anthropic,google,perplexity')
    .option('-i, --iterations <n>', 'Number of iterations per query', '1')
    .option('-q, --queries <n>', 'Number of queries to generate', '20')
    .option('-c, --config <path>', 'Config file path')
    .option('-o, --output <dir>', 'Output directory')
    .option('--competitors <list>', 'Comma-separated competitor list')
    .option('--format <list>', 'Report formats (html,json,csv,markdown)', 'html,json')
    .option('--log-level <level>', 'Log level', 'info')
    .action(async (opts) => {
      try {
        setLogLevel(opts.logLevel);

        const enabledProviders = opts.providers.split(',').map((p: string) => p.trim());
        const config = loadConfig({
          configFile: opts.config,
          cliOverrides: {
            brand: opts.brand,
            website: opts.website,
            competitors: opts.competitors ? opts.competitors.split(',').map((c: string) => c.trim()) : [],
            execution: {
              concurrency: 3,
              retries: 3,
              retryDelayMs: 1000,
              timeoutMs: 30000,
              iterations: parseInt(opts.iterations, 10),
            },
            queries: {
              count: parseInt(opts.queries, 10),
              strategies: ['keyword', 'persona', 'competitor', 'intent'],
              categories: ['recommendation', 'comparison', 'best-of', 'how-to', 'review', 'alternative', 'general'],
            },
            report: {
              formats: opts.format.split(',').map((f: string) => f.trim()) as ('html' | 'json' | 'csv' | 'markdown')[],
              includeCharts: true,
              includeRawData: false,
            },
            ...(opts.output ? { outputDir: opts.output } : {}),
          },
        });

        // Disable providers not in the list
        for (const [name, providerConfig] of Object.entries(config.providers)) {
          if (!enabledProviders.includes(name)) {
            providerConfig.enabled = false;
          }
        }

        const engine = new VoyageGeoEngine(config);
        const ctx = await engine.run();

        process.stdout.write('\n');
        successMessage(`Analysis complete! Run ID: ${ctx.runId}`);
        successMessage(`Results: ${engine.getStorage().getRunPath(ctx.runId)}`);
      } catch (err) {
        errorMessage(`Pipeline failed: ${err instanceof Error ? err.message : String(err)}`);
        process.exit(1);
      }
    });
}
