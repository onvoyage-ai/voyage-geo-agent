import type { PipelineStage } from '../types.js';
import type { RunContext } from '../../core/context.js';
import type { FileSystemStorage } from '../../storage/filesystem.js';
import type { ReportRenderer } from './renderers/types.js';
import { HtmlRenderer } from './renderers/html.js';
import { JsonRenderer } from './renderers/json.js';
import { CsvRenderer } from './renderers/csv.js';
import { MarkdownRenderer } from './renderers/markdown.js';
import { generateCharts } from './charts/generator.js';
import { createLogger } from '../../utils/logger.js';
import { stageHeader, createSpinner } from '../../utils/progress.js';

const logger = createLogger('reporting');

const RENDERER_MAP: Record<string, () => ReportRenderer> = {
  html: () => new HtmlRenderer(),
  json: () => new JsonRenderer(),
  csv: () => new CsvRenderer(),
  markdown: () => new MarkdownRenderer(),
};

export class ReportingStage implements PipelineStage {
  name = 'reporting';
  description = 'Generate reports and visualizations';

  constructor(private storage: FileSystemStorage) {}

  async execute(ctx: RunContext): Promise<RunContext> {
    stageHeader(this.name, this.description);

    if (!ctx.analysisResult || !ctx.brandProfile) {
      throw new Error('Analysis results and brand profile are required for reporting');
    }

    const spinner = createSpinner('Generating reports...');
    spinner.start();

    const formats = ctx.config.report.formats;
    const reportData = {
      runId: ctx.runId,
      brand: ctx.brandProfile,
      analysis: ctx.analysisResult,
      generatedAt: new Date().toISOString(),
    };

    // Generate charts
    if (ctx.config.report.includeCharts) {
      spinner.text = 'Generating charts...';
      try {
        const charts = await generateCharts(
          this.storage.getRunPath(ctx.runId),
          ctx.analysisResult,
        );
        logger.info({ charts }, 'Charts generated');
      } catch (err) {
        logger.warn({ error: err instanceof Error ? err.message : String(err) }, 'Chart generation failed, continuing');
      }
    }

    // Generate reports in each format
    for (const format of formats) {
      const factory = RENDERER_MAP[format];
      if (!factory) {
        logger.warn({ format }, 'Unknown report format, skipping');
        continue;
      }

      spinner.text = `Generating ${format} report...`;
      const renderer = factory();
      await renderer.render(reportData, this.storage);
      logger.info({ format }, 'Report generated');
    }

    spinner.succeed(`Reports generated: ${formats.join(', ')}`);

    return ctx;
  }
}
