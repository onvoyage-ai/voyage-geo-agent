import chalk from 'chalk';
import type { PipelineStage } from '../types.js';
import type { RunContext } from '../../core/context.js';
import type { GeneratedQuery, QuerySet } from '../../types/query.js';
import type { ProviderRegistry } from '../../providers/registry.js';
import type { FileSystemStorage } from '../../storage/filesystem.js';
import type { QueryStrategyInterface } from './strategies/types.js';
import { KeywordStrategy } from './strategies/keyword.js';
import { PersonaStrategy } from './strategies/persona.js';
import { CompetitorStrategy } from './strategies/competitor.js';
import { IntentStrategy } from './strategies/intent.js';
import { createLogger } from '../../utils/logger.js';
import { stageHeader, createSpinner } from '../../utils/progress.js';

const logger = createLogger('query-generation');

const STRATEGY_MAP: Record<string, () => QueryStrategyInterface> = {
  keyword: () => new KeywordStrategy(),
  persona: () => new PersonaStrategy(),
  competitor: () => new CompetitorStrategy(),
  intent: () => new IntentStrategy(),
};

export class QueryGenerationStage implements PipelineStage {
  name = 'query-generation';
  description = 'Generate search queries for brand analysis';

  constructor(
    private providerRegistry: ProviderRegistry,
    private storage: FileSystemStorage,
  ) {}

  async execute(ctx: RunContext): Promise<RunContext> {
    stageHeader(this.name, this.description);

    if (!ctx.brandProfile) {
      throw new Error('Brand profile is required for query generation');
    }

    const spinner = createSpinner('Generating queries with AI...');
    spinner.start();

    const profile = ctx.brandProfile;
    const queryConfig = ctx.config.queries;
    const strategiesEnabled = queryConfig.strategies;
    const totalCount = queryConfig.count;
    const perStrategy = Math.ceil(totalCount / strategiesEnabled.length);

    // Pick a provider to use for query generation (prefer fastest: openai > anthropic > google > perplexity)
    const generatorProvider = this.pickGeneratorProvider();

    const allQueries: GeneratedQuery[] = [];

    for (const strategyName of strategiesEnabled) {
      const factory = STRATEGY_MAP[strategyName];
      if (!factory) {
        logger.warn({ strategy: strategyName }, 'Unknown strategy, skipping');
        continue;
      }

      spinner.text = `AI generating ${strategyName} queries via ${generatorProvider.displayName}...`;
      const strategy = factory();
      const queries = await strategy.generate(profile, perStrategy, generatorProvider);
      allQueries.push(...queries);
    }

    // Trim to exact count
    const trimmed = allQueries.slice(0, totalCount);

    const querySet: QuerySet = {
      brand: profile.name,
      queries: trimmed,
      generatedAt: new Date().toISOString(),
      totalCount: trimmed.length,
    };

    await this.storage.saveJSON(ctx.runId, 'queries.json', querySet);
    spinner.succeed(`Generated ${trimmed.length} AI-crafted queries across ${strategiesEnabled.length} strategies`);

    // Print query table
    this.printQueryTable(trimmed);

    logger.info({ count: trimmed.length, strategies: strategiesEnabled }, 'Query generation complete');

    return { ...ctx, querySet };
  }

  private pickGeneratorProvider() {
    const enabled = this.providerRegistry.getEnabled();
    if (enabled.length === 0) {
      throw new Error('No configured providers available for query generation');
    }

    // Prefer order: openai (fastest/cheapest), anthropic, google, perplexity
    const preferred = ['openai', 'anthropic', 'google', 'perplexity'];
    for (const name of preferred) {
      const match = enabled.find((p) => p.name === name);
      if (match) return match;
    }

    return enabled[0];
  }

  private printQueryTable(queries: GeneratedQuery[]): void {
    const w = process.stdout.write.bind(process.stdout);

    w('\n');
    // Header
    const hdr = (s: string, len: number) => chalk.bold.gray(s.padEnd(len));
    w(`  ${hdr('#', 4)}${hdr('Strategy', 12)}${hdr('Category', 16)}${hdr('Query', 80)}\n`);
    w(`  ${chalk.gray('─'.repeat(110))}\n`);

    // Rows
    for (let i = 0; i < queries.length; i++) {
      const q = queries[i];
      const num = chalk.gray(String(i + 1).padEnd(4));
      const strategy = this.strategyColor(q.strategy).padEnd(12);
      const category = chalk.dim(q.category.padEnd(16));
      const text = q.text.length > 78 ? q.text.slice(0, 75) + '...' : q.text;
      w(`  ${num}${strategy}${category}${text}\n`);
    }

    w('\n');
  }

  private strategyColor(strategy: string): string {
    switch (strategy) {
      case 'keyword': return chalk.cyan(strategy);
      case 'persona': return chalk.magenta(strategy);
      case 'competitor': return chalk.yellow(strategy);
      case 'intent': return chalk.green(strategy);
      default: return chalk.white(strategy);
    }
  }
}
