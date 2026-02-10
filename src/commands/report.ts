import type { Command } from 'commander';
import { loadConfig } from '../config/loader.js';
import { createRunContext } from '../core/context.js';
import type { BrandProfile } from '../types/brand.js';
import type { AnalysisResult } from '../types/analysis.js';
import { FileSystemStorage } from '../storage/filesystem.js';
import { ReportingStage } from '../stages/reporting/stage.js';
import { setLogLevel } from '../utils/logger.js';
import { successMessage, errorMessage } from '../utils/progress.js';

export function registerReportCommand(program: Command): void {
  program
    .command('report')
    .description('Generate reports from analysis results')
    .requiredOption('--run-id <id>', 'Run ID')
    .option('--format <list>', 'Report formats (html,json,csv,markdown)', 'html,json')
    .option('-c, --config <path>', 'Config file path')
    .option('-o, --output <dir>', 'Output directory')
    .option('--log-level <level>', 'Log level', 'info')
    .action(async (opts) => {
      try {
        setLogLevel(opts.logLevel);

        const config = loadConfig({
          configFile: opts.config,
          cliOverrides: {
            report: {
              formats: opts.format.split(',').map((f: string) => f.trim()) as ('html' | 'json' | 'csv' | 'markdown')[],
              includeCharts: true,
              includeRawData: false,
            },
          },
        });

        const storage = new FileSystemStorage(opts.output || config.outputDir);
        const brandProfile = await storage.loadJSON<BrandProfile>(opts.runId, 'brand-profile.json');
        const analysisResult = await storage.loadJSON<AnalysisResult>(opts.runId, 'analysis/analysis.json');

        const ctx = {
          ...createRunContext(config),
          runId: opts.runId,
          brandProfile,
          analysisResult,
        };

        const stage = new ReportingStage(storage);
        await stage.execute(ctx);

        successMessage(`Reports generated at: ${storage.getRunPath(opts.runId)}/reports/`);
      } catch (err) {
        errorMessage(`Report generation failed: ${err instanceof Error ? err.message : String(err)}`);
        process.exit(1);
      }
    });
}
