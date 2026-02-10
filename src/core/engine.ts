import type { VoyageGeoConfig } from '../config/schema.js';
import { Pipeline } from './pipeline.js';
import { createRunContext, type RunContext } from './context.js';
import { ResearchStage } from '../stages/research/stage.js';
import { QueryGenerationStage } from '../stages/query-generation/stage.js';
import { ExecutionStage } from '../stages/execution/stage.js';
import { AnalysisStage } from '../stages/analysis/stage.js';
import { ReportingStage } from '../stages/reporting/stage.js';
import { FileSystemStorage } from '../storage/filesystem.js';
import { ProviderRegistry } from '../providers/registry.js';
import { createLogger } from '../utils/logger.js';

export class VoyageGeoEngine {
  private config: VoyageGeoConfig;
  private pipeline: Pipeline;
  private storage: FileSystemStorage;
  private providerRegistry: ProviderRegistry;
  private logger = createLogger('engine');

  constructor(config: VoyageGeoConfig) {
    this.config = config;
    this.pipeline = new Pipeline();
    this.storage = new FileSystemStorage(config.outputDir);
    this.providerRegistry = new ProviderRegistry();

    this.registerProviders();
    this.buildPipeline();
  }

  private registerProviders(): void {
    for (const [name, providerConfig] of Object.entries(this.config.providers)) {
      if (providerConfig.enabled && providerConfig.apiKey) {
        this.providerRegistry.register(name, providerConfig);
      }
    }
  }

  private buildPipeline(): void {
    this.pipeline
      .addStage(new ResearchStage(this.providerRegistry, this.storage))
      .addStage(new QueryGenerationStage(this.providerRegistry, this.storage))
      .addStage(new ExecutionStage(this.providerRegistry, this.storage))
      .addStage(new AnalysisStage(this.storage))
      .addStage(new ReportingStage(this.storage));
  }

  async run(): Promise<RunContext> {
    const ctx = createRunContext(this.config);
    this.logger.info({ runId: ctx.runId, brand: this.config.brand }, 'Starting GEO analysis');

    await this.storage.createRunDir(ctx.runId);
    await this.storage.saveMetadata(ctx.runId, {
      runId: ctx.runId,
      config: this.config,
      startedAt: ctx.startedAt,
      status: 'running',
    });

    try {
      const result = await this.pipeline.run(ctx);

      await this.storage.saveMetadata(ctx.runId, {
        runId: ctx.runId,
        config: this.config,
        startedAt: ctx.startedAt,
        completedAt: result.completedAt,
        status: 'completed',
      });

      this.logger.info({ runId: ctx.runId }, 'GEO analysis completed');
      return result;
    } catch (error) {
      await this.storage.saveMetadata(ctx.runId, {
        runId: ctx.runId,
        config: this.config,
        startedAt: ctx.startedAt,
        completedAt: new Date().toISOString(),
        status: 'failed',
        errors: ctx.errors,
      });
      throw error;
    }
  }

  getProviderRegistry(): ProviderRegistry {
    return this.providerRegistry;
  }

  getPipeline(): Pipeline {
    return this.pipeline;
  }

  getStorage(): FileSystemStorage {
    return this.storage;
  }
}
